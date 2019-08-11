from .models import MovieNightEvent, Movie, UserAttendence
from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth.models import User
from .utils import badgify


import pytz


def strfdelta(tdelta, fmt):
    d = {"days": abs(tdelta.days)}
    d["hours"], rem = divmod(tdelta.seconds, 3600)
    d["minutes"], d["seconds"] = divmod(rem, 60)
    return fmt.format(**d)


class MovieNightEventSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    date = serializers.DateTimeField(format="%B %d, %Y, %I:%M %p")
    date_delta = serializers.SerializerMethodField()
    movies = serializers.SerializerMethodField()
    vote_enabled = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    reg_users = serializers.SerializerMethodField()

    def get_reg_users(self, MovieNight):
        return MovieNight.get_num_registered()

    def get_movies(self, MovieNight):
        return ', '.join([str(movie.title) for movie in MovieNight.MovieList.all()])

    def get_status(self, MovieNight):
        return MovieNight.get_status()

    def get_vote_enabled(self, MovieNight):
        return MovieNight.voting_enabled()

    def get_date_delta(self, MovieNight):
        date = MovieNight.date
        now = timezone.now()
        timedelta = date - now
        timedelta_secs = int(timedelta.total_seconds())

        # localize to boston TZ
        boston_tz = pytz.timezone("America/New_York")
        fmt = "%B %d, %Y, %I:%M %p %Z%z"
        date_boston_time = date.astimezone(boston_tz)

        if timedelta_secs > 0:
            return date_boston_time.strftime(fmt) + " (" + strfdelta(timedelta, "In {days}d, {hours}hrs, {minutes}min") + ")"
        else:
            timedelta = now - date
            return date_boston_time.strftime(fmt) + " (" + strfdelta(timedelta, "{days}d, {hours}hrs, {minutes}min ago") + ")"

    class Meta:
        model = MovieNightEvent
        fields = (
            'id', 'motto', 'date', "movies", "isdraft", "movies", "date_delta", "vote_enabled", "status", "reg_users"
        )


class UserAttendenceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user = serializers.SerializerMethodField()
    toppings = serializers.SerializerMethodField()
    reg_date = serializers.SerializerMethodField()
    firstlastname = serializers.SerializerMethodField()

    def get_firstlastname(self, UserAttendence):
        return UserAttendence.user.first_name + " " + UserAttendence.user.last_name

    def get_reg_date(self, UserAttendence):
        date = UserAttendence.registered_at
        boston_tz = pytz.timezone("America/New_York")
        fmt = "%B %d, %Y, %I:%M %p %Z%z"
        date_boston_time = date.astimezone(boston_tz).strftime(fmt)
        return date_boston_time

    def get_user(self, UserAttendence):
        return UserAttendence.user.username

    def get_toppings(self, UserAttendence):
        return ' '.join([badgify(o.topping.topping, 'primary') for o in UserAttendence.get_toppings()])

    class Meta:
        model = UserAttendence
        fields = (
            'id', 'user', 'toppings', 'reg_date', "registration_complete", "movienight", 'firstlastname'
        )
