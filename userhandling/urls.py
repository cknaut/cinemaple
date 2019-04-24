from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:imdb_id>/add/', views.add_movie_fromIMDB, name='add_movie_fromIMDB'),
    path('activate/<str:key>', views.activation,  name='activation'),
]
