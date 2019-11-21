from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import pytz
from django.utils import timezone
from .utils import badgify
# from urllib.request import urlopen
# from PIL import Image
import time
import random
import numpy as np
import uuid

# import scipy.ndimage.gaussian_filter

from py3votecore.schulze_method import SchulzeMethod
from py3votecore.condorcet import CondorcetHelper
from .vote import get_pref_lists, prepare_voting_dict


class Location(models.Model):
    name = models.CharField(max_length=200)
    street = models.CharField(max_length=200)
    zip_code = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    country = models.CharField(max_length=200)

    def print_address(self):
        return '{}, {} {}, {}'.format(self.street, self.zip_code, self.city, self.state)

    def __str__(self):              # __unicode__ on Python 2
        return self.name


class LocationPermission(models.Model):
    ROLE_CHOICES = [
    ('HO', 'Host'),
    ('AM', 'Ambassador'),
    ('GU', 'Guest'),
    ('RW', 'Revoked Access'),
    ]
    
    location = models.ForeignKey(Location, on_delete=models.CASCADE)

    # ALl users get an activation code, so you'll have to manually check if user can invite using get_invite_code
    #NEVER DIRECTLY RETRIEVE THIS ALWAYS USE get_invite_code()
    invitation_code = models.UUIDField(default=uuid.uuid4, editable=True)
    

    def get_invite_code(self):
        if self.can_invite:
            return self.invitation_code
        else:
            return ""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locperms')
    inviter = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='invitor')


    role = models.CharField(
        max_length=2,
        choices=ROLE_CHOICES,
        default='GU',
    )

    def can_invite(self):
        # Hosts and Amb. can invite
        return self.role in ('HO', 'AM')

    def is_host(self):
        return self.role in ('HO')

    def __str__(self):              # __unicode__ on Python 2
        return "{} / {} / {}".format(self.user.username, self.location, self.role) 


# We create a one-to-one map from the built-in User model to a Profile model
# From https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    email_buffer = models.EmailField(default='') # contains unverified email
    birth_date = models.DateField(null=True, blank=True)
    activation_key = models.CharField(max_length=40, blank=True)
    key_expires = models.DateTimeField(null=True, blank=True)


    

    def get_location_permissions(self):
        return self.user.locperms.all()


    def get_loc_perms_of_host(self, hostuser):
        # given a host, return all user permissions of user for which host is host
        assert hostuser.profile.is_host(), "User must be host"

        host_locs = hostuser.profile.get_hosted_locations()
        self_locperms = self.get_location_permissions()

        return self_locperms.filter(location__in=host_locs)

    def get_hosting_location_perms(self):
        # Return Location Permissions of locations where user can invite
        loc_permissions = self.user.locperms.filter(role='HO')
        return loc_permissions

    def get_hosted_locations(self):
        # Returns list of locations for which user has Host status
        return [i.location for i in self.get_hosting_location_perms()]

    def get_managed_loc_perms(self):
        # get location permissions for locations for which user is host
        return LocationPermission.objects.filter(location__in=self.get_hosted_locations())

    
    def get_managed_users(self):
        # Get set of all users which are associated to a location for which user is host
        man_users =  [i.user for i in self.get_managed_loc_perms()]
        return man_users

    def is_host(self):
        # True if host for at least one locations, will be used to unlock all hidden urls
        if len(self.get_hosting_location_perms()) > 0:
            return True
        else:
            return False



    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()




class PasswordReset(models.Model):
    username = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reset_key = models.CharField(max_length=40, blank=True)
    reset_used = models.BooleanField(default=False)

    def __str__(self):              # __unicode__ on Python 2
        return self.username

