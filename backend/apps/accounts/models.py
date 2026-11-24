import hashlib
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
    # Identifies the member's Flash Invaders account (apps/invaders/flash_invaders.py): secret,
    # never serialized back to the browser.
    flash_invaders_uid = models.CharField("UID Flash Invaders", max_length=64, blank=True)
    # Keep the manual flash buttons despite the sync (e.g. while the app's API is broken).
    manual_flash = models.BooleanField("flash manuel avec la synchro", default=False)

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


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def default_reset_expiration():
    return timezone.now() + timedelta(hours=settings.PASSWORD_RESET_VALIDITY_HOURS)


class PasswordResetQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(used_at__isnull=True, revoked_at__isnull=True, expires_at__gt=timezone.now())


class PasswordReset(models.Model):
    """Single-use link created by a team admin for a member who forgot their password (no email sent)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="membre", related_name="password_resets", on_delete=models.CASCADE
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="créé par",
        related_name="created_password_resets",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    # Only the SHA-256 of the token is stored: the link is shown once, to the admin who creates it.
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField("créé le", auto_now_add=True)
    expires_at = models.DateTimeField("expire le", default=default_reset_expiration)
    used_at = models.DateTimeField("utilisé le", null=True, blank=True)
    revoked_at = models.DateTimeField("annulé le", null=True, blank=True)

    objects = PasswordResetQuerySet.as_manager()

    class Meta:
        verbose_name = "réinitialisation de mot de passe"
        verbose_name_plural = "réinitialisations de mot de passe"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def is_pending(self):
        return self.used_at is None and self.revoked_at is None and self.expires_at > timezone.now()

    @classmethod
    def issue(cls, user, created_by):
        """Cancels the member's pending links and returns a new one with its clear token."""
        cls.objects.pending().filter(user=user).update(revoked_at=timezone.now())
        token = generate_token()
        return cls.objects.create(user=user, created_by=created_by, token_hash=hash_token(token)), token

    @classmethod
    def find(cls, token):
        return cls.objects.select_related("user").filter(token_hash=hash_token(token)).first()

    @staticmethod
    def url_for(token):
        return f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{token}"
