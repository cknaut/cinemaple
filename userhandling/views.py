import datetime
import json
import random
import urllib
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db.utils import OperationalError
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
import numpy as np
import requests
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAdminUser

from .forms import (AlreadyBroughtToppingForm, LoginForm, MoveNightForm,
                    MovieAddForm, MyPasswordChangeForm, PasswordResetForm,
                    PasswordResetRequestForm, PermissionsChangeForm,
                    ProfileUpdateForm, RegistrationForm,
                    SneakymovienightIDForm, ToppingAddForm, ToppingForm,
                    VotePreferenceForm)
from .models import (LocationPermission, Movie, MovieNightEvent,
                     MovienightTopping, PasswordReset, Profile, Topping,
                     UserAttendence, VotePreference)
from .serializers import (LocationPermissionSerializer,
                          MovieNightEventSerializer,
                          RestrictedLocationPermissionSerializer,
                          UserAttendenceSerializer)
from .utils import (check_ml_health, Mailchimp, send_role_change_email,
                    VerificationHash)


# Render Index Page, manage register
def index(request):

    past_mn_id = [movie_night.id for movie_night
                  in MovieNightEvent.objects.all()
                  if movie_night.get_status() == "PAST"]
    mn_in_past = MovieNightEvent.objects.filter(id__in=past_mn_id)

    show_last = 5
    movienights_render = mn_in_past.order_by('-date')[:show_last]

    num_mn_past = len(mn_in_past)
    start_counter = num_mn_past - show_last

    # Total Runtime of all winner movies in past
    total_rt = 0
    for movie_night in mn_in_past:
        _, _, runtime = movie_night.get_winning_movie()
        total_rt += runtime

    # if request.user.is_authenticated:
    #     return redirect("curr_mov_nights")
    successful_verified = False
    context = {
        'successful_verified': successful_verified,
        'email': "",
        'username': "",
        'movienights' : movienights_render,
        'total_rt'  : total_rt,
        'num_mn_past' : num_mn_past,
        'mn_start_counter'      : start_counter,
        'num_show'              : show_last
    }
    return render(request, 'userhandling/index.html', context)

# View called from activation email. Activate user if link didn't expire \
# (48h default), or offer to send a second link if the first expired.


def activation(request, key):
    profile = get_object_or_404(Profile, activation_key=key)

    if profile.user.is_active is False:
        if timezone.now() > profile.key_expires:
            id_user = profile.user.id
            # TODO THis will fail
            new_activation_link(request, id_user)

        else:  # Activation successful
            # Activate user.
            profile.user.is_active = True
            profile.user.save()

            # Subscribe to Mailchimp list.
            mail_chimp = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID)
            mail_chimp.add_email(profile.user.email, profile.user.first_name,
                                 profile.user.last_name)

            # Add tag to contact, this will define if
            # correct emails will be send.
            loc_id_tag = profile.get_location_permissions()
            location_ids = [i.location.id for i in loc_id_tag]

            # ties user to location and will never be altered
            location_tags = ["{}{}".format(settings.MC_PREFIX_LOCPERMID, i)
                             for i in location_ids]

            # specifies user access. Is present only if user has access.
            has_access_tags = ["{}{}".format(settings.MC_PREFIX_HASACCESSID, i)
                               for i in location_ids]

            for location_tag, has_access_tags in \
                    zip(location_tags, has_access_tags):
                mail_chimp.add_tag_to_user(location_tag, profile.user.email)
                mail_chimp.add_tag_to_user(has_access_tags, profile.user.email)

            sender_email = "info@cinemaple.com"
            sender_name = "Cinemaple"
            subject = "Welcome to Cinemaple!"
            recipients = [profile.user.email]

            context_email = {
                'firstname'    : profile.user.first_name
            }
            content = render_to_string(
                "userhandling/emails/cinemaple_email_welcome.html",
                context_email
            )

            email = EmailMultiAlternatives(
                subject, '',
                sender_name + " <" + sender_email + ">",
                recipients)
            email.attach_alternative(content, "text/html")
            email.send()

            # TODO: Avoid Multiplocation of index routine
            past_mn_id = [movie_night.id for movie_night
                          in MovieNightEvent.objects.all()
                          if movie_night.get_status() == "PAST"]
            mn_in_past = MovieNightEvent.objects.filter(id__in=past_mn_id)

            show_last = 5
            movienights_render = mn_in_past.order_by('-date')[:show_last]

            num_mn_past = len(mn_in_past)
            start_counter = num_mn_past - show_last

            # Total Runtime of all winner movies in past
            total_rt = 0
            for movie_night in mn_in_past:
                _, _, runtime = movie_night.get_winning_movie()
                total_rt += runtime

            successful_verified = True
            context = {
                'successful_verified'   : successful_verified,
                'email'                 : profile.user.email,
                'username'              : profile.user,
                'movienights'           : movienights_render,
                'total_rt'              : total_rt,
                'num_mn_past'           : num_mn_past,
                'mn_start_counter'      : start_counter,
                'num_show'              : show_last
            }
            return render(request, 'userhandling/index.html', context)

    # If user is already active, simply display error message
    else:
        return HttpResponse("User already registered.")


