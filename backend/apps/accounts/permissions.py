from rest_framework.permissions import BasePermission


class IsTeamMember(BasePermission):
    """Default permission: an authenticated user who belongs to a team."""

    message = "Vous devez appartenir à une équipe."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.team_id is not None)


class IsTeamAdmin(IsTeamMember):
    message = "Action réservée aux administrateurs de l'équipe."

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_team_admin
