from django.urls import path


from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:imdb_id>/add/', views.add_movie_fromIMDB, name='add_movie_fromIMDB'),
    path('activate/<str:key>', views.activation,  name='activation'),
    path('registration/', views.registration,  name='registration'),
    path('login/', views.my_login,  name='login'),
    path('logout/', views.my_logout,  name='logout'),
]
