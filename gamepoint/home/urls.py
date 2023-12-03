from django.contrib import admin
from django.urls import path, include
from home import views
from django.urls import path, include
# , TeamViewSet, GameViewSet, ScoreViewSet

urlpatterns = [
    path('', views.home, name="home"),
    path('livematchs', views.livematchs, name="livematchs"),
    path('oldmatchs', views.oldmatchs, name="oldmatchs"),
]