def new_activation_link(request, user_id):
    form = ProfileUpdateForm()
    datas = {}
    user = User.objects.get(id=user_id)
    if user is not None and not user.is_active:

        # We generate a random activation key
        verification_hash = VerificationHash()
        datas['activation_key'] = verification_hash.\
            gen_ver_hash(datas['username'])

        # Update profile with new activation key and expiry data.
        profile = Profile.objects.get(user=user)
        profile.activation_key = datas['activation_key']
        profile.key_expires = datetime.datetime.strftime(
            datetime.datetime.now() + datetime.timedelta(days=2),
            "%Y-%m-%d %H:%M:%S")
        profile.save()

        if request.method == 'POST':
            form = ProfileUpdateForm(request.POST)
        if form.is_valid():
            datas = {}
            datas['first_name'] = profile.user.first_name
            datas['email'] = profile.email_buffer
            reset_email = form.send_activation_new_email()  # noqa: F841, E501  # pylint: disable=unused-variable

    return redirect('index')


def registration(request, inv_code):

    # validate invitation cod
    try:
        loc_p = LocationPermission.objects.get(invitation_code=inv_code)
        if loc_p.can_invite():
            code_valid = True
        else:
            code_valid = False
    except LocationPermission.DoesNotExist:
        code_valid = False

    if not code_valid:
        return HttpResponse("Invalid invitation link.")

    # instanciated form with invitation code passed in URL
    registration_form = RegistrationForm(initial={'invitation_code': inv_code})

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
            datas['invitation_code'] = registration_form.\
                cleaned_data['invitation_code']

            # TODO: Check if user already exists

            # We generate a random activation key
            verification_hash = VerificationHash()
            datas['activation_key'] = verification_hash.\
                gen_ver_hash(datas['username'])

            registration_form.send_activation_email(datas)
            registration_form.save(datas)  # Save the user and his profile

            successful_reg_submit = True
            subscribe_email = datas['email']

    context = {
        'form': registration_form,
        'successful_submit'     : successful_reg_submit,
        'subscribe_email'       : str(subscribe_email),
        'invitation_code'       : inv_code
    }
    return render(request, 'userhandling/registration.html', context)


def my_login(request):
    login_form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(request.POST)
        next_url = request.POST.get('next')
        if form.is_valid():
            # At this point, the clean() fuction in the form already made \
            # sure that the user is valid and active.
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
            reset_email = form.populate_passwordreset_send_email()
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
        passwordresetobject = PasswordReset.objects.get(reset_key=reset_key)
        error = 0
    except PasswordReset.DoesNotExist:
        error = -1
        return error

    if timezone.now() > passwordresetobject.created_at + \
       datetime.timedelta(days=2):
        error = -2
    if passwordresetobject.reset_used:
        error = -3

    return error


