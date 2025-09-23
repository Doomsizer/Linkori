from django.urls import path
from . import views

urlpatterns = [
    path('main/', views.get_mainboard, name='mainboard'),
]