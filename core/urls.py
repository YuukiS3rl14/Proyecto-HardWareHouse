from django.urls import path
from .views import *

urlpatterns = [
    path('', mostrarIndex, name='index'),
]