def password_reset(request, reset_key):

    form = PasswordResetForm()
    successful_submit = False

    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            # get password from form
            password = form.cleaned_data['password1']

            # Retrieve user object and reset password.
            passwordresetobject = PasswordReset.objects.get(
                reset_key=reset_key)
            username = passwordresetobject.username
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()

            # Prevent this activation key from beeing reused.
            passwordresetobject.reset_used = True
            passwordresetobject.save()

            sender_email = "info@cinemaple.com"
            sender_name = "Cinemaple"
            subject = "Password successfully changed"
            recipients = [user.email]

            context_email = {
                'username'          : user.username,
                'firstname'          : user.first_name,
            }

            html_email = render_to_string(
                "userhandling/emails/cinemaple_email_pw_reset_done.html",
                context_email
            )

            email = EmailMultiAlternatives(
                subject,
                '',
                sender_name + " <" + sender_email + ">",
                recipients
            )

            email.attach_alternative(html_email, "text/html")
            email.send()

            successful_submit = True
    else:

        # Check password link for multiple error cases.
        link_check_res = check_pw_rest_link(request, reset_key)

        if link_check_res == -1:
            return HttpResponse("Password reset link could not be associated \
                                with valid username.")
        if link_check_res == -2:
            return HttpResponse("Password reset key expired, \
                                 please restart password reset.")
        if link_check_res == -3:
            return HttpResponse("Password reset link has already been used.")

    context = {
        'form'              : form,
        'successful_submit' : successful_submit,
        'reset_key'         : reset_key
    }

    return render(request, 'userhandling/password_reset.html', context)


@login_required
def curr_mov_nights(request):

    # TODO: Update this with new multi host access management
    has_revoked = request.user.profile.has_at_least_one_revk()
    if not has_revoked:
        movienights = MovieNightEvent.objects.order_by('-date')
    else:
        return details_mov_nights(request, None, True)

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
# Given a list of movie IDs, create movies and add to DB.
def add_movies_from_form(request, movienight, mov_id_add):

    for movie_id in mov_id_add:
        # retrieve json via tmdb API
        data = json.loads(imdb_tmdb_api_wrapper_movie(
            request, tmdb_id=movie_id).content)

        # Try to get movie object of previously added, if not exists,
        # add object.
        try:
            movie = Movie.objects.get(tmdbid=data["id"])
        except Movie.DoesNotExist:
            # create and svae movie object
            movie = Movie(tmdbid=data["id"])
            movie.tmdbid = data["id"]
            movie.title = data["title"]
            movie.year = data["Year"]
            movie.director = data["Director"]
            movie.producer = data["Producer"]
            movie.runtime = data["Runtime"]
            movie.actors = data["Actors"]
            movie.plot = data["Plot"]
            movie.country = data["Country"]
            movie.posterpath = data["poster_path"]
            movie.trailerlink = data["Trailerlink"]
            movie.save()

        movienight.MovieList.add(movie)


@user_passes_test(lambda u: u.is_staff)
def add_movie_night(request):

    # if true, votingnight exists and at least one person has voted --> \
    #  Don't allow for change in movies
    voting_occured = False

    if request.method == 'POST':  # If the form has been submitted...

        # Check if hidden field is populated with id, this is only the case \
        # if view called to change
        form3 = SneakymovienightIDForm(request.POST, prefix="form3")
        movienightid = form3.data['form3-movienightid']

        if movienightid != "":
            movie_night = get_object_or_404(MovieNightEvent, pk=movienightid)
            voting_occured = movie_night.get_num_voted() > 0
        else:
            movie_night = MovieNightEvent()

        form2 = MovieAddForm(request.POST, prefix="form2")

        form1 = MoveNightForm(request.POST, prefix="form1",
                              instance=movie_night)  # An unbound form
        if form1.is_valid() and form2.is_valid():  # All validation rules pass
            form1.save()  # This creates or updates the movienight

            # generate list of movie ids to be added:
            num_formfields = 10
            mov_id_add = []

            # Don't change movie list if voting has occured.
            if not voting_occured:

                # if change mode: first delete all movies
                if movienightid != "":
                    movielist = movie_night.MovieList.all()
                    movielist.delete()

                for i in range(1, num_formfields + 1):
                    # Look at correct formfield
                    movie_id = form2.cleaned_data['movieid{}'.format(i)]
                    # If not empty, generate
                    if movie_id != "":
                        mov_id_add.append(movie_id)

                # Create and save movies objects
                add_movies_from_form(request, movie_night, mov_id_add)

            return redirect('/mov_night/{}'.format(movie_night.id))
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
        'navbar': 'admin',
        'voting_occured': voting_occured
    }
    return render(request, 'userhandling/admin_movie_add.html', context)


