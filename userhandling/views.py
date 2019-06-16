from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.mail import EmailMessage
import urllib, json
import hashlib
import random
from .utils import Mailchimp, VerificationHash
from .forms import RegistrationForm, LoginForm, PasswordResetRequestForm, PasswordResetForm, MoveNightForm, MovieAddForm

from .models import Movie, MovieNightEvent, Profile, PasswordReset
import tmdbsimple as tmdb
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
import requests
from django.core import serializers
from rest_framework import viewsets
from .serializers import MovieNightEventSerializer

# ....

# Render Index Page, manage register
def index(request):

    if request.user.is_authenticated:
        return redirect("curr_mov_nights")
    successful_verified = False
    context = {
        'successful_verified'   : successful_verified,
        'email'                 : "",
        'username'              : ""
    }
    return render(request, 'userhandling/index.html', context)

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
            # TODO THis will fail
            new_activation_link(request, id_user)

        else: #Activation successful
            # Activate user.
            profile.user.is_active = True
            profile.user.save()

            # Subscribe to Mailchimp list.
            mc = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID)
            mc.add_email(profile.user.email)

            # Todo: Add more fields to Mailchimp.

            movienights = MovieNightEvent.objects.order_by('-date')[:5]
            successful_verified = True
            context = {
            'movienights'           : movienights,
            'successful_verified'   : successful_verified,
            'email'                 : profile.user.email,
            'username'              : profile.user.username
            }
            return render(request, 'userhandling/index.html', context)

    #If user is already active, simply display error message
    else:
        already_active = True #Display : error message
        return HttpResponse("User already registered.")


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
        return HttpResponse("Activation link expired. You have resent an activation link for {}.".format(user.email))

    return redirect('index')

def registration(request):
    registration_form = RegistrationForm()

    # Has a registration succesfully been submitted?
    successful_reg_submit = False
    subscribe_email = ''

    if request.method == 'POST':
        registration_form = RegistrationForm(request.POST)
        if registration_form.is_valid():
            datas={}
            datas['username']=registration_form.cleaned_data['username']
            datas['email']=registration_form.cleaned_data['email']
            datas['password1']=registration_form.cleaned_data['password1']
            datas['first_name']=registration_form.cleaned_data['first_name']
            datas['last_name']=registration_form.cleaned_data['last_name']

            # TODO: Check if user alredy exists

            #We generate a random activation key
            vh = VerificationHash()
            datas['activation_key']= vh.gen_ver_hash(datas['username'])

            registration_form.send_activation_email(datas)
            registration_form.save(datas) #Save the user and his profile

            successful_reg_submit = True
            subscribe_email = datas['email']

    context = {
        'form': registration_form,
        'successful_submit' : successful_reg_submit,
        'subscribe_email' :  str(subscribe_email),
    }
    return render(request, 'userhandling/registration.html', context)

def my_login(request):
    login_form = LoginForm()


    if request.method == 'POST':
        form = LoginForm(request.POST)
        next_url = request.POST.get('next')
        if form.is_valid():
            # At this point, the clean() fuction in the form already made sure that the user is valid and active.
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if next_url != 'None':
                    return HttpResponseRedirect(next_url)
                else:
                    return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
            else:
                return HttpResponse("User is none despite clean in form.")
        else:
            login_form = form #Display form with error messages (incorrect fields, etc)
    else:
        next_url = request.GET.get('next')



    context = {
        'login_form': login_form,
        'next'  : next_url,
    }
    return render(request, 'userhandling/login.html', context)

def password_reset_request(request):
    form = PasswordResetRequestForm()
    successful_submit = False
    reset_email = ""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            reset_email = form.populate_PasswordReset_send_email()
            successful_submit = True

    context = {
        'form': form,
        'successful_submit' : successful_submit,
        'reset_email' : reset_email
    }
    return render(request, 'userhandling/password_reset_request.html', context)

def password_reset_request_done(request):
    form = PasswordResetRequestForm(request.POST)
    context = {
        'form': form,
        'successful_submit' : True,
    }
    return render(request, 'userhandling/password_reset_request.html', context)

def check_pw_rest_link(request, reset_key):
    # validate reset link
    try:
        PasswordResetObject = PasswordReset.objects.get(reset_key=reset_key)
        error = 0
    except PasswordReset.DoesNotExist:
        error = -1
        return error

    if timezone.now() > PasswordResetObject.created_at + datetime.timedelta(days=2):
        error = -2
    if PasswordResetObject.reset_used:
        error = -3

    return error

