from django.urls import path, re_path
from django.contrib.auth import views as auth_views


from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('activate/<str:key>', views.activation,  name='activation'),
    path('reset/<str:reset_key>', views.password_reset,  name='password_reset'),
    path('registration/', views.registration,  name='registration'),
    path('login/', views.my_login,  name='login'),
    path('logout/', auth_views.LogoutView.as_view(),  name='logout'),
    path('password_reset_request/', views.password_reset_request,  name='password_reset_request'),
    path('password_reset_request_done/',  views.password_reset_request_done,  name='password_reset_request_done'),
    path('tmdb/<str:query>',  views.tmdb_api_wrapper_search,  name='tmdb_api_wrapper_search_queryonly'),
    path('tmdb/<str:query>',  views.tmdb_api_wrapper_search,  name='tmdb_api_wrapper_search_queryonly'),
    path('imdb_tmdb/movie/<int:tmdb_id>',  views.imdb_tmdb_api_wrapper_movie,  name='tmdb_api_wrapper_movie'),
    path('add_movie_night',  views.add_movie_night,  name='add_movie_night'),
    path('search_movie',  views.search_movie,  name='search_movie'),
    path('welcome',  views.welcome,  name='welcome')
]
