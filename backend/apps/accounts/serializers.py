import re

from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.invaders import flash_invaders

from .models import Invitation, PasswordReset, Team, User

FLASH_INVADERS_UID_PATTERN = re.compile(r"^[0-9A-Za-z-]{8,64}$")


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name"]


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "display_name", "role", "date_joined"]


class MeSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    # The UID is write-only: the browser only learns whether the sync is on. Empty turns it off.
    flash_invaders_uid = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=64)
    flash_sync_enabled = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "display_name",
            "role",
            "team",
            "map_theme",
            "flash_invaders_uid",
            "flash_sync_enabled",
            "manual_flash",
        ]
        # Only user preferences are editable here.
        read_only_fields = ["id", "email", "display_name", "role"]

    def get_flash_sync_enabled(self, user):
        return bool(user.flash_invaders_uid)

    def validate_flash_invaders_uid(self, uid):
        uid = uid.strip()
        if uid and (not FLASH_INVADERS_UID_PATTERN.match(uid) or not flash_invaders.check_uid(uid)):
            raise serializers.ValidationError("UID inconnu de Flash Invaders.")
        return uid


class TeamDetailSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ["id", "name", "created_at", "members"]

    def get_members(self, team):
        members = team.members.filter(is_active=True).order_by("display_name")
        return MemberSerializer(members, many=True).data


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(self.context["request"], email=attrs["email"], password=attrs["password"])
        if user is None:
            raise serializers.ValidationError("Email ou mot de passe incorrect.")
        attrs["user"] = user
        return attrs


class InvitationSerializer(serializers.ModelSerializer):
    invited_by = MemberSerializer(read_only=True)
    url = serializers.CharField(read_only=True)

    class Meta:
        model = Invitation
        fields = ["id", "email", "invited_by", "url", "created_at", "expires_at"]
        read_only_fields = ["created_at", "expires_at"]

    def validate_email(self, email):
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cet email.")
        return email


class PublicInvitationSerializer(serializers.ModelSerializer):
    """What an invited person sees before creating their account."""

    team = TeamSerializer(read_only=True)
    invited_by = serializers.CharField(source="invited_by.display_name", default=None, read_only=True)

    class Meta:
        model = Invitation
        fields = ["team", "invited_by", "email", "expires_at"]


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.CharField()
    email = serializers.EmailField()
    display_name = serializers.CharField(max_length=50)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_token(self, token):
        invitation = Invitation.objects.select_related("team").filter(token=token).first()
        if invitation is None or not invitation.is_pending:
            raise serializers.ValidationError("Cette invitation est invalide ou a expiré.")
        return invitation

    def validate_email(self, email):
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cet email.")
        return email

    def validate(self, attrs):
        invitation = attrs["token"]
        if invitation.email and invitation.email.lower() != attrs["email"].lower():
            raise serializers.ValidationError({"email": "Cette invitation est réservée à une autre adresse email."})
        candidate = User(email=attrs["email"], display_name=attrs["display_name"])
        try:
            password_validation.validate_password(attrs["password"], candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Lock the invitation so it cannot be used twice concurrently.
        invitation = Invitation.objects.select_for_update().get(pk=validated_data["token"].pk)
        if not invitation.is_pending:
            raise serializers.ValidationError({"token": "Cette invitation est invalide ou a expiré."})
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            display_name=validated_data["display_name"],
            team=invitation.team,
            role=invitation.role,
        )
        invitation.used_at = timezone.now()
        invitation.used_by = user
        invitation.save(update_fields=["used_at", "used_by"])
        return user


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_token(self, token):
        reset = PasswordReset.find(token)
        if reset is None or not reset.is_pending or not reset.user.is_active:
            raise serializers.ValidationError("Ce lien est invalide ou a expiré.")
        return reset

    def validate(self, attrs):
        try:
            password_validation.validate_password(attrs["password"], attrs["token"].user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        return attrs

    @transaction.atomic
    def save(self):
        # Lock the link so it cannot be used twice concurrently.
        reset = PasswordReset.objects.select_for_update().select_related("user").get(pk=self.validated_data["token"].pk)
        if not reset.is_pending:
            raise serializers.ValidationError({"token": "Ce lien est invalide ou a expiré."})
        user = reset.user
        # A new password hash also ends the member's other sessions (session auth hash).
        user.set_password(self.validated_data["password"])
        user.save(update_fields=["password"])
        reset.used_at = timezone.now()
        reset.save(update_fields=["used_at"])
        return user