# Wrap bare tmdb API request
def tmdb_api_wrapper_search(request, query, year=""):

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
    except AttributeError:
        raise Exception("Critical TMDB API error")

    return JsonResponse(data)


#  Using the full JSON, returns print-friendly string of first n occurences
def get_printable_list(data, fieldname, num_retrieve, harvard_comma):

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


# Search crew list by job description
def get_person_by_job(data, job_desc):

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
    except AttributeError:
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
    if data["runtime"] is None:
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


# Once ID is know, can query more information
def imdb_tmdb_api_wrapper_movie(request, tmdb_id):

    tmdb_movie_images_links = tmdb_get_movie_images_videos(tmdb_id)

    return JsonResponse(tmdb_movie_images_links)


@login_required
def dashboard(request):
    return render(request, 'userhandling/dashboard.html')


@user_passes_test(lambda u: u.is_staff)
def man_mov_nights(request):
    context = {
        'navbar' : 'admin'
    }
    return render(request, 'userhandling/admin_movie_night_manage.html',
                  context)


def attendence_list(request, movienight_id):

    context = {
        'movienight': get_object_or_404(MovieNightEvent, pk=movienight_id),
        'navbar': 'curr_mov_night',
    }

    return render(request, 'userhandling/attendence_list.html', context)


@login_required
def past_mov_nights(request):
    context = {
        'navbar' : 'past_mov_nights'
    }
    return render(request, 'userhandling/past_mov_nights.html', context)


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

        # Check if there has been votes cast for this movienight \
        # (avoids scenario where user registeres too late and is only user)
        num_voted_mn = movienight.get_num_voted()
        if num_voted_mn > 0:
            winning_movie, _, _ = movienight.get_winning_movie()

        # if user has voted, show rating and toppings
        user_has_voted = movienight.user_has_voted(request.user)
        movielist = list(movienight.MovieList.all())

        ordered_votelist = []

        if user_has_voted:

            votelist, _ = movienight.get_user_info(request.user)

            for movie in movielist:
                ratingobject = votelist.filter(movie=movie)

                if len(ratingobject) > 1:
                    return HttpResponse("More than one vote for movie {} \
                                        found.".format(movie.title))
                elif not ratingobject:
                    return HttpResponse("No vote found for movie {}."
                                        .format(movie.title))

                ordered_votelist.append(ratingobject[0].preference)

    context = {
        'movienight': movienight,
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
    activemovieexists = False

    for movienight_test in MovieNightEvent.objects.all():
        if movienight_test.get_status() == "ACTIVE":
            activemovieexists = True
            break

    if activemovieexists:
        context = {
            'movienight': movienight,
            'navbar': "movie_night_manage",
            'activeMovieExists': activemovieexists,
        }
        return render(request, 'userhandling/curr_mov_nights.html', context)
    else:
        _, context = check_ml_health(movienight.location.id)
        context['movienight_id'] = movienight_id

        return render(request, 'userhandling/activate_user_check.html'
                      , context)


def gen_mn_email(request, movienight, type_email):
    context_email = {
        'movienight'    : movienight,
        'user'          : request.user,
        'type'          : type_email,
    }

    html_email = render_to_string(
        "userhandling/emails/cinemaple_email_invite.html",
        context_email
    )

    return html_email


def gen_activation_email(request, link, type_email):
    context_email = {
        'user'          : request.user,
        'type'          : type_email,
        'link'          : link,
    }

    html_email = render_to_string("userhandling/emails/ \
                 cinemaple_email_activate.html", context_email)

    return html_email


def preview_email_invitation(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)
    email_html = gen_mn_email(request, movienight, type_email='invitation'),
    return HttpResponse(email_html)


def preview_mn_email(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)

    context_page = {
        'email_html'    : gen_mn_email(
            request,
            movienight,
            type_email='reminder'
        ),
        'movienight'    : movienight,
    }

    return render(request, 'userhandling/check_email.html', context_page)


def schedule_email(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)

    html_data_reminder = gen_mn_email(request, movienight,
                                      type_email='reminder')
    html_data_invitation = gen_mn_email(request, movienight,
                                        type_email='invitation')

    time_activation = movienight.get_activation_date()
    time_reminder = movienight.get_reminder_date()

    # Location ID nedded to address correct users
    loc_id = movienight.location.id

    # First Generate 2 Campaigns
    mail_chimp = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID)

    reply_to = 'info@cinemaple.com'
    preview_text = 'We have a treat for you!'
    from_name = request.user.first_name

    title1 = 'INVITATION Movie Night: {}'.format(movienight.motto)
    title2 = 'REMINDER Movie Night: {}'.format(movienight.motto)

    subject_line1 = 'Invitation for Movie Night: {}'.format(movienight.motto)
    subject_line2 = 'Reminder for Movie Night: {}'.format(movienight.motto)

    res1 = mail_chimp.create_campaign(time_activation, reply_to, subject_line1,
                                      preview_text, title1, from_name,
                                      html_data_invitation, loc_id)
    res2 = mail_chimp.create_campaign(time_reminder, reply_to, subject_line2,
                                      preview_text, title2, from_name,
                                      html_data_reminder, loc_id)

    # Check if MC Statuscodes are ok
    if res1 == 204 and res2 == 204:
        movienight.isdraft = False
        movienight.save()
    else:
        return HttpResponse("Mailchimp campaign creation unsuccessful.")

    return redirect(curr_mov_nights)


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
    # This view should return a list of all the movienights \
    # for the currently authenticated user.

    def get_queryset(self):
        movienight_id = self.kwargs['movienight_id']

        movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)

        return UserAttendence.objects.filter(movienight=movienight)


