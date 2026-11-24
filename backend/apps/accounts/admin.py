from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Invitation, PasswordReset, Team, User


class MemberInline(admin.TabularInline):
    model = User
    fields = ["email", "display_name", "role", "is_active"]
    readonly_fields = ["email"]
    extra = 0
    can_delete = False
    show_change_link = True


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]
    inlines = [MemberInline]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "display_name", "team", "role", "is_active", "is_staff"]
    list_filter = ["team", "role", "is_active", "is_staff"]
    search_fields = ["email", "display_name"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        # flash_invaders_uid left out on purpose: it is a secret of the member.
        ("Profil", {"fields": ["display_name", "team", "role", "map_theme", "manual_flash"]}),
        ("Permissions", {"fields": ["is_active", "is_staff", "is_superuser", "groups", "user_permissions"]}),
        ("Dates", {"fields": ["last_login", "date_joined"]}),
    ]
    add_fieldsets = [
        (None, {"classes": ["wide"], "fields": ["email", "display_name", "team", "role", "password1", "password2"]}),
    ]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["team", "email", "role", "invited_by", "created_at", "expires_at", "used_at", "revoked_at"]
    list_filter = ["team", "role"]
    readonly_fields = ["token", "url", "used_at", "used_by"]


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ["user", "created_by", "created_at", "expires_at", "used_at", "revoked_at"]
    list_filter = ["user__team"]
    # The token is only known by the admin who created the link (hash stored).
    fields = ["user", "created_by", "created_at", "expires_at", "used_at", "revoked_at"]
    readonly_fields = fields

    def has_add_permission(self, request):
        return False