class Movie(models.Model):
    tmdbID = models.CharField(max_length=200)
    title = models.CharField(max_length=500)
    year = models.CharField(max_length=4)
    director = models.CharField(max_length=500)
    producer = models.CharField(max_length=500)
    runtime = models.CharField(max_length=10)
    actors = models.CharField(max_length=500)
    plot = models.TextField(max_length=2000)
    country = models.CharField(max_length=500)
    posterpath = models.CharField(max_length=100)
    trailerlink = models.CharField(max_length=200)
    on_netflix = models.BooleanField(default=False)
    netflix_link = models.TextField(blank=True)
    on_amazon = models.BooleanField(default=False)
    amazon_link = models.TextField(blank=True)

    def get_runtime_int(self):
        runtime = self.runtime
        runtime = runtime.replace('min', '')
        runtime_int = int(runtime)
        return runtime_int

    def __str__(self):
        return self.title

    # def filtered_poster(self): 
        # print("Running filter function")       
        # return Image.open(urlopen("https://image.tmdb.org/t/p/w200"+self.posterpath))


class VotingParameters(models.Model):
    vote_disable_before = models.DurationField() # how long before the movienight the vote should e closed
    reminder_email_before = models.DurationField() # how long before the movienight the final reminder email sould be sent
    initial_email_after = models.DurationField() # how long after activation of movienight should emails be send out?
    def __str__(self):
        return "Only instance of this model."

