from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from apps.invaders.views import map_tile

from .ratelimit import limit_posts_by_ip
from .views import SpaView, service_worker, web_manifest

urlpatterns = [
    # Before admin.site.urls: brute-force protection for the admin login form.
    path(
        "admin/login/",
        limit_posts_by_ip(settings.ADMIN_LOGIN_ATTEMPTS_PER_MINUTE, 60, "admin-login")(admin.site.login),
    ),
    path("admin/", admin.site.urls),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.invaders.urls")),
    path("sw.js", service_worker, name="service-worker"),
    path("manifest.webmanifest", web_manifest, name="web-manifest"),
    path("tiles/<int:z>/<int:x>/<int:y>.png", map_tile, name="map-tile"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Every other path is a Vue Router route: serve the app page (keep this last).
urlpatterns += [re_path(r"^(?!api/|admin/|static/|media/|tiles/).*$", SpaView.as_view(), name="spa")]
