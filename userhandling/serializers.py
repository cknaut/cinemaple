from .models import MovieNightEvent, Movie
from rest_framework import serializers



class MovieNightEventSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    date = serializers.DateTimeField(format="%B %d, %Y, %I:%M %p")


    movies = serializers.SerializerMethodField()



    def get_movies(self, MovieNight):
        return ', '.join([str(movie.title) for movie in MovieNight.MovieList.all()])


    class Meta:
        model = MovieNightEvent
        fields = (
            'id', 'motto', 'date', "movies", "isactive", "movies"
        )


