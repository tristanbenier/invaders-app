import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class Team(models.Model):
    name = models.CharField("nom", max_length=100)
    created_at = models.DateTimeField("créée le", auto_now_add=True)

    class Meta:
        verbose_name = "équipe"
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email must be set")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        return self._create_user(email, password, **extra_fields)


class Role(models.TextChoices):
    ADMIN = "admin", "Administrateur"
    MEMBER = "member", "Membre"


class MapTheme(models.TextChoices):
    LIGHT = "light", "Clair"
    DARK = "dark", "Sombre"


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    email = models.EmailField("email", unique=True)
    display_name = models.CharField("pseudo", max_length=50)
    # Superusers may have no team; every regular user belongs to exactly one.
    team = models.ForeignKey(
        Team,
        verbose_name="équipe",
        related_name="members",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    role = models.CharField("rôle", max_length=10, choices=Role.choices, default=Role.MEMBER)
    map_theme = models.CharField("thème de la carte", max_length=10, choices=MapTheme.choices, default=MapTheme.LIGHT)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    objects = UserManager()

    class Meta:
        verbose_name = "utilisateur"

    def __str__(self):
        return self.display_name or self.email

    @property
    def is_team_admin(self):
        return self.team_id is not None and self.role == Role.ADMIN


def generate_token():
    return secrets.token_urlsafe(32)


def default_expiration():
    return timezone.now() + timedelta(days=settings.INVITATION_VALIDITY_DAYS)


class InvitationQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(used_at__isnull=True, revoked_at__isnull=True, expires_at__gt=timezone.now())


class Invitation(models.Model):
    team = models.ForeignKey(Team, verbose_name="équipe", related_name="invitations", on_delete=models.CASCADE)
    # Null when created by a superuser from the command line (first team admin).
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="invité par",
        related_name="sent_invitations",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    token = models.CharField(max_length=64, unique=True, default=generate_token, editable=False)
    # When set, the invitation can only be accepted with this email.
    email = models.EmailField("email", blank=True)
    role = models.CharField("rôle", max_length=10, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField("créée le", auto_now_add=True)
    expires_at = models.DateTimeField("expire le", default=default_expiration)
    used_at = models.DateTimeField("utilisée le", null=True, blank=True)
    used_by = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="utilisée par",
        related_name="accepted_invitation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    revoked_at = models.DateTimeField("révoquée le", null=True, blank=True)

    objects = InvitationQuerySet.as_manager()

    class Meta:
        verbose_name = "invitation"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.team} — {self.email or self.token[:8]}"

    @property
    def is_pending(self):
        return self.used_at is None and self.revoked_at is None and self.expires_at > timezone.now()

    @property
    def url(self):
        return f"{settings.FRONTEND_URL.rstrip('/')}/invitation/{self.token}"
