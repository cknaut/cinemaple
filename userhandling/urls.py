from django.urls import path, re_path, include
from django.contrib.auth import views as auth_views
from rest_framework import routers


from . import views
router = routers.DefaultRouter()
router.register(r'movienights', views.MovieNightEventViewSet)

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
    path('curr_mov_nights',  views.curr_mov_nights,  name='curr_mov_nights'),
    path('man_mov_nights',  views.man_mov_nights,  name='man_mov_nights'),
    path('dashboard',  views.dashboard,  name='dashboard'),
    path('mov_night/<str:movienight_id>', views.details_mov_nights,  name='details_mov_nights'),
    path('delete_mov_night/<str:movienight_id>', views.delete_mov_night,  name='delete_mov_night'),
    path('activate_movie_night/<str:movienight_id>', views.activate_movie_night,  name='activate_movie_night'),
    re_path('^api/', include(router.urls)),
]
