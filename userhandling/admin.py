from django.contrib import admin

from .models import MovieNightEvent, Movie, Profile

# Register your models here.
admin.site.register(MovieNightEvent)
admin.site.register(Movie)
admin.site.register(Profile)
