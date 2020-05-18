import random
# from .utils import badgify
# from urllib.request import urlopen
# from PIL import Image

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from py3votecore.condorcet import CondorcetHelper
from py3votecore.schulze_method import SchulzeMethod
import pytz

from .vote import get_pref_lists, prepare_voting_dict

# import scipy.ndimage.gaussian_filter


# Wrap Bootrap Badge HTML around string
def badgify(string, badge_type):
    badge_html = "<span class='badge badge-" + \
        badge_type + "'>" + string + "</span>"
    return badge_html


class Location(models.Model):
    name = models.CharField(max_length=200)
    street = models.CharField(max_length=200)
    zip_code = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    country = models.CharField(max_length=200)

    def print_address(self):
        return '{}, {} {}, {}'.format(self.street, self.zip_code,
                                      self.city, self.state)

    def __str__(self):              # __unicode__ on Python 2
        return self.name


class LocationPermission(models.Model):
    ROLE_CHOICES = [
        ('HO', 'Host'),
        ('AM', 'Ambassador'),
        ('GU', 'Guest'),
    ]

    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    revoked_access = models.BooleanField(default=False)
    rev_access_hash = models.CharField(max_length=40, blank=True)

    # ALl users get an activation code, so you'll have to manually \
    # check if user can invite using get_invite_code
    # NEVER DIRECTLY RETRIEVE THIS ALWAYS USE get_invite_code()
    invitation_code = models.UUIDField(null=True, editable=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='locperms')
    inviter = models.ForeignKey(User, null=True, blank=True,
                                on_delete=models.SET_NULL,
                                related_name='invitor')

    role = models.CharField(
        max_length=2,
        choices=ROLE_CHOICES,
        default='GU',
    )

    def is_active(self):
        return self.user.is_active

    def get_invitation_link(self):
        return "https://www.cinemaple.com/registration/" + \
            str(self.invitation_code)

    def get_invite_code(self):
        if self.can_invite():
            return self.invitation_code
        else:
            return ""

    def can_invite(self):
        # Hosts and Amb. can invite
        return self.role in ('HO', 'AM')

    def is_host(self):
        return self.role in 'HO'

    def __str__(self):              # __unicode__ on Python 2
        return "{} / {} / {}".format(self.user.username,
                                     self.location, self.role)


# We create a one-to-one map from the built-in User model to a Profile model
# From \
# https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    email_buffer = models.EmailField(default='')  # contains unverified email
    birth_date = models.DateField(null=True, blank=True)
    activation_key = models.CharField(max_length=40, blank=True)
    key_expires = models.DateTimeField(null=True, blank=True)

    def get_location_permissions(self):
        return self.user.locperms.all()

    def has_revoked(self, location):
        locperms = self.get_location_permissions()
        locperms_location = locperms.filter(location__in=location)
        has_revoked = False
        for locperm in locperms_location:
            if locperm.revoked_access:
                has_revoked = True
                return has_revoked

        return has_revoked

    # returns true if at least one locperm has revoked access
    def has_at_least_one_revk(self):
        locperms = self.get_location_permissions()
        has_revoked = False
        for locperm in locperms:
            if locperm.revoked_access:
                has_revoked = True
                return has_revoked

        return has_revoked

    # given a host, return all user permissions of \
    # user for which host is host
    def get_loc_perms_of_host(self, hostuser):
        assert hostuser.profile.is_host(), "User must be host"

        host_locs = hostuser.profile.get_hosted_locations()
        self_locperms = self.get_location_permissions()

        return self_locperms.filter(location__in=host_locs)

    # Return Location Permissions of locations where user is host
    def get_hosting_location_perms(self):
        loc_permissions = self.user.locperms.filter(role='HO')
        return loc_permissions

    # Return Location Permissions of locations where user can invite
    def get_invitable_location_perms(self):
        loc_permissions = self.user.locperms.filter(role__in=['HO', 'AM'])
        return loc_permissions

    # Returns list of locations for which user has Host status
    def get_hosted_locations(self):
        return [i.location for i in self.get_hosting_location_perms()]

    # Returns list of locations for which user has any location permission
    def get_all_locations(self):
        return [i.location for i in self.get_location_permissions()]

    # get location permissions for locations for which user is host
    def get_managed_loc_perms(self):
        return LocationPermission.objects.filter(
            location__in=self.get_hosted_locations())

    # Get set of all users which are associated to a location \
    # for which user is host
    def get_managed_users(self):
        man_users = [i.user for i in self.get_managed_loc_perms()]
        return man_users

    # Return locationPermissions of users which have been \
    # invited by this profile's user
    def get_intivees_locperms(self):
        invitees = LocationPermission.objects.filter(inviter=self.user)
        return invitees

    # True if host for at least one locations, will be used \
    # to unlock all hidden urls
    def is_host(self):
        if self.get_hosting_location_perms():
            return True
        else:
            return False

    # True if can invite for at least one locations, will \
    # be used to unlock all hidden urls
    def is_inviter(self):
        if self.get_invitable_location_perms():
            return True
        else:
            return False

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(
    sender, instance, created, **kwargs
):  # pylint: disable=unused-argument
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(
    sender, instance, **kwargs
):  # pylint: disable=unused-argument
    instance.profile.save()


