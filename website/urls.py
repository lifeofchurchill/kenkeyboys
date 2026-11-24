from django.urls import path
from django.views.generic import TemplateView

from . import views

# The namespace that lets templates write {% url 'website:home' %}
app_name = "website"


def coming_soon(page, title):
    """A placeholder for a page we have not built yet."""
    return TemplateView.as_view(
        template_name="website/coming_soon.html",
        extra_context={"active_page": page, "page_title": title},
    )


urlpatterns = [
    path("", views.home, name="home"),
    path("squad/", views.squad, name="players"),
    # <int:pk> captures a whole number from the address and passes it to the view as pk
    path("news/<int:pk>/", views.news_detail, name="news_detail"),
    # Placeholders: each is swapped for a real view as we build that page
    path("matches/", coming_soon("matches", "Fixtures & results"), name="matches"),
    path("news/", coming_soon("news", "News"), name="news"),
    path("honours/", coming_soon("honours", "Trophy room"), name="honours"),
]