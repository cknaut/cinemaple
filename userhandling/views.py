from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.mail import EmailMessage
import urllib
import json
import hashlib
import random
from .utils import Mailchimp, VerificationHash
from .forms import RegistrationForm, LoginForm, PasswordResetRequestForm, \
    PasswordResetForm, MoveNightForm, MovieAddForm, SneakymovienightIDForm, VotePreferenceForm, ToppingForm, AlreadyBroughtToppingForm, ToppingAddForm, MyPasswordChangeForm, ProfileUpdateForm
from .models import Movie, MovieNightEvent, Profile, PasswordReset, VotePreference, Topping, MovienightTopping, UserAttendence
import tmdbsimple as tmdb
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
import requests
from django.core import serializers
from rest_framework import viewsets
from .serializers import MovieNightEventSerializer, UserAttendenceSerializer
from django.contrib.auth.decorators import user_passes_test
from django.forms import formset_factory
import numpy as np
from rest_framework import generics

# ....


# Render Index Page, manage register
def index(request):

    if request.user.is_authenticated:
        return redirect("curr_mov_nights")
    successful_verified = False
    context = {
        'successful_verified': successful_verified,
        'email': "",
        'username': ""
    }
    return render(request, 'userhandling/index.html', context)

# View called from activation email. Activate user if link didn't expire (48h default), or offer to
# send a second link if the first expired.


def activation(request, key):
    activation_expired = False
    already_active = False
    profile = get_object_or_404(Profile, activation_key=key)
    if profile.user.is_active == False:
        if timezone.now() > profile.key_expires:
            activation_expired = True  # Display: offer the user to send a new activation link
            id_user = profile.user.id
            # TODO THis will fail
            new_activation_link(request, id_user)

        else:  # Activation successful
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
                'movienights': movienights,
                'successful_verified': successful_verified,
                'email': profile.user.email,
                'username': profile.user.username
            }
            return render(request, 'userhandling/index.html', context)

    # If user is already active, simply display error message
    else:
        already_active = True  # Display : error message
        return HttpResponse("User already registered.")


