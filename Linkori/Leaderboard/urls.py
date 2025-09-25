from django.urls import path
from . import views

urlpatterns = [
    path("mainboard/", views.get_mainboard, name="mainboard"),
    path("leaderboard/", views.get_leaderboard, name="leaderboard")
]