from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Invitation, PasswordReset, User
from .permissions import IsTeamAdmin
from .serializers import (
    AcceptInvitationSerializer,
    InvitationSerializer,
    LoginSerializer,
    MeSerializer,
    PublicInvitationSerializer,
    ResetPasswordSerializer,
    TeamDetailSerializer,
)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    """Sets the CSRF cookie so the SPA can send it back in X-CSRFToken."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if user.team_id is None:
            raise PermissionDenied("Ce compte n'appartient à aucune équipe.")
        login(request, user)
        return Response(MeSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user


class FlashInvadersUidView(APIView):
    """The member's own Flash Invaders UID, shown on demand in the settings (never in /auth/me/)."""

    throttle_scope = "auth"

    def get(self, request):
        response = Response({"uid": request.user.flash_invaders_uid})
        # A secret: keep it out of every cache.
        response["Cache-Control"] = "no-store"
        return response


class PublicInvitationView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"
    serializer_class = PublicInvitationSerializer

    def get_object(self):
        invitation = get_object_or_404(
            Invitation.objects.select_related("team", "invited_by"), token=self.kwargs["token"]
        )
        if not invitation.is_pending:
            raise ValidationError("Cette invitation est invalide ou a expiré.")
        return invitation


@method_decorator(csrf_protect, name="dispatch")
class AcceptInvitationView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        if request.user.is_authenticated:
            raise PermissionDenied("Vous êtes déjà connecté.")
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response(MeSerializer(user).data, status=status.HTTP_201_CREATED)


class TeamView(generics.RetrieveAPIView):
    serializer_class = TeamDetailSerializer

    def get_object(self):
        return self.request.user.team


class TeamMemberRemoveView(APIView):
    permission_classes = [IsTeamAdmin]

    def delete(self, request, pk):
        member = get_object_or_404(User, pk=pk, team=request.user.team, is_active=True)
        if member == request.user:
            raise ValidationError("Vous ne pouvez pas vous retirer vous-même.")
        # Deactivate rather than delete so the member's history is kept.
        member.is_active = False
        member.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class InvitationListCreateView(generics.ListCreateAPIView):
    serializer_class = InvitationSerializer

    @property
    def throttle_scope(self):
        # Limit creating invitations, not listing them (the team page lists them on each visit).
        return "invitations" if self.request.method == "POST" else None

    def get_queryset(self):
        return Invitation.objects.pending().filter(team=self.request.user.team).select_related("invited_by")

    def perform_create(self, serializer):
        serializer.save(team=self.request.user.team, invited_by=self.request.user)


class InvitationRevokeView(APIView):
    def delete(self, request, pk):
        invitation = get_object_or_404(Invitation.objects.pending(), pk=pk, team=request.user.team)
        if not (request.user.is_team_admin or invitation.invited_by_id == request.user.id):
            raise PermissionDenied("Seuls l'auteur de l'invitation ou un administrateur peuvent la révoquer.")
        invitation.revoked_at = timezone.now()
        invitation.save(update_fields=["revoked_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetCreateView(APIView):
    """A team admin creates a single-use link for a member who forgot their password (no email sent)."""

    permission_classes = [IsTeamAdmin]
    throttle_scope = "password_reset"

    def post(self, request, pk):
        member = get_object_or_404(User, pk=pk, team=request.user.team, is_active=True)
        reset, token = PasswordReset.issue(member, created_by=request.user)
        # The clear token is only in this response: the database keeps its hash.
        return Response(
            {"url": PasswordReset.url_for(token), "expires_at": reset.expires_at},
            status=status.HTTP_201_CREATED,
            headers={"Cache-Control": "no-store"},
        )


@method_decorator(ensure_csrf_cookie, name="dispatch")
class PublicPasswordResetView(APIView):
    """Who the link is for, so the page can greet the member."""

    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def get(self, request, token):
        reset = PasswordReset.find(token)
        if reset is None or not reset.is_pending or not reset.user.is_active:
            raise ValidationError("Ce lien est invalide ou a expiré.")
        return Response({"display_name": reset.user.display_name, "email": reset.user.email})


@method_decorator(csrf_protect, name="dispatch")
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        # Like invitations: an admin testing the link must not switch accounts by accident.
        if request.user.is_authenticated:
            raise PermissionDenied("Vous êtes déjà connecté.")
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response(MeSerializer(user).data)
