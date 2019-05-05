from django.urls import path
from django.contrib.auth import views as auth_views


from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:imdb_id>/add/', views.add_movie_fromIMDB, name='add_movie_fromIMDB'),
    path('activate/<str:key>', views.activation,  name='activation'),
    path('registration/', views.registration,  name='registration'),
    path('login/', views.my_login,  name='login'),
    path('logout/', auth_views.LogoutView.as_view(),  name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(),  name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(),  name='password_reset_done'),
]
