from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Invitation, Role, Team


class Command(BaseCommand):
    help = "Create a team and print the invitation link for its first admin."

    def add_arguments(self, parser):
        parser.add_argument("name", help="Team name")
        parser.add_argument("--email", default="", help="Restrict the admin invitation to this email")

    @transaction.atomic
    def handle(self, *args, name, email, **options):
        team = Team.objects.create(name=name)
        invitation = Invitation.objects.create(team=team, email=email, role=Role.ADMIN)
        self.stdout.write(self.style.SUCCESS(f"Team “{team.name}” created (id={team.pk})."))
        self.stdout.write(f"Admin invitation link (expires {invitation.expires_at:%Y-%m-%d %H:%M}):")
        self.stdout.write(invitation.url)