def new_activation_link(request, user_id):
    form = RegistrationForm()
    datas = {}
    user = User.objects.get(id=user_id)
    if user is not None and not user.is_active:

        # We generate a random activation key
        vh = VerificationHash()
        datas['activation_key'] = vh.gen_ver_hash(datas['username'])

        # Update profile with new activation key and expiry data.
        profile = Profile.objects.get(user=user)
        profile.activation_key = datas['activation_key']
        profile.key_expires = datetime.datetime.strftime(
            datetime.datetime.now() + datetime.timedelta(days=2), "%Y-%m-%d %H:%M:%S")
        profile.save()

        # Resend verification email.
        mg = Mailgun()
        link = "http://cinemaple.com/activate/"+profile.activation_key

        sender_email = "admin@cinemaple.com"
        sender_name = "Cinemaple"
        subject = "Your new activation link."
        recipients = [user.email]
        content = "Please activate your email using the following link: " + link

        # Send message and retrieve status and return JSON object.
        status_code, r_json = mg.send_email(
            sender_email, sender_name, subject, recipients, content)

        assert status_code == 200, "Send of new key failed"
        request.session['new_link'] = True  # Display: new link sent
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
            datas = {}
            datas['username'] = registration_form.cleaned_data['username']
            datas['email'] = registration_form.cleaned_data['email']
            datas['password1'] = registration_form.cleaned_data['password1']
            datas['first_name'] = registration_form.cleaned_data['first_name']
            datas['last_name'] = registration_form.cleaned_data['last_name']

            # TODO: Check if user alredy exists

            # We generate a random activation key
            vh = VerificationHash()
            datas['activation_key'] = vh.gen_ver_hash(datas['username'])

            registration_form.send_activation_email(datas)
            registration_form.save(datas)  # Save the user and his profile

            successful_reg_submit = True
            subscribe_email = datas['email']

    context = {
        'form': registration_form,
        'successful_submit': successful_reg_submit,
        'subscribe_email':  str(subscribe_email),
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
            # Display form with error messages (incorrect fields, etc)
            login_form = form
    else:
        next_url = request.GET.get('next')
    context = {
        'login_form': login_form,
        'next': next_url,
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
        'successful_submit': successful_submit,
        'reset_email': reset_email
    }
    return render(request, 'userhandling/password_reset_request.html', context)


def password_reset_request_done(request):
    form = PasswordResetRequestForm(request.POST)
    context = {
        'form': form,
        'successful_submit': True,
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
            PasswordResetObject = PasswordReset.objects.get(
                reset_key=reset_key)
            username = PasswordResetObject.username
            user = User.objects.get(username=username)
            user.set_password(pw)
            user.save()

            # Prevent this activation key from beeing reused.
            PasswordResetObject.reset_used = True
            PasswordResetObject.save()

            # send confrmation email
            sender_email = "admin@cinemaple.com"
            sender_name = "Cinemaple"
            subject = "Password successfully changed"
            recipients = [user.email]
            content = "Hi " + user.first_name + \
                ", you have successfully changed your password and can now login using the new password: http://www.cinemaple.com/login"

            email_send = EmailMessage(
                subject, content, sender_name + " <" + sender_email + ">", recipients)
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
        'successful_submit': successful_submit,
        'reset_key': reset_key
    }

    return render(request, 'userhandling/password_reset.html', context)


@login_required
def curr_mov_nights(request):

    movienights = MovieNightEvent.objects.order_by('-date')

    # Horribly inefficiently retrieve active movie night.
    movienight_return = None
    no_movie = True
    movienight_id = None
    for movienight in movienights:
        if movienight.is_active():
            movienight_return = movienight
            no_movie = False
            movienight_id = movienight_return.id

    return details_mov_nights(request, movienight_id, no_movie)


@login_required
def search_movie(request):
    context = {
        'debug': settings.DEBUG,
    }
    return render(request, 'userhandling/movie_search.html', context)


@login_required
def add_movies_from_form(request, movienight,  mov_ID_add):
    ''' Given a list of movie IDs, create movies and add to DB '''

    for movie_id in mov_ID_add:
        # retrieve json via tmdb API
        data = json.loads(imdb_tmdb_api_wrapper_movie(
            request, tmdb_id=movie_id).content)

        # Try to get movie object of previously added, if not exists, add object.
        try:
            m = Movie.objects.get(tmdbID=data["id"])
        except Movie.DoesNotExist:
            # create and svae movie object
            m = Movie(tmdbID=data["id"])
            m.tmdbID = data["id"]
            m.title = data["title"]
            m.year = data["Year"]
            m.director = data["Director"]
            m.producer = data["Producer"]
            m.runtime = data["Runtime"]
            m.actors = data["Actors"]
            m.plot = data["Plot"]
            m.country = data["Country"]
            m.posterpath = data["poster_path"]
            m.trailerlink = data["Trailerlink"]
            m.save()

        movienight.MovieList.add(m)


@user_passes_test(lambda u: u.is_staff)
def add_movie_night(request):

    # if true, votingnight exists and at least one person has voted --> Don't allow for change in movies
    voting_occured = False

    if request.method == 'POST':  # If the form has been submitted...

        # CHeck if hidden field is populated with id, this is only the case if view called to change
        form3 = SneakymovienightIDForm(request.POST, prefix="form3")
        movienightid = form3.data['form3-movienightid']

        if movienightid != "":
            mn = get_object_or_404(MovieNightEvent, pk=movienightid)
            voting_occured = mn.get_num_voted() > 0
        else:
            mn = MovieNightEvent()

        form2 = MovieAddForm(request.POST, prefix="form2")

        form1 = MoveNightForm(request.POST, prefix="form1",
                              instance=mn)  # An unbound form
        if form1.is_valid() and form2.is_valid():  # All validation rules pass
            form1.save()  # This creates or updates the movienight

            # generate list of movie ids to be added:
            num_formfields = 10
            mov_ID_add = []

            # Don't change movie list if voting has occured.
            if not voting_occured:

                # if change mode: first delete all movies
                if movienightid != "":
                    movielist = mn.MovieList.all()
                    movielist.delete()

                for i in range(1, num_formfields+1):
                    # Look at correct formfield
                    movie_id = form2.cleaned_data['movieID{}'.format(i)]
                    # If not empty, generate
                    if movie_id != "":
                        mov_ID_add.append(movie_id)

                # Create and save movies objects
                add_movies_from_form(request, mn, mov_ID_add)

            return redirect('/mov_night/{}'.format(mn.id))
        else:
            return HttpResponse("Form not valid.")
    else:

        form1 = MoveNightForm(prefix="form1")  # An unbound form
        form2 = MovieAddForm(prefix="form2")
        form3 = SneakymovienightIDForm(prefix="form3")
        # TODO: This Fails.
    context = {
        'debug': settings.DEBUG,
        'form1': form1,
        "form2": form2,
        "form3": form3,
        'voting_occured': voting_occured
    }
    return render(request, 'userhandling/admin_movie_add.html', context)


def tmdb_api_wrapper_search(request, query, year=""):
    ''' Since we don't want to expose out API key on the client side, we write a wrapper on the tmdb API'''

    args = {
        "api_key": settings.TMDB_API_KEY,
        "language": "en-US",
        "query": query,
        "page": 1,
        "include_adult": "false",
        "region": "",
        "year": year,
    }

    url_api = "https://api.themoviedb.org/3/search/movie?{}".format(
        urllib.parse.urlencode(args))

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

    for i in range(num_retrieve):
        if i == num_retrieve - 1:
            if num_retrieve == 1:
                resultsstring = data[i][fieldname]
            elif harvard_comma:
                resultsstring = resultsstring + "and " + data[i][fieldname]
            else:
                resultsstring = resultsstring + data[i][fieldname]
        else:
            resultsstring = resultsstring + data[i][fieldname] + ", "

    return resultsstring


def get_person_by_job(data, job_desc):
    ''' Search crew list by job description'''

    resultarray = []
    for entry in data:
        if entry["job"] == job_desc:
            resultarray.append(entry)

    return resultarray


def tmdb_get_movie_images_videos(tmdb_id):

    url_api = "https://api.themoviedb.org/3/movie/" + \
        str(tmdb_id) + "?api_key=" + str(settings.TMDB_API_KEY) + \
        "&append_to_response=videos,credits"

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
    data["Country"] = get_printable_list(
        prod_countries, "name", num_countries, False)

    # Retrieve runtime
    if data["runtime"] == None:
        data["Runtime"] = ""
    else:
        data["Runtime"] = str(data["runtime"]) + " min"

    # Retrieve Director and producer list
    directors = get_person_by_job(data["credits"]["crew"], "Director")
    producers = get_person_by_job(data["credits"]["crew"], "Producer")
    num_directors = 3
    num_producers = 3
    data["Director"] = get_printable_list(
        directors, "name", num_directors, True)
    data["Producer"] = get_printable_list(
        producers, "name", num_producers, True)

    # retrieve youtube link

    video_res = data["videos"]["results"]
    num_videos = len(video_res)

    trailerlink = ""

    if num_videos > 0:
        for i in range(num_videos):
            linktype = video_res[i]["type"]
            site = video_res[i]["site"]
            if site == "YouTube" and linktype == "Trailer":
                trailerlink = "https://www.youtube.com/embed/" + \
                    video_res[i]["key"]

    data["Trailerlink"] = trailerlink

    return data


def imdb_tmdb_api_wrapper_movie(request, tmdb_id):
    ''' Once ID is know, can query more information'''

    tmdb_movie_images_links = tmdb_get_movie_images_videos(tmdb_id)

    return JsonResponse(tmdb_movie_images_links)


@login_required
def dashboard(request):
    return render(request, 'userhandling/dashboard.html')


@user_passes_test(lambda u: u.is_staff)
def man_mov_nights(request):
    return render(request, 'userhandling/admin_movie_night_manage.html')


def attendence_list(request, movienight_id):

    context = {
        'movienight': get_object_or_404(MovieNightEvent, pk=movienight_id),
        'navbar': 'curr_mov_night',
    }

    return render(request, 'userhandling/attendence_list.html', context)


@login_required
def details_mov_nights(request, movienight_id, no_movie=False):

    movienight = None
    ordered_votelist = None
    toppings = None
    user_has_voted = None
    winning_movie = None
    toppings = None
    user_has_reg = None

    if not no_movie:

        movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)

        user_has_reg = movienight.user_has_registered(request.user)

        if user_has_reg:
            toppings = movienight.get_user_topping_list(
                request.user, 'primary')

            # Check if there has been votes cast for this movienight (avoids scenario where user registeres too late and is only user)
            num_voted_mn = movienight.get_num_voted()
            if num_voted_mn > 0:
                winning_movie, _ = movienight.get_winning_movie()

        # if user has voted, show rating and toppings
        user_has_voted = movienight.user_has_voted(request.user)
        movielist = list(movienight.MovieList.all())

        ordered_votelist = []

        if user_has_voted:

            votelist, _ = movienight.get_user_info(request.user)

            for movie in movielist:
                ratingobject = votelist.filter(movie=movie)

                if len(ratingobject) > 1:
                    return HttpResponse("More than one vote for movie {} found.".format(movie.title))
                elif len(ratingobject) == 0:
                    return HttpResponse("No vote found for movie {}.".format(movie.title))

                ordered_votelist.append(ratingobject[0].preference)

    context = {
        'movienight': movienight,
        'navbar': "movie_night_manage",
        'activeMovieExists': False,
        'user_has_voted': user_has_voted,
        'user_has_reg': user_has_reg,
        'ordered_votelist': ordered_votelist,
        'no_movie': no_movie,
        'navbar': 'curr_mov_night',
        'toppings': toppings,
        'winning_movie': winning_movie
    }
    return render(request, 'userhandling/curr_mov_nights.html', context)


