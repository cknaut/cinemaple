from .models import MovieNightEvent, Movie
from rest_framework import serializers
from django.utils import timezone
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



    def get_movies(self, MovieNight):
        return ', '.join([str(movie.title) for movie in MovieNight.MovieList.all()])

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
            return date_boston_time.strftime(fmt)  + " (" + strfdelta(timedelta, "In {days}d, {hours}hrs, {minutes}min") + ")"
        else:
            timedelta =  now - date
            return date_boston_time.strftime(fmt) + " (" +  strfdelta(timedelta, "{days}d, {hours}hrs, {minutes}min ago") + ")"




    class Meta:
        model = MovieNightEvent
        fields = (
            'id', 'motto', 'date', "movies", "isactive", "movies", "date_delta"
        )


