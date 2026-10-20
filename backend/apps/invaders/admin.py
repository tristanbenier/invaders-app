from django.contrib import admin

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
