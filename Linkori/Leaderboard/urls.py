from django.urls import path
from . import views

urlpatterns = [
    path("mainboard/", views.get_mainboard, name="mainboard"),
    path("leaderboard/", views.get_leaderboard, name="leaderboard"),
    path("user-servers/", views.get_user_servers, name="user-servers"),
    path("cities/", views.get_cities, name="cities")
]