@user_passes_test(lambda u: u.is_staff)
def delete_mov_night(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)
    movienight.delete()

    return redirect("man_mov_nights")


@user_passes_test(lambda u: u.is_staff)
def activate_movie_night(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)

    # First check if there exists more than allowed movies:
    activeMovieExists = False

    for movienight_test in MovieNightEvent.objects.all():
        if movienight_test.get_status() == "ACTIVE":
            activeMovieExists = True
            break

    if activeMovieExists:
        context = {
            'movienight': movienight,
            'navbar': "movie_night_manage",
            'activeMovieExists': activeMovieExists,
        }
        return render(request, 'userhandling/curr_mov_nights.html', context)
    else:
        movienight.isdraft = False
        movienight.save()

    return redirect("man_mov_nights")


@user_passes_test(lambda u: u.is_staff)
def deactivate_movie_night(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)

    if movienight.get_status() == "PAST":
        return HttpResponse("Cannot deactivate a movie night in the past.")
    else:
        movienight.isdeactivated = True
        movienight.save()
        return redirect("man_mov_nights")


class UserAttendenceList(generics.ListAPIView):
    serializer_class = UserAttendenceSerializer

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        movienight_id = self.kwargs['movienight_id']

        movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)

        return UserAttendence.objects.filter(movienight=movienight)


