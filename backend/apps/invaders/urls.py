from django.urls import path
from rest_framework.routers import SimpleRouter

from . import stats, views

router = SimpleRouter()
router.register("countries", views.CountryViewSet, basename="country")
router.register("cities", views.CityViewSet, basename="city")
router.register("invaders", views.InvaderViewSet, basename="invader")

urlpatterns = [
    path("flashes/", views.MyFlashListView.as_view(), name="my-flashes"),
    path("geocode/reverse/", views.ReverseGeocodeView.as_view(), name="geocode-reverse"),
    path("geocode/search/", views.AddressSearchView.as_view(), name="geocode-search"),
    path("iss/", views.IssPositionView.as_view(), name="iss-position"),
    path("stats/me/", stats.MyStatsView.as_view(), name="stats-me"),
    path("stats/team/", stats.TeamStatsView.as_view(), name="stats-team"),
    path("import/preview/", views.ImportView.as_view(commit=False), name="import-preview"),
    path("import/commit/", views.ImportView.as_view(commit=True), name="import-commit"),
    *router.urls,
]