class ProfileList(generics.ListAPIView):
    # This one is called from the manage user view for hosts
    serializer_class = LocationPermissionSerializer

    def get_queryset(self):
        # Only show all users that are associated to \
        # locations where user is host
        managed_locperm = self.request.user.profile.get_managed_loc_perms()

        active_ids = [locperm.id for locperm in managed_locperm
                      if locperm.is_active()]
        active_locperms = managed_locperm.filter(id__in=active_ids)

        return active_locperms


class ProfileListInvite(generics.ListAPIView):
    # This one is called from the invitation view
    serializer_class = RestrictedLocationPermissionSerializer

    def get_queryset(self):
        # Show Users which have been invited by active user

        managed_locperm = self.request.user.profile.get_intivees_locperms()

        # Filter out inactive locperms
        active_ids = [locperm.id for locperm in managed_locperm
                      if locperm.is_active()]
        active_locperms = managed_locperm.filter(id__in=active_ids)

        return active_locperms


class MovieNightEventViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = MovieNightEvent.objects.all().order_by('-date')
    serializer_class = MovieNightEventSerializer


class PastMovieNightEventViewSet(viewsets.ModelViewSet):

    # in order to avoid problems arising from starting from scratch

    try:
        past_mn_id = [movie_night.id for movie_night
                      in MovieNightEvent.objects.all()
                      if movie_night.get_status() == "PAST"]

        queryset = MovieNightEvent.objects.filter(id__in=past_mn_id)
        # queryset = MovieNightEvent.objects.all().order_by('-date')
    except OperationalError:
        queryset = MovieNightEvent.objects.filter(id=1)

    serializer_class = MovieNightEventSerializer


def get_instantciated_movie_add_form(movienight):
    # Ugly way to initialize movieform
    initial_dict = {}
    movielist = movienight.MovieList.all()
    for i, movie in enumerate(movielist):
        initial_dict["movieid{}".format(i + 1)] = movie.tmdbid

    form2 = MovieAddForm(initial=initial_dict,
                         prefix="form2")  # An unbound for

    return form2, movielist