class MovieNightEventViewSet(viewsets.ModelViewSet):
    queryset = MovieNightEvent.objects.all().order_by('-date')
    serializer_class = MovieNightEventSerializer


def get_instantciated_movie_add_form(MovieNight):
    # Ugly way to initialize movieform
    initial_dict = {}
    movielist = MovieNight.MovieList.all()
    num_movies = len(movielist)
    for i, movie in enumerate(movielist):
        initial_dict["movieID{}".format(i+1)] = movie.tmdbID

    form2 = MovieAddForm(initial=initial_dict,
                         prefix="form2")  # An unbound for

    return form2, movielist


@user_passes_test(lambda u: u.is_staff)
def change_movie_night(request, movienight_id):
    MovieNight = get_object_or_404(MovieNightEvent, pk=movienight_id)

    voting_occured = MovieNight.get_num_voted() > 0

    form1 = MoveNightForm(
        prefix="form1", instance=MovieNight)  # An unbound for

    form2, movielist = get_instantciated_movie_add_form(MovieNight)
    form3 = SneakymovienightIDForm(prefix="form3", initial={
                                   "movienightid": movienight_id})
    context = {
        'debug': settings.DEBUG,
        'form1': form1,
        "form2": form2,
        "form3": form3,
        "movielist": movielist,
        "navbar": "mod_movie",
        'voting_occured': voting_occured,
    }
    return render(request, 'userhandling/admin_movie_add.html', context)


