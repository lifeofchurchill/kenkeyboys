from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
# Named static_url so it doesn't clash with the "static" helper above
from django.templatetags.static import static as static_url
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Browsers and Google ask for /favicon.ico directly; point them at the real icon.
    # permanent=True: tells them it lives there for good, so they remember it
    path(
        "favicon.ico",
        RedirectView.as_view(url=static_url("website/img/icons/favicon.ico"), permanent=True),
    ),
    path("api/", include("club.urls")),
    path("api/", include("matches.urls")),
    path("", include("website.urls")),
]

# On the laptop (debug on), Django serves uploaded photos itself.
# On the live site, PythonAnywhere's web server does it instead
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)