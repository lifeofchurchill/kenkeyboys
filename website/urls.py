from django.urls import path

from . import views

app_name = "website"

urlpatterns = [
    path("", views.home, name="home"),
    path("matches/", views.matches, name="matches"),
    path("matches/<int:pk>/", views.match_detail, name="match_detail"),
    path("squad/", views.squad, name="players"),
    path("news/", views.news, name="news"),
    path("news/<int:pk>/", views.news_detail, name="news_detail"),
    path("honours/", views.honours, name="honours"),
    path("about/", views.about, name="about"),
    path("join/", views.join, name="join"),
]