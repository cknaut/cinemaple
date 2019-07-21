from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .utils import badgify
import time



# We create a one-to-one map from the built-in User model to a Profile model
# From https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    activation_key = models.CharField(max_length=40, blank=True)
    key_expires = models.DateTimeField(null=True, blank=True)
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

    def __str__(self):
        return self.title


class VotingParameters(models.Model):
    vote_disable_before = models.DurationField() # how long before the movienight the vote should e closed
    reminder_email_before = models.DurationField() # how long before the movienight the final reminder email sould be sent
    initial_email_before = models.DurationField() # how long before the movienight the first invitation_email

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
        return  (timezone.now()  <= vote_until_val and self.is_active())

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


    def get_user_topping_list(self, user, badgestatus=None):
        _, toppings = self.get_user_info(user)
        if not badgestatus == None:
            return ' '.join([badgify(str(Topping.topping), badgestatus) for Topping in toppings])
        else:
            return ', '.join([str(Topping.topping) for Topping in toppings])

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





