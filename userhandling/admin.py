from django.contrib import admin

from .models import MovieNightEvent, Movie

# Register your models here.
admin.site.register(MovieNightEvent)
admin.site.register(Movie)
