from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.conf import settings
import urllib, json
import hashlib
import random
from .utils import Mailchimp, Mailgun, VerificationHash
from .forms import RegistrationForm

from .models import Movie, MovieNightEvent
# ...


# Render Index Page
def index(request):
    movienights = MovieNightEvent.objects.order_by('-date')[:5]
    return render(request, 'userhandling/index.html', {'movienights': movienights})

# Access movie info using IMDB and add model instance containing info
def add_movie_fromIMDB(request, imdb_id):
    args = {"apikey": settings.OMDB_API_KEY, "i": imdb_id, "plot" : "full"}
    url_api = " http://www.omdbapi.com/?{}".format(urllib.parse.urlencode(args))

    # Load Return Object Into JSON
    try:
        with urllib.request.urlopen(url_api) as url:
            data = json.loads(url.read().decode())
    except:
        raise Exception("{} is not valid IMDB ID")

    # Create movie instance from returned JSON
    m = Movie(imdbID=imdb_id)
    m.title = data["Title"]
    m.year = data["Year"]
    m.director = data["Director"]
    m.runtime = data["Runtime"]
    m.plot = data["Plot"]
    m.country = data["Country"]
    m.actors = data["Actors"]
    m.save()

    return render(request, 'userhandling/index.html')

# Register Email
def register(request):
    if request.user.is_authenticated:
        return redirect('index')
    registration_form = RegistrationForm()
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            datas={}
            datas['username']=form.cleaned_data['username']
            datas['email']=form.cleaned_data['email']
            datas['password1']=form.cleaned_data['password1']

            #We generate a random activation key
            vh = VerificationHash()
            datas['activation_key']= vh.gen_ver_hash(datas['username'])

            form.send_activation_email(datas)
            form.save(datas) #Save the user and his profile

            request.session['registered']=True #For display purposes
            return redirect('index')
        else:
            registration_form = form #Display form with error messages (incorrect fields, etc)
    return render(request, 'userhandling/registration.html', {'form': registration_form})

