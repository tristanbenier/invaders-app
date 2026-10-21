from django.conf import settings
from django.http import FileResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView


@method_decorator([ensure_csrf_cookie, never_cache], name="dispatch")
class SpaView(TemplateView):
    """HTML page that mounts the Vue app; Vue Router handles the path client-side."""

    template_name = "index.html"

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), "vite_dev_mode": settings.DJANGO_VITE["default"]["dev_mode"]}


@never_cache
def service_worker(request):
    """The service worker must be served from the root to control the whole site."""
    path = settings.FRONTEND_DIST_DIR / "sw.js"
    if not path.is_file():
        raise Http404
    return FileResponse(path.open("rb"), content_type="text/javascript")