def password_reset(request, reset_key):

    form = PasswordResetForm()
    successful_submit = False

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            # get pw from form
            pw = form.cleaned_data['password1']

            # Retrieve user object and reset password.
            PasswordResetObject = PasswordReset.objects.get(reset_key=reset_key)
            username = PasswordResetObject.username
            user = User.objects.get(username=username)
            user.set_password(pw)
            user.save()

            # Prevent this activation key from beeing reused.
            PasswordResetObject.reset_used = True
            PasswordResetObject.save()

            # send confrmation email
            sender_email    = "admin@cinemaple.com"
            sender_name     = "Cinemaple"
            subject         = "Password successfully changed"
            recipients      = [user.email]
            content         = "Hi " + user.first_name + ", you have successfully changed your password and can now login using the new password: http://www.cinemaple.com/login"

            email_send = EmailMessage(subject, content, sender_name + " <" + sender_email + ">", recipients)
            email_send.send()
            successful_submit = True
    else:

        # Check password link for multiple error cases.
        link_check_res = check_pw_rest_link(request, reset_key)

        if link_check_res == -1:
            return HttpResponse("Password reset link could not be associated with valid username.")
        if link_check_res == -2:
         return HttpResponse("Password reset key expired, please restart password reset.")
        if link_check_res == -3:
            return HttpResponse("Password reset link has already been used.")

    context = {
        'form': form,
        'successful_submit' : successful_submit,
        'reset_key' : reset_key
    }

    return render(request, 'userhandling/password_reset.html', context)


@login_required
def curr_mov_nights(request):

    movienight = MovieNightEvent.objects.order_by('-date')[0]
    context = {
        'movienight' : movienight,
        'navbar' : 'curr_mov_night',
    }
    return render(request, 'userhandling/curr_mov_nights.html', context)

@login_required
def search_movie(request):
    context = {
        'debug'           : settings.DEBUG,
    }
    return render(request, 'userhandling/movie_search.html', context)


@login_required
def add_movies_from_form(request, movienight,  mov_ID_add):
    ''' Given a list of movie IDs, create movies and add to DB '''

    for movie_id in mov_ID_add:
        # retrieve json via tmdb API
        data = json.loads(imdb_tmdb_api_wrapper_movie(request, tmdb_id=movie_id).content)

        # Try to get movie object of previously added, if not exists, add object.
        try:
            m = Movie.objects.get(tmdbID=data["id"])
        except Movie.DoesNotExist:
            # create and svae movie object
            m = Movie(tmdbID=data["id"])
            m.tmdbID          = data["id"]
            m.title           = data["title"]
            m.year            = data["Year"]
            m.director        = data["Director"]
            m.producer        = data["Producer"]
            m.runtime         = data["Runtime"]
            m.actors          = data["Actors"]
            m.plot            = data["Plot"]
            m.country         = data["Country"]
            m.posterpath      = data["poster_path"]
            m.trailerlink     = data["Trailerlink"]
            m.save()

        movienight.MovieList.add(m)


@login_required
def add_movie_night(request):
    if not request.user.is_staff:
        return HttpResponse("Only staff users are authorised to view this page.")

    if request.method == 'POST': # If the form has been submitted...

        form2 = MovieAddForm(request.POST, prefix="form2")
        mn = MovieNightEvent()
        form1 = MoveNightForm(request.POST, prefix="form1", instance = mn) # An unbound form
        if form1.is_valid() and form2.is_valid(): # All validation rules pass
            form1.save() # This creates the movienight

            # generate list of movie ids to be added:
            num_formfields = 10
            mov_ID_add = []

            for i in range(1, num_formfields+1):
                # Look at correct formfield
                movie_id = form2.cleaned_data['movieID{}'.format(i)]
                # If not empty, generate
                if movie_id  != "":
                    mov_ID_add.append(movie_id)

            # Create and save movies objects
            add_movies_from_form(request, mn, mov_ID_add)

            return redirect('/mov_night/{}'.format(mn.id))
        else:
            return HttpResponse("Form not valid.")
    else:
        form1 = MoveNightForm(prefix="form1") # An unbound form
        form2 = MovieAddForm(prefix="form2")
        # TODO: This Fails.
    context = {
        'debug' : settings.DEBUG,
        'form1'      : form1,
        "form2"      : form2,
    }
    return render(request, 'userhandling/admin_movie_add.html', context)


