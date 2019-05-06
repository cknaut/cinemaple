from django.urls import path
from django.contrib.auth import views as auth_views


from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:imdb_id>/add/', views.add_movie_fromIMDB, name='add_movie_fromIMDB'),
    path('activate/<str:key>', views.activation,  name='activation'),
    path('reset/<str:reset_key>', views.password_reset,  name='password_reset'),
    path('registration/', views.registration,  name='registration'),
    path('login/', views.my_login,  name='login'),
    path('logout/', auth_views.LogoutView.as_view(),  name='logout'),
    path('password_reset_request/', views.password_reset_request,  name='password_reset_request'),
    path('password_reset_request_done/',  views.password_reset_request_done,  name='password_reset_request_done'),
]
