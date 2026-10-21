from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from .views import SpaView, service_worker

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.invaders.urls")),
    path("sw.js", service_worker, name="service-worker"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Every other path is a Vue Router route: serve the app page (keep this last).
urlpatterns += [re_path(r"^(?!api/|admin/|static/|media/).*$", SpaView.as_view(), name="spa")]