@user_passes_test(lambda u: u.is_staff)
def change_movie_night(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)

    voting_occured = movienight.get_num_voted() > 0

    form1 = MoveNightForm(
        prefix="form1", instance=movienight)  # An unbound for

    form2, movielist = get_instantciated_movie_add_form(movienight)
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

            for id_num in form.cleaned_data['toppings']:
                topping = get_object_or_404(Topping, pk=id_num)
                movienight_topping = MovienightTopping(
                    topping=topping, user_attendence=user_attendence)
                movienight_topping.save()

            # active movinight
            user_attendence.registration_complete = True
            user_attendence.save()

            return redirect(curr_mov_nights)

        elif toppingaddform.is_valid():

            topping = Topping()
            instanciated_form = ToppingAddForm(request.POST, instance=topping)
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
        'second_load': second_load,
        "navbar": "curr_mov_night",
    }
    return render(request, 'userhandling/topping_add.html', context)


def rate_movie_night(request, movienight, user_attendence):
    movielist = list(movienight.MovieList.all())

    # create formset
    prefformlist = formset_factory(VotePreferenceForm, extra=0)

    if request.method == 'POST':

        formset = prefformlist(request.POST)

        if formset.is_valid():
            for form in formset:
                movie = get_object_or_404(
                    Movie, pk=form.cleaned_data['movieid'])

                # In case someone tampers with the hidden input field.
                if movie not in movielist:
                    return HttpResponse("The movie you're voting for is \
                           not associated to the movienight \
                           you're voting for.")

                vote_preference = VotePreference(
                    user_attendence=user_attendence, movie=movie)
                vote_preference.preference = form.cleaned_data['rating']
                vote_preference.save()

            # Proceed to Toppings Add
            return redirect(topping_add_movie_night,
                            movienight_id=movienight.id)

    else:
        random.shuffle(movielist)

        # if voting disabled, only allow topping indication
        if not movienight.voting_enabled():
            return redirect(topping_add_movie_night,
                            movienight_id=movienight.id)

        formset = prefformlist(initial=[
            {'movieid': movie.id,
             'rating': 0
             } for movie in movielist
        ])

    movielist_formset = zip(movielist, formset)

    looper = np.arange(len(movielist))

    context = {
        'movienight': movienight,
        'formset': formset,
        'movielist_formset': movielist_formset,
        'looper': looper,
        'num_movs': len(movielist),
        'navbar': 'curr_mov_night'
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
            user_attendence = UserAttendence.objects.filter(
                movienight=movienight, user=request.user)[0]
            # delete all votes
            user_attendence.get_votes().delete()
        except IndexError:
            user_attendence = UserAttendence(
                movienight=movienight, user=request.user
            )
            user_attendence.save()

        return rate_movie_night(request, movienight, user_attendence)


@login_required
def ureg_movie_night(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)
    user_attendence = UserAttendence.objects.filter(
        movienight=movienight, user=request.user)[0]

    # remove user from attendence list, delete votes, delete toppings
    user_attendence.delete()
    return redirect(curr_mov_nights)


@login_required
def count_votes(request, movienight_id):
    movienight = get_object_or_404(MovieNightEvent, pk=movienight_id)

    winning_movie, vote_result, _ = movienight.get_winning_movie()

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
        "navbar": "curr_mov_night",
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

    if request.method == 'POST':
        form = MyPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            pw_changed = True
            form = MyPasswordChangeForm(request.user)
            context = {
                'form': form,
                'pw_changed': True,
                'navbar' : 'user'
            }
            return render(request, 'userhandling/change_password.html',
                          context)
    else:
        form = MyPasswordChangeForm(request.user)
    return render(request, 'userhandling/change_password.html', {
        'form': form,
        'pw_changed': pw_changed,
        'navbar': 'user'
    })


@login_required
def change_profile(request):

    if request.method == 'POST':
        user = request.user
        old_email = user.email

        form = ProfileUpdateForm(request.POST, instance=user)
        if form.is_valid():
            new_email = form.cleaned_data['email']

            if old_email != new_email:

                form.save()  # This updates the user settings
                user.email = old_email  # undo email change
                user.profile.email_buffer = new_email

                # We update activation key
                verification_hash = VerificationHash()
                user.profile.activation_key = verification_hash.\
                    gen_ver_hash(user.username + new_email)

                user.save()
                user.profile.save()

                datas = {
                    'activation_key' : user.profile.activation_key,
                    'email'          : new_email,
                    'first_name'     : user.first_name,
                }

                # send activation email
                form.send_activation_new_email(datas)

                email_changed = True
                user_saved = False

            else:
                form.save()  # This updates the user settings
                email_changed = False
                user_saved = True

            # reneew form instance to update form content from Profile settings
            form = ProfileUpdateForm(instance=user)
            context = {
                'form': form,
                'email_changed': email_changed,
                'user_saved' : user_saved,
                'email_activated' : False,
                'navbar' : 'user'
            }
            return render(request, 'userhandling/change_profile.html', context)
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {
        'form': form,
        'email_changed': False,
        'user_saved' : False,
        'email_activated' : False,
        'navbar' : 'user'
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

    # Update Mailchimp
    mail_chimp = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID)
    mail_chimp.change_subscriber_email(old_email, new_email)

    if request.user.is_authenticated:
        form = ProfileUpdateForm(instance=request.user)

        context = {
            'form': form,
            'email_changed': False,
            'user_saved' : False,
            'email_activated' : True,
        }
        return render(request, 'userhandling/change_profile.html', context)
    else:
        return HttpResponse(new_email + " has been activated.")


@user_passes_test(lambda u: u.is_staff)
def ml_health(request):

    locperms_managed = request.user.profile.get_hosting_location_perms()

    for locperm in locperms_managed:
        _, context = check_ml_health(locperm.location.id)

    context['navbar'] = 'admin'
    return render(request, 'userhandling/mailinglist_health.html', context)


@user_passes_test(lambda u: u.is_staff)
def show_loc_users(request):
    context = {
        'navbar' : 'admin'
    }
    return render(request, 'userhandling/loc_user_list.html', context)


@login_required
def faq(request):

    context = {
        'navbar'              : "faq"
    }
    return render(request, 'userhandling/faq.html', context)


def priv_pol(request):
    return render(request, 'userhandling/priv_pol.html')


@login_required
def manage_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    # Verify permission
    if user not in request.user.profile.get_managed_users():
        return HttpResponse("You have insufficient permissions \
                            to modify this users's status")

    # Get all user perms of user
    location_permissions = user.profile.get_loc_perms_of_host(request.user)

    context = {
        'navbar'              : "admin",
        'user'                : user,
        'inv_code_changed'                : False,
        'location_permissions'              : location_permissions,
    }
    return render(request, 'userhandling/man_user.html', context)


def gen_new_invitation_key(request, user_id, locperm_id):

    user = get_object_or_404(User, pk=user_id)
    locperm = get_object_or_404(LocationPermission, pk=locperm_id)

    # get all user perms of user
    location_permissions = user.profile.get_loc_perms_of_host(request.user)

    # Verify permission
    if user not in request.user.profile.get_managed_users():
        return HttpResponse("You have insufficient permissions to \
                            modify this users's status")

    # Generate new invtitation code

    new_invitation_code = uuid.uuid4()
    locperm.invitation_code = new_invitation_code
    locperm.save()

    context = {
        'navbar'              : "admin",
        'user'                : user,
        'change_loc'                        : locperm.location,
        "change_inv_key"                    : new_invitation_code,
        'inv_code_changed'                : True,
        'location_permissions'              : location_permissions,
    }
    return render(request, 'userhandling/man_user.html', context)


def change_role(request, user_id, locperm_id):
    user = get_object_or_404(User, pk=user_id)
    locperm = get_object_or_404(LocationPermission, pk=locperm_id)

    # Verify permission
    if user not in request.user.profile.get_managed_users():
        return HttpResponse("You have insufficient permissions \
                            to modify this users's status")

    if request.method == 'POST':
        form = PermissionsChangeForm(request.POST, instance=locperm)
        if form.is_valid():

            new_role = form.cleaned_data['role']
            form.save()  # This updates the user settings
            location_permissions = user.profile.\
                get_loc_perms_of_host(request.user)

            # Notify user
            if new_role == 'AM' or new_role == 'HO':
                send_role_change_email(user, new_role, locperm.location)

            # add invitation code if user changed from could \
            # invite to could not invite

            # user_can_invite = locperm.can_invite()
            # user_could_invite = locperm.can_invite()
            # if not user_could_invite and user_can_invite:
            #     new_invitation_code = uuid.uuid4()
            #     locperm.invitation_code = new_invitation_code
            #     locperm.save()

            context = {
                'navbar'                : "admin",
                'user'                  : user,
                'change_loc'            : locperm.location,
                'change_perm'           : locperm.get_role_display,
                'inv_code_changed'      : False,
                'permission_changed'    : True,
                'location_permissions'  : location_permissions,
            }
            return render(request, 'userhandling/man_user.html', context)

    else:
        form = PermissionsChangeForm(instance=locperm)

    context = {
        'navbar'              : "admin",
        'user'                : user,
        'locperm'             : locperm,
        'form'                : form
    }

    return render(request, 'userhandling/change_perms.html', context)


def toggle_access_from_hash(rev_access_hash):
    # Change user access from Treu to False or from False to True
    locperm = get_object_or_404(LocationPermission,
                                rev_access_hash=rev_access_hash)

    old_status = locperm.revoked_access
    locperm.revoked_access = not old_status
    locperm.save()

    # Update MC tag used to exclude revoked access users from mailings
    mail_chimp = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID)
    has_access_tag = "{}{}".format(settings.MC_PREFIX_HASACCESSID,
                                   locperm.location.id)

    if not old_status:
        # if toggled from no revokec access to revoked access
        mail_chimp.untag(has_access_tag, locperm.user.profile.user.email)
    else:
        mail_chimp.add_tag_to_user(
            has_access_tag, locperm.user.profile.user.email
        )
    return 0

