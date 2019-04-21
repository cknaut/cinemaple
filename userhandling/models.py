from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# We create a one-to-one map from the built-in User model to a Profile model
# From https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Movie(models.Model):
    imdbID = models.CharField(max_length=200)
    title = models.CharField(max_length=500)
    year = models.CharField(max_length=200)
    director = models.CharField(max_length=200)
    runtime = models.CharField(max_length=200)
    actors = models.CharField(max_length=2000)
    plot = models.TextField(max_length=2000)
    country = models.CharField(max_length=200)

    def __str__(self):
        return self.title


class MovieNightEvent(models.Model):
    motto = models.CharField(max_length=200)
    description = models.CharField(max_length=5000)
    date = models.DateTimeField('date published')
    MovieList = models.ManyToManyField(Movie, blank=True)

    def __str__(self):
        return self.motto

