from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import urllib, json 
from .utils import Mailchimp

from .models import Movie, MovieNightEvent
# ...
 

# Render Index Page
def index(request):
    movienights = MovieNightEvent.objects.order_by('-date')[:5]
    return render(request, 'userhandling/index.html', {'movienights': movienights})

# Access movie info using IMDB and add model instance containing info
def add_movie_fromIMDB(request, imdb_id):
    args = {"apikey": settings.OMDB_API_KEY, "i": imdb_id, "plot" : "full"}
    url_api = " http://www.omdbapi.com/?{}".format(urllib.parse.urlencode(args))

    # Load Return Object Into JSON
    try:
        with urllib.request.urlopen(url_api) as url:
            data = json.loads(url.read().decode())
    except:
        raise Exception("{} is not valid IMDB ID")

    # Create movie instance from returned JSON
    m = Movie(imdbID=imdb_id)
    m.title = data["Title"]
    m.year = data["Year"]
    m.director = data["Director"]
    m.runtime = data["Runtime"]
    m.plot = data["Plot"]
    m.country = data["Country"]
    m.actors = data["Actors"]
    m.save()
 
    return render(request, 'userhandling/index.html')
    