def topping_add_movie_night(request, movienight_id):

    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)
    voting_enabled = movienight.voting_enabled()
    second_load = False  # used to prevent triggering of modal

    user_attendence = UserAttendence.objects.filter(
        movienight=movienight, user=request.user)[0]

    if request.method == 'POST':

        form = ToppingForm(movienight, request.POST)
        form_brought_along = AlreadyBroughtToppingForm(movienight)
        toppingaddform = ToppingAddForm(request.POST)

        if form.is_valid():

            for id in form.cleaned_data['toppings']:
                topping = get_object_or_404(Topping, pk=id)
                mt = MovienightTopping(
                    topping=topping, user_attendence=user_attendence)
                mt.save()

            # active movinight
            user_attendence.registration_complete = True
            user_attendence.save()

            return redirect(curr_mov_nights)

        elif toppingaddform.is_valid():

            t = Topping()
            instanciated_form = ToppingAddForm(request.POST, instance=t)
            instanciated_form.save()

            # Update Add Form
            form = ToppingForm(movienight)
            form_brought_along = AlreadyBroughtToppingForm(movienight)
            toppingaddform = ToppingAddForm()
            second_load = True

    else:
        form = ToppingForm(movienight)
        form_brought_along = AlreadyBroughtToppingForm(movienight)
        toppingaddform = ToppingAddForm()

    context = {
        'form': form,
        'form_brought_along': form_brought_along,
        'toppingaddform': toppingaddform,
        'voting_enabled': voting_enabled,
        'second_load': second_load
    }
    return render(request, 'userhandling/topping_add.html', context)


def rate_movie_night(request, movienight, user_attendence):
    movielist = list(movienight.MovieList.all())

    # create formset
    prefFormList = formset_factory(VotePreferenceForm, extra=0)

    if request.method == 'POST':

        formset = prefFormList(request.POST)

        if formset.is_valid():
            for form in formset:
                movie = get_object_or_404(
                    Movie, pk=form.cleaned_data['movieID'])

                # In case someone tampers with the hidden input field.
                if not movie in movielist:
                    return HttpResponse("The movie you're voting for is not associated to the movienight you're voting for.")

                vp = VotePreference(
                    user_attendence=user_attendence, movie=movie)
                vp.preference = form.cleaned_data['rating']
                vp.save()

            # Proceed to Toppings Add
            return redirect(topping_add_movie_night, movienight_id=movienight.id)

    else:
        random.shuffle(movielist)

        # if voting disabled, only allow topping indication
        if not movienight.voting_enabled():
            return redirect(topping_add_movie_night, movienight_id=movienight.id)

        formset = prefFormList(initial=[
            {'UserID':   request.user.id,
             'movienightID':   movienight.id,
             'movieID':   movie.id,
             'name':   movie.title
             } for movie in movielist
        ])

    movielist_formset = zip(movielist, formset)

    looper = np.arange(len(movielist))

    context = {
        'movienight': movienight,
        'formset': formset,
        'movielist_formset': movielist_formset,
        'looper': looper,
        'num_movs': len(movielist)
    }
    return render(request, 'userhandling/movienight_vote.html', context)


@login_required
def reg_movie_night(request, movienight_id):

    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)

    if movienight.user_has_registered(request.user):
        return HttpResponse("You've already registered for this movienight.")
    elif not movienight.free_spots() > 0:
        return HttpResponse("Movienight full.")
    else:

        # look for attendence object and create one if not found
        try:
            ua = UserAttendence.objects.filter(
                movienight=movienight, user=request.user)[0]

            # delete all votes
            ua.get_votes().delete()
        except:
            ua = UserAttendence(movienight=movienight, user=request.user)
            ua.save()

        return rate_movie_night(request, movienight, ua)


