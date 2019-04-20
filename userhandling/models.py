from django.db import models



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

