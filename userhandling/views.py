from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.conf import settings
import urllib, json
import hashlib
import random
from .utils import Mailchimp, Mailgun, VerificationHash
from .forms import RegistrationForm

from .models import Movie, MovieNightEvent, Profile
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


#View called from activation email. Activate user if link didn't expire (48h default), or offer to
#send a second link if the first expired.
def activation(request, key):
    activation_expired = False
    already_active = False
    profile = get_object_or_404(Profile, activation_key=key)
    if profile.user.is_active == False:
        if timezone.now() > profile.key_expires:
            activation_expired = True #Display: offer the user to send a new activation link
            id_user = profile.user.id
            new_activation_link(request, id_user)

        else: #Activation successful
            # Activate user.
            profile.user.is_active = True
            profile.user.save()

            # Subscribe to Mailchimp list.
            mc = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID)
            mc.add_email(profile.user.email)

            # Todo: Add more fields to Mailchimp.
            HttpResponse("You have successfully registered {}.".format(profile.user.email))

    #If user is already active, simply display error message
    else:
        already_active = True #Display : error message
        HttpResponse("User already registered.")

    return redirect('index')

def new_activation_link(request, user_id):
    form = RegistrationForm()
    datas={}
    user = User.objects.get(id=user_id)
    if user is not None and not user.is_active:

        #We generate a random activation key
        vh = VerificationHash()
        datas['activation_key']= vh.gen_ver_hash(datas['username'])

        # Update profile with new activation key and expiry data.
        profile = Profile.objects.get(user=user)
        profile.activation_key = datas['activation_key']
        profile.key_expires = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=2), "%Y-%m-%d %H:%M:%S")
        profile.save()


        # Resend verification email.
        mg = Mailgun()
        link="http://cinemaple.com/activate/"+profile.activation_key



        sender_email    = "admin@cinemaple.com"
        sender_name     = "Cinemaple"
        subject         = "Your new activation link."
        recipients      = [user.email]
        content         = "Please activate your email using the following link: " + link

        # Send message and retrieve status and return JSON object.
        status_code, r_json = mg.send_email(sender_email, sender_name, subject, recipients, content)

        assert status_code == 200, "Send of new key failed"
        request.session['new_link']=True #Display: new link sent
        HttpResponse("Activation link expired. You have resent an activation link for {}.".format(user.email))


    return redirect('index')