@login_required
def ureg_movie_night(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)
    ua = UserAttendence.objects.filter(
        movienight=movienight, user=request.user)[0]

    # remove user from attendence list, delete votes, delete toppings
    ua.delete()
    return redirect(curr_mov_nights)


@login_required
def count_votes(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)

    winning_movie, vote_result = movienight.get_winning_movie()

    pairs = vote_result["pairs"]

    # prettify voting dict by resolving movies
    pairs = vote_result["pairs"]
    pairs_dict_movies = {tuple(get_object_or_404(
        Movie, pk=j).title for j in k): v for k, v in pairs.items()}

    strong_pairs = vote_result["strong_pairs"]
    strong_pairs_dict_movies = {tuple(get_object_or_404(
        Movie, pk=j).title for j in k): v for k, v in strong_pairs.items()}

    context = {
        'winning_movie': winning_movie,
        'pairs_dict_movies': pairs_dict_movies.items(),
        'strong_pairs_dict_movies': strong_pairs_dict_movies.items(),
    }
    return render(request, 'userhandling/vote_details.html', context)


@login_required
def user_prefs(request):
    context = {
        'pw_changed': False,
        'user_saved' : False
    }
    return render(request, 'userhandling/user_prefs.html', context)


@login_required
def change_password(request):
    pw_changed = False
    user_saved = False

    if request.method == 'POST':
        form = MyPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            pw_changed = True
            context = {
                'pw_changed': True
            }
            return render(request, 'userhandling/user_prefs.html', context)
    else:
        form = MyPasswordChangeForm(request.user)
    return render(request, 'userhandling/change_password.html', {
        'form': form,
        'pw_changed': pw_changed,
        'user_saved' : user_saved
    })

@login_required
def change_profile(request):

    if request.method == 'POST':
        user = request.user
        old_email = request.user.email

        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            new_email = form.cleaned_data['email']

            if old_email != new_email:

                form.save() #this updates the user settings
                request.user.email = old_email # undo email change
                request.user.profile.email_buffer = new_email

                 # We update activation key
                vh = VerificationHash()
                request.user.profile.activation_key = vh.gen_ver_hash(request.user.username + new_email)

                request.user.save()
                request.user.profile.save()

                datas = {
                    'activation_key' : request.user.profile.activation_key,
                    'email'          : new_email,
                    'first_name'     : request.user.first_name,
                }

                # send activation email
                form.send_activation_new_email(datas)

                email_changed = True
                user_saved = False

            else:
                form.save() #this updates the user settings
                email_changed = False
                user_saved = True

            # reneew form instance to update form content from Profile settings
            form = ProfileUpdateForm(instance=request.user)
            context = {
                'form': form,
                'email_changed': email_changed,
                'user_saved' : user_saved,
                'email_activated' : False,

            }
            return render(request, 'userhandling/change_profile.html', context)
    else:
        form =  ProfileUpdateForm(instance=request.user)

    context = {
        'form': form,
        'email_changed': False,
        'user_saved' : False,
        'email_activated' : False,
    }
    return render(request, 'userhandling/change_profile.html', context)

# Activate email after email update
def activate_emailupdate(request, key):
    profile = get_object_or_404(Profile, activation_key=key)

    new_email = profile.email_buffer
    old_email = profile.user.email

    if new_email == old_email:
        return HttpResponse("Email has already been activated.")

    # update    email settings from buffer
    profile.user.email = new_email

    # reset buffer
    profile.email_buffer = ''

    profile.save()
    profile.user.save()

    #Update Mailchimp
    mc = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID)
    mc.unsubscribe(old_email)
    mc.add_email(new_email)

    if request.user.is_authenticated:
        form =  ProfileUpdateForm(instance=request.user)

        context = {
            'form': form,
            'email_changed': False,
            'user_saved' : False,
            'email_activated' : True,
        }
        return render(request, 'userhandling/change_profile.html', context)
    else:
        return HttpResponse(new_email + " has been activated.")



def trigger_emails(request, movienight_id):
    mc = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID)
    members_list = mc.get_member_list()
    return HttpResponse(movienight_id)