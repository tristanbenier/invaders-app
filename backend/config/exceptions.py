from django.http import Http404, JsonResponse
from rest_framework.exceptions import NotFound
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    # get_object_or_404 messages are English and expose model names.
    if isinstance(exc, Http404):
        exc = NotFound()
    return drf_exception_handler(exc, context)


def csrf_failure(request, reason=""):
    """JSON instead of Django's HTML page, so the SPA can show the message."""
    return JsonResponse(
        {"detail": "La vérification de sécurité a échoué. Rechargez la page et réessayez."}, status=403
    )
