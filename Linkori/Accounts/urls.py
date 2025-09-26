from django.urls import path
from . import views

urlpatterns = [
    path('osu/login/', views.osu_login_view, name='osu_login'),
    path('osu/callback/', views.osu_callback_view, name='osu_callback'),
    path('discord/login/', views.discord_login_view, name='discord_login'),
    path('discord/callback/', views.discord_callback_view, name='discord_callback'),
    path('user/', views.user_view, name='user'),
    path('regions/', views.get_regions, name='regions'),
    path('cities/', views.get_cities, name='cities_by_regions'),
]