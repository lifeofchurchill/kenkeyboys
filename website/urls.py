from django.urls import path

from . import views

# The namespace that lets templates write {% url 'website:home' %}
app_name = "website"

urlpatterns = [
    path("", views.home, name="home"),
    path("matches/", views.matches, name="matches"),
    # <int:pk> captures a whole number from the address and passes it to the view as pk
    path("matches/<int:pk>/", views.match_detail, name="match_detail"),
    path("squad/", views.squad, name="players"),
    path("news/", views.news, name="news"),
    path("news/<int:pk>/", views.news_detail, name="news_detail"),
    path("honours/", views.honours, name="honours"),
    path("about/", views.about, name="about"),
    path("join/", views.join, name="join"),
]