def tmdb_api_wrapper_search(request, query, year=""):
    ''' Since we don't want to expose out API key on the client side, we write a wrapper on the tmdb API'''

    args = {
        "api_key"       : settings.TMDB_API_KEY,
        "language"      : "en-US",
        "query"         : query,
        "page"          : 1,
        "include_adult" : "false",
        "region"        : "",
        "year"          : year,
    }

    url_api = "https://api.themoviedb.org/3/search/movie?{}".format(urllib.parse.urlencode(args))

    # Load Return Object Into JSON
    try:
        data = requests.get(url_api).json()
    except:
        raise Exception("Critical TMDB API error")

    return JsonResponse(data)

def get_printable_list(data, fieldname, num_retrieve, harvard_comma):
    ''' Using the full JSON, returns print-friendly string of first n occurences'''

    resultsstring = ""
    num_retrieve = min(num_retrieve, len(data))

    for i  in range(num_retrieve):
        if i == num_retrieve - 1:
            if num_retrieve == 1:
                resultsstring = data[i][fieldname]
            elif harvard_comma:
                resultsstring = resultsstring + "and " + data[i][fieldname]
            else:
                resultsstring = resultsstring + data[i][fieldname]
        else:
            resultsstring = resultsstring + data[i][fieldname]+ ", "

    return resultsstring

def get_person_by_job(data, job_desc):
    ''' Search crew list by job description'''

    resultarray = []
    for entry in data:
        if entry["job"] == job_desc:
            resultarray.append(entry)

    return resultarray


def tmdb_get_movie_images_videos(tmdb_id):

    url_api = "https://api.themoviedb.org/3/movie/" + str(tmdb_id) + "?api_key=" + str(settings.TMDB_API_KEY) + "&append_to_response=videos,credits"

    # Load Return Object Into JSON
    try:
        data = requests.get(url_api).json()
    except:
        raise Exception("{} is not valid TMDB ID".format(tmdb_id))

    # retrive some interesting data from lower level json

    # Actor list
    num_actors = 4
    cast = data["credits"]["cast"]
    data["Actors"] = get_printable_list(cast, "name", num_actors, True)

    data["Year"] = data["release_date"][:4]
    data["Plot"] = data["overview"]

    # Production Country list
    num_countries = 3
    prod_countries = data["production_countries"]
    data["Country"] = get_printable_list(prod_countries, "name", num_countries, False)

    # Retrieve runtime
    if data["runtime"] == None:
        data["Runtime"] = ""
    else:
        data["Runtime"] = str(data["runtime"]) + " min"

    # Retrieve Director and producer list
    directors = get_person_by_job( data["credits"]["crew"], "Director")
    producers = get_person_by_job( data["credits"]["crew"], "Producer")
    num_directors = 3
    num_producers = 3
    data["Director"] = get_printable_list(directors, "name", num_directors, True)
    data["Producer"] = get_printable_list(producers, "name", num_producers, True)

    # retrieve youtube link

    video_res = data["videos"]["results"]
    num_videos = len(video_res)

    trailerlink = ""

    if num_videos > 0:
        for i in range(num_videos):
            linktype = video_res[i]["type"]
            site = video_res[i]["site"]
            if site == "YouTube" and linktype == "Trailer":
                trailerlink =  "https://www.youtube.com/embed/" + video_res[i]["key"]

    data["Trailerlink"] = trailerlink

    return data

def imdb_tmdb_api_wrapper_movie(request, tmdb_id):
    ''' Once ID is know, can query more information'''

    tmdb_movie_images_links = tmdb_get_movie_images_videos(tmdb_id)

    return JsonResponse(tmdb_movie_images_links)

@login_required
def dashboard(request):
    return render(request, 'userhandling/dashboard.html')


@login_required
def man_mov_nights(request):

    if not request.user.is_staff:
        return HttpResponse("Only staff users are authorised to view this page.")


    return render(request, 'userhandling/admin_movie_night_manage.html')

@login_required
def details_mov_nights(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)
    context = {
        'movienight' : movienight,
        'navbar' : "movie_night_manage",
    }
    return render(request, 'userhandling/curr_mov_nights.html', context)


@login_required
def delete_mov_night(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)
    movienight.delete()

    return redirect("index")



class MovieNightEventViewSet(viewsets.ModelViewSet):
    queryset = MovieNightEvent.objects.all().order_by('-date')
    serializer_class = MovieNightEventSerializer





