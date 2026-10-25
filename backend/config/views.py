import hashlib

from django.conf import settings
from django.http import FileResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView


_bundle_versions = {}


def bundle_version():
    """Short hash of the built bundles, appended to their URLs (?v=) so browsers fetch new ones.

    Recomputed only when a bundle file changes (keyed on modification times).
    """
    paths = [settings.FRONTEND_DIST_DIR / name for name in ("bundle.min.js", "bundle.min.css")]
    key = tuple(path.stat().st_mtime_ns if path.exists() else 0 for path in paths)
    if key not in _bundle_versions:
        digest = hashlib.sha256()
        for path in paths:
            if path.exists():
                digest.update(path.read_bytes())
        _bundle_versions.clear()
        _bundle_versions[key] = digest.hexdigest()[:12]
    return _bundle_versions[key]


@method_decorator([ensure_csrf_cookie, never_cache], name="dispatch")
class SpaView(TemplateView):
    """HTML page that mounts the Vue app; Vue Router handles the path client-side."""

    template_name = "index.html"

    def get_context_data(self, **kwargs):
        dev_mode = settings.DJANGO_VITE["default"]["dev_mode"]
        return {
            **super().get_context_data(**kwargs),
            "vite_dev_mode": dev_mode,
            "bundle_version": None if dev_mode else bundle_version(),
        }


@never_cache
def service_worker(request):
    """The service worker must be served from the root to control the whole site."""
    path = settings.FRONTEND_DIST_DIR / "sw.js"
    if not path.is_file():
        raise Http404
    return FileResponse(path.open("rb"), content_type="text/javascript")