class PasswordReset(models.Model):
    username = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reset_key = models.CharField(max_length=40, blank=True)
    reset_used = models.BooleanField(default=False)

    def __str__(self):              # __unicode__ on Python 2
        return self.username


class Movie(models.Model):
    tmdbid = models.CharField(max_length=200)
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
        try:
            runtime_int = int(runtime)
        except ValueError:
            runtime_int = 90
        return runtime_int

    def __str__(self):
        return self.title

    # def filtered_poster(self):
        # print("Running filter function")
        # return Image.open(urlopen(
        # "https://image.tmdb.org/t/p/w200"+self.posterpath))


class VotingParameters(models.Model):
    # how long before the movienight the vote should e closed
    vote_disable_before = models.DurationField()
    # how long before the movienight the final reminder email sould be sent
    reminder_email_before = models.DurationField()
    # how long after activation of movienight should emails be send out?
    initial_email_after = models.DurationField()

    def __str__(self):
        return "Only instance of this model."


class QuickPoll(models.Model):
    motto = models.CharField(max_length=200)
    description = models.TextField(max_length=10000)
    MovieList = models.ManyToManyField(Movie, blank=True)

    # Date added.
    add_date = models.DateField(auto_now_add=True)

    # Duration active.
    duration = models.DurationField()

    # Used for URL dispatching.
    ref_code = models.UUIDField(null=False, editable=False)



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
        already_chosen_topings = MovienightTopping.objects.filter(
            user_attendence__in=uas)
        topings_to_exclude = [o.topping for o in already_chosen_topings]
        available_topings = Topping.objects.exclude(
            topping__in=topings_to_exclude)
        return already_chosen_topings, available_topings

    def vote_until(self):
        voting_parameters = VotingParameters.objects.all()
        assert len(voting_parameters) == 1, "More than one voting \
            parameters settings found."
        voting_delta = voting_parameters[0].vote_disable_before
        return self.date - voting_delta

    def voting_enabled(self):
        vote_until_val = self.vote_until()
        return timezone.now() <= vote_until_val and self.is_active()

    def is_in_future(self):
        return self.date > timezone.now()

    # if in future and not in draft: Active
    def is_active(self):
        return self.is_in_future() and not self.isdraft \
            and not self.isdeactivated

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
        elif not self.is_in_future():
            return "PAST"

    def user_has_registered(self, user):
        user_attendence = self.userattendence_set.filter(user=user)
        if not user_attendence:
            return False
        else:
            return user_attendence[0].registration_complete

    def get_user_info(self, user):
        # get list of VotePreference and MovienightTopping \
        # associated to user and movienight
        if self.user_has_registered(user):
            user_attendence = self.userattendence_set.filter(user=user)[0]
            votes = user_attendence.get_votes()
            toppings = [u.topping for u in user_attendence.get_toppings()]
            return votes, toppings
        else:
            return None, None

    def user_has_voted(self, user):
        # we allow for registered users to not have voted \
        # if they register too late
        if self.user_has_registered(user):
            votes, _ = self.get_user_info(user)
            if not votes:
                return False
            else:
                return True
        else:
            return False

    def get_user_topping_list(self, user, badgestatus=None):
        _, toppings = self.get_user_info(user)
        if badgestatus is not None:
            return ' '.join([badgify(str(topping.topping), badgestatus)
                             for topping in toppings])
        else:
            return ', '.join([str(topping.topping) for topping in toppings])

    def get_num_registered(self):
        uas = UserAttendence.objects.filter(movienight=self,
                                            registration_complete=True)
        return len(uas)

    def get_registered_userattend(self):
        uas = UserAttendence.objects.filter(movienight=self,
                                            registration_complete=True)
        return uas

    def get_num_voted(self):
        # return number of registered users and number of users who have voted
        uas = self.get_registered_userattend()

        num_voted_count = 0
        for user_attendence in uas:
            ua_user = user_attendence.user
            has_voted = self.user_has_voted(ua_user)
            if has_voted:
                num_voted_count += 1
        return num_voted_count

    # counts votes and returns current schulze winner
    def get_winning_movie(self):

        user_attendences = self.get_registered_userattend()

        # Avoid rekursion error
        if not user_attendences:
            winning_movie = None
            vote_result = None
            runtime = 0
        else:
            pref_orderings = get_pref_lists(user_attendences)
            input_dict = prepare_voting_dict(pref_orderings)

            vote_result = SchulzeMethod(input_dict,
                                        ballot_notation=CondorcetHelper.
                                        BALLOT_NOTATION_GROUPING).as_dict()

            # check for tied winners
            try:
                # take tied movies if exist
                winner_movies_ids = vote_result["tied_winners"]
                tied_winners = True
            except KeyError:
                winner_movies_id = vote_result["winner"]
                tied_winners = False

            if tied_winners:
                # we now randomly select one of the tied winners \
                # by using a hashed random number

                # convert set to list
                winner_movies_ids = list(winner_movies_ids)

                # order list in order to remove \
                #  ambiguity in set to list conversion
                winner_movies_ids.sort()

                num_ties = len(winner_movies_ids)

                # seeding random with the movienight id ensures randomness \
                # between movienights and \
                # consistent winner for a single movienight
                random.seed(a=self.id, version=2)
                winning_index = random.randint(0, num_ties - 1)
                winner_movies_id = winner_movies_ids[winning_index]

            winning_movie = Movie.objects.get(pk=winner_movies_id)

            runtime = winning_movie.get_runtime_int()

        return winning_movie, vote_result, runtime

    def rounddate(self, delta_t, roundto):
        # Need to round dates to 15 mins for Mailchimp

        new_minutes = roundto * (delta_t.minute // roundto)
        new_seconds = 0
        new_microsecond = 0

        newdate = delta_t.replace(minute=new_minutes, second=new_seconds,
                                  microsecond=new_microsecond)
        return newdate

    def get_reminder_date(self):
        voting_parameters = VotingParameters.objects.all()
        assert len(voting_parameters) == 1, \
            "More than one voting parameters settings found."
        reminder_email_before = voting_parameters[0].reminder_email_before
        date = self.date - reminder_email_before
        date_rounded = self.rounddate(date, 15)
        return date_rounded

    def get_activation_date(self):
        voting_parameters = VotingParameters.objects.all()
        assert len(voting_parameters) == 1, \
            "More than one voting parameters settings found."
        initial_email_after = voting_parameters[0].initial_email_after
        date = timezone.now() + initial_email_after
        date_rounded = self.rounddate(date, 15)
        return date_rounded

    def get_pretty_date(self, date):
        now = timezone.now()
        timedelta = date - now
        # localize to boston TZ
        boston_tz = pytz.timezone("America/New_York")
        fmt = "%B %d, %Y, %I:%M %p %Z%z"
        date_boston_time = date.astimezone(boston_tz)

        return date_boston_time.strftime(fmt) + \
            " ( in " + str(timedelta) + ")"

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
        if self.get_votes():
            return True
        else:
            return False


class VotePreference(models.Model):
    user_attendence = models.ForeignKey(UserAttendence,
                                        on_delete=models.CASCADE,
                                        blank=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    preference = models.IntegerField(blank=True)  # 0 to 5

    def __str__(self):
        return self.movie.title + ": " + str(self.preference)


class Topping(models.Model):
    topping = models.CharField(max_length=300)

    def __str__(self):
        return self.topping


class MovienightTopping(models.Model):
    topping = models.ForeignKey(Topping, on_delete=models.CASCADE)
    user_attendence = models.ForeignKey(UserAttendence,
                                        on_delete=models.CASCADE,
                                        blank=True)

    def __str__(self):
        return self.topping.topping