class MovieNightEvent(models.Model):
    motto = models.CharField(max_length=200)
    description = models.TextField(max_length=10000)
    date = models.DateTimeField('date published')
    isdraft = models.BooleanField(default=True)
    isdeactivated = models.BooleanField(default=False)
    MovieList = models.ManyToManyField(Movie, blank=True)
    MaxAttendence = models.IntegerField(blank=False, default=25)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)

    def free_spots(self):
        return self.MaxAttendence - self.get_num_registered()

    def get_topping_list(self):
        uas = UserAttendence.objects.filter(movienight=self)
        already_chosen_topings = MovienightTopping.objects.filter(user_attendence__in = uas)

        topings_to_exclude = [o.topping for o in already_chosen_topings]

        available_topings = Topping.objects.exclude(topping__in=topings_to_exclude)
        return already_chosen_topings, available_topings

    def vote_until(self):
        voting_parameters = VotingParameters.objects.all()
        assert len(voting_parameters) == 1, "More than one voting parameters settings found."
        voting_delta = voting_parameters[0].vote_disable_before
        return self.date - voting_delta

    def voting_enabled(self):
        vote_until_val = self.vote_until()
        return  (timezone.now() <= vote_until_val and self.is_active())

    def is_in_future(self):
        return self.date  > timezone.now()

    # if in future and not in draft: Active
    def is_active(self):
        return self.is_in_future() and not self.isdraft and not self.isdeactivated

    # Flow of status:
    # Creation --> DRAFT
    # Activate by Button --> ACTIVE (Emails sent out)
    # Date of movienight passed --> PAST
    # Deactivated by button > DEAC
    def get_status(self):
        if self.isdraft:
            return "DRAFT"
        elif self.is_active():
            return "ACTIVE"
        elif self.isdeactivated:
            return "DEAC"
        elif  not self.is_in_future():
            return "PAST"

    def user_has_registered(self, user):
        ua = self.userattendence_set.filter(user=user)
        if len(ua) == 0:
            return False
        else:
            return ua[0].registration_complete

    def get_user_info(self, user):
        # get list of VotePreference and MovienightTopping associated to user and movienight
        if self.user_has_registered(user):
            ua = self.userattendence_set.filter(user=user)[0]
            votes = ua.get_votes()
            toppings = [u.topping for u in ua.get_toppings()]
            return votes, toppings
        else:
            return None, None

    def user_has_voted(self, user):
        # we allow for registered users to not have voted if they register too late
        if self.user_has_registered(user):
            votes, _ = self.get_user_info(user)
            if len(votes) == 0:
                return False
            else:
                return True
        else:
            return False

    def get_user_topping_list(self, user, badgestatus=None):
        _, toppings = self.get_user_info(user)
        if not badgestatus == None:
            return ' '.join([badgify(str(Topping.topping), badgestatus) for Topping in toppings])
        else:
            return ', '.join([str(Topping.topping) for Topping in toppings])

    def get_num_registered(self):
        uas = UserAttendence.objects.filter(movienight=self, registration_complete=True)
        return len(uas)

    def get_registered_userattend(self):
        uas = UserAttendence.objects.filter(movienight=self, registration_complete=True)
        return uas


    def get_num_voted(self):
        # return number of registered users and number of users who have voted
        uas = self.get_registered_userattend()

        num_voted_count = 0
        for us in uas:
            ua_user = us.user
            has_voted = self.user_has_voted(ua_user)
            if has_voted:
                num_voted_count += 1
        return num_voted_count



    # counts votes and returns current schulze winner
    def get_winning_movie(self):

        user_attendences = self.get_registered_userattend()
        pref_orderings = get_pref_lists(user_attendences)
        input_dict = prepare_voting_dict(pref_orderings)

        vote_result = SchulzeMethod(input_dict, ballot_notation = CondorcetHelper.BALLOT_NOTATION_GROUPING).as_dict()

        # check for tied winners
        try:
            # take tied movies if exist
            winner_movies_ids = vote_result["tied_winners"]
            tied_winners = True
        except:
            winner_movies_id = vote_result["winner"]
            tied_winners = False

        if tied_winners:
             # we now randomly select one of the tied winners by using a hashed random numbre

            # convert set to list
            winner_movies_ids = list(winner_movies_ids)

            # order list in order to remove ambiguity in set to list conversion
            winner_movies_ids.sort()

            num_ties = len(winner_movies_ids)

            # seeding random with the movienight id ensures randomness between movienights and
            # consistent winner for a single movienight
            random.seed(a=self.id, version=2)
            winning_index = random.randint(0,num_ties-1)
            winner_movies_id = winner_movies_ids[winning_index]

        winning_movie = Movie.objects.get(pk=winner_movies_id)


        runtime = winning_movie.get_runtime_int()
        return winning_movie, vote_result, runtime


    def rounddate(self, dt, roundto):
        # Need to round dates to 15 mins for Mailchimp

        new_minutes = roundto*(dt.minute // roundto)
        new_seconds = 0
        new_microsecond = 0

        newdate = dt.replace(minute=new_minutes, second=new_seconds, microsecond=new_microsecond)
        return newdate

    def get_reminder_date(self):
        voting_parameters = VotingParameters.objects.all()
        assert len(voting_parameters) == 1, "More than one voting parameters settings found."
        reminder_email_before = voting_parameters[0].reminder_email_before
        date  =  self.date - reminder_email_before
        date_rounded = self.rounddate(date, 15)
        return date_rounded

    def get_activation_date(self):
        voting_parameters = VotingParameters.objects.all()
        assert len(voting_parameters) == 1, "More than one voting parameters settings found."
        initial_email_after = voting_parameters[0].initial_email_after
        date  =  timezone.now() + initial_email_after
        date_rounded = self.rounddate(date, 15)
        return date_rounded

    def get_pretty_date(self, date):
        now = timezone.now()
        timedelta = date - now
                # localize to boston TZ
        boston_tz = pytz.timezone("America/New_York")
        fmt = "%B %d, %Y, %I:%M %p %Z%z"
        date_boston_time = date.astimezone(boston_tz)

        return date_boston_time.strftime(fmt) + " ( in "  + str(timedelta) + ")"

    def get_pretty_mn_date(self):
        return self.get_pretty_date(self.date)

    def get_pretty_reminder_date(self):
        return self.get_pretty_date(self.get_reminder_date())

    def get_pretty_activation_date(self):
        return self.get_pretty_date(self.get_activation_date())

    def __str__(self):
        return self.motto

class UserAttendence(models.Model):
    movienight = models.ForeignKey(MovieNightEvent, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    registration_complete = models.BooleanField(default=False)

    def get_votes(self):
        return self.votepreference_set.all()

    def get_toppings(self):
        return self.movienighttopping_set.all()

    def has_voted(self):
        if len(self.get_votes()) > 0:
            return True
        else:
            return False

class VotePreference(models.Model):
    user_attendence = models.ForeignKey(UserAttendence, on_delete=models.CASCADE, blank=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    preference  = models.IntegerField(blank=True) #0 to 5

    def __str__(self):
        return self.movie.title + ": " + str(self.preference)

class Topping(models.Model):
    topping = models.CharField(max_length=300)

    def __str__(self):
        return self.topping

class MovienightTopping(models.Model):
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE)
    user_attendence = models.ForeignKey(UserAttendence, on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return  self.topping.topping





