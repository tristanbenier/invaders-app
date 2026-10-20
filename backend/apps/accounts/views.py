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

from .models import Invitation, User
from .permissions import IsTeamAdmin
from .serializers import (
    AcceptInvitationSerializer,
    InvitationSerializer,
    LoginSerializer,
    MeSerializer,
    PublicInvitationSerializer,
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
