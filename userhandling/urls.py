from django.urls import path, re_path, include
from django.contrib.auth import views as auth_views
from rest_framework import routers


from . import views
router = routers.DefaultRouter()
router.register(r'movienights', views.MovieNightEventViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('activate/<str:key>', views.activation,  name='activation'),
    path('activate/update_email/<str:key>', views.activate_emailupdate,  name='activate_emailupdate'),
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
    path('past_mov_nights',  views.past_mov_nights,  name='past_mov_nights'),
    path('dashboard',  views.dashboard,  name='dashboard'),
    path('mov_night/<str:movienight_id>', views.details_mov_nights,  name='details_mov_nights'),
    path('delete_mov_night/<str:movienight_id>', views.delete_mov_night,  name='delete_mov_night'),
    path('activate_movie_night/<str:movienight_id>', views.activate_movie_night,  name='activate_movie_night'),
    path('deactivate_movie_night/<str:movienight_id>', views.deactivate_movie_night,  name='deactivate_movie_night'),
    path('change_movie_night/<str:movienight_id>', views.change_movie_night,  name='change_movie_night'),
    path('reg_movie_night/<str:movienight_id>', views.reg_movie_night,  name='reg_movie_night'),
    path('ureg_movie_night/<str:movienight_id>', views.ureg_movie_night,  name='ureg_movie_night'),
    re_path('^api/', include(router.urls)),
    path('topping_add_movie_night/<str:movienight_id>', views.topping_add_movie_night,  name='topping_add_movie_night'),
    path('attendence_list/<str:movienight_id>', views.attendence_list,  name='attendence_list'),
    path('api/attendence_list/<str:movienight_id>', views.UserAttendenceList.as_view()),
    path('count_votes/<str:movienight_id>', views.count_votes,  name='count_votes'),
    path('user_prefs/', views.user_prefs,  name='user_prefs'),
    path('change_password/', views.change_password,  name='change_password'),
    path('change_profile/', views.change_profile,  name='change_profile'),
    path('trigger_emails/<str:movienight_id>', views.trigger_emails,  name='trigger_emails'),
    path('ml_health/', views.ml_health,  name='ml_health'),
    path('preview_mn_email/<str:movienight_id>', views.preview_mn_email,  name='preview_mn_email'),
    path('schedule_email/<str:movienight_id>', views.schedule_email,  name='schedule_email'),






    #path('vote_movie_night/<str:movienight_id>', views.vote_movie_night,  name='vote_movie_night'),

]
