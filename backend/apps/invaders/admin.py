from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.urls import path

from .admin_imports import import_invaders_view, upload_photos_view

from .models import City, Country, Flash, Invader, InvaderHistory


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["name", "team"]
    list_filter = ["team"]
    search_fields = ["name"]


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["name", "prefix", "country", "team"]
    list_filter = ["team", "country"]
    search_fields = ["name", "prefix"]


class InvaderHistoryInline(admin.TabularInline):
    model = InvaderHistory
    fields = ["created_at", "user", "action", "changes"]
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Invader)
class InvaderAdmin(admin.ModelAdmin):
    inlines = [InvaderHistoryInline]
    # Adds the "Importer des invaders" and "Envoyer des photos" buttons.
    change_list_template = "admin/invaders/invader/change_list.html"

    def get_urls(self):
        def screen(view):
            def wrapped(request):
                if not self.has_add_permission(request):
                    raise PermissionDenied
                return view(self, request)

            return self.admin_site.admin_view(wrapped)

        return [
            path("import/", screen(import_invaders_view), name="invaders_invader_import"),
            path("upload-photos/", screen(upload_photos_view), name="invaders_invader_upload_photos"),
            *super().get_urls(),
        ]
    list_display = ["name", "city", "points", "status", "team", "created_by", "created_at"]
    list_filter = ["team", "status", "city__country"]
    autocomplete_fields = ["city"]
    search_fields = ["name", "city__name", "address1", "zip"]


@admin.register(Flash)
class FlashAdmin(admin.ModelAdmin):
    list_display = ["invader", "user", "flashed_at"]
    list_filter = ["user__team"]
    search_fields = ["invader__name", "user__display_name"]
    autocomplete_fields = ["invader"]