# Called from manage user page accessible for hosts)
@user_passes_test(lambda u: u.profile.is_host)
def toggle_access_admin(request, rev_access_hash):
    toggle_access_from_hash(rev_access_hash)
    locperm = get_object_or_404(LocationPermission,
                                rev_access_hash=rev_access_hash)
    user = locperm.user

    # Get all user perms of user
    location_permissions = user.profile.get_loc_perms_of_host(request.user)

    context = {
        'navbar'                    : "admin",
        'user'                      : user,
        'inv_code_changed'          : False,
        'location_permissions'      : location_permissions,
    }
    return render(request, 'userhandling/man_user.html', context)


@user_passes_test(lambda u: u.profile.is_inviter)
def invite(request):

    locperms = request.user.profile.get_invitable_location_perms()
    context = {
        'navbar'    : 'invite',
        'locperms'  : locperms,
    }
    return render(request, 'userhandling/invite.html', context)

# Called from Invite paged
@user_passes_test(lambda u: u.profile.is_inviter)
def toggle_access_invite(request, rev_access_hash):
    toggle_access_from_hash(rev_access_hash)
    return redirect("view_invited")


# Revoke access from Email
def revoke_access_from_email(request, rev_access_hash):
    locperm = get_object_or_404(LocationPermission,
                                rev_access_hash=rev_access_hash)

    locperm.revoked_access = True
    locperm.save()

    # Update MC tag used to exclude revoked access users from mailings
    mail_chimp = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID)

    # if toggled from no revokec access to revoked access
    has_access_tag = "{}{}".format(settings.MC_PREFIX_HASACCESSID,
                                   locperm.location.id)
    mail_chimp.untag(has_access_tag, locperm.user.profile.user.email)

    context = {
        'navbar'    : 'invite',
        'locperm'   : locperm,
    }
    return render(request, 'userhandling/revoked_from_email.html', context)


def view_invited(request):
    locperms = request.user.profile.get_invitable_location_perms()
    context = {
        'navbar'    : 'invite',
        'locperms'  : locperms,
    }
    return render(request, 'userhandling/view_invited.html', context)
