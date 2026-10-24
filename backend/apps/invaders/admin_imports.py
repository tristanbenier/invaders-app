"""Django admin screens to import invaders (JSON) and upload photos.

Both reuse the same code as the API and the management commands
(importer.py and photos.py). The JSON import has two steps: a preview, then a
confirmation; the uploaded rows wait in a temporary file in between.
"""

import json
import re
import secrets
import tempfile
import time
from pathlib import Path

from django import forms
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.accounts.models import Team, User

from . import importer
from .models import Invader
from .photos import InvalidImage, attach_photo, invader_name_from_filename

PENDING_DIR = Path(tempfile.gettempdir()) / "invaders-imports"
TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{20,64}$")
MAX_PHOTOS_PER_UPLOAD = 100


def _members():
    return User.objects.filter(team__isnull=False, is_active=True).select_related("team").order_by("team__name", "display_name")


class TeamAndAuthorForm(forms.Form):
    team = forms.ModelChoiceField(Team.objects.order_by("name"), label="Équipe")
    author = forms.ModelChoiceField(
        _members(),
        label="Auteur",
        help_text="Membre de l'équipe enregistré comme auteur dans l'historique.",
    )

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["author"].queryset = _members()
        self.fields["author"].label_from_instance = lambda user: f"{user.display_name} ({user.email}) — {user.team}"
        user = getattr(request, "user", None)
        if user is not None and user.team_id and not self.is_bound:
            self.initial.setdefault("team", user.team_id)
            self.initial.setdefault("author", user.pk)

    def clean(self):
        cleaned = super().clean()
        team, author = cleaned.get("team"), cleaned.get("author")
        if team and author and author.team_id != team.pk:
            self.add_error("author", "L'auteur doit faire partie de l'équipe choisie.")
        return cleaned


class InvaderImportForm(TeamAndAuthorForm):
    file = forms.FileField(label="Fichier JSON", help_text="Liste d'invaders, 5 Mo maximum (format décrit ci-dessous).")
    mark_as_flashed = forms.BooleanField(
        label="Marquer tous ces invaders comme flashés par l'auteur", required=False
    )


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data]
        files = [super(MultipleImageField, self).clean(file, initial) for file in files if file]
        if not files:
            raise forms.ValidationError("Choisissez au moins une photo.")
        if len(files) > MAX_PHOTOS_PER_UPLOAD:
            raise forms.ValidationError(f"{MAX_PHOTOS_PER_UPLOAD} photos maximum par envoi.")
        return files


class PhotoUploadForm(TeamAndAuthorForm):
    photos = MultipleImageField(
        label="Photos",
        help_text="Chaque fichier est rattaché à l'invader dont il porte le nom : « PA_223.jpg » ou « PA_223.xxx.png ».",
    )
    overwrite = forms.BooleanField(label="Remplacer les photos existantes", required=False)
    square = forms.BooleanField(
        label="Recadrer en carré",
        required=False,
        help_text="Sinon, les photos gardent leurs proportions.",
    )


def _readable(errors):
    """ "points : Ce champ est obligatoire. ; name : …" from DRF-style errors."""
    if isinstance(errors, dict):
        return " ; ".join(f"{field} : {' '.join(map(str, messages))}" for field, messages in errors.items())
    return " ".join(map(str, errors))


def _save_pending(rows):
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    # Previews never confirmed: drop them after a day.
    for stale in PENDING_DIR.glob("*.json"):
        if time.time() - stale.stat().st_mtime > 24 * 60 * 60:
            stale.unlink(missing_ok=True)
    token = secrets.token_urlsafe(24)
    (PENDING_DIR / f"{token}.json").write_text(json.dumps(rows), encoding="utf-8")
    return token


def _pending_path(token):
    if not TOKEN_PATTERN.match(token or ""):
        return None
    path = PENDING_DIR / f"{token}.json"
    return path if path.is_file() else None


def import_invaders_view(model_admin, request):
    context = {**model_admin.admin_site.each_context(request), "opts": Invader._meta, "title": "Importer des invaders"}
    changelist = reverse("admin:invaders_invader_changelist")

    if request.method == "POST" and request.POST.get("step") == "confirm":
        form = TeamAndAuthorForm(request.POST, request=request)
        path = _pending_path(request.POST.get("token"))
        if path is None:
            messages.error(request, "Cet import a expiré : envoyez le fichier à nouveau.")
            return redirect("admin:invaders_invader_import")
        if form.is_valid():
            team, author = form.cleaned_data["team"], form.cleaned_data["author"]
            rows = json.loads(path.read_text(encoding="utf-8"))
            # Analyzed again: the data may have changed since the preview.
            result = importer.analyze(team, rows)
            if result["errors"]:
                messages.error(request, "Le fichier contient des erreurs : rien n'a été importé.")
            else:
                done = importer.commit(team, author, result, request.POST.get("mark_as_flashed") == "on")
                path.unlink(missing_ok=True)
                messages.success(
                    request,
                    f"Import terminé dans « {team} » : {done['created']} créé(s), {done['updated']} mis à jour, "
                    f"{done['cities_created']} ville(s) créée(s), {done['flashed']} flash(s) ajouté(s).",
                )
                return redirect(changelist)
        form = InvaderImportForm(request=request)
        return render(request, "admin/invaders/invader/import_invaders.html", {**context, "form": form})

    form = InvaderImportForm(request.POST or None, request.FILES or None, request=request)
    if request.method == "POST" and form.is_valid():
        try:
            rows = importer.read_rows(form.cleaned_data["file"])
        except importer.ImportFileError as exc:
            form.add_error("file", str(exc))
        else:
            team = form.cleaned_data["team"]
            summary = importer.summarize(importer.analyze(team, rows))
            return render(
                request,
                "admin/invaders/invader/import_invaders_preview.html",
                {
                    **context,
                    "title": "Vérifier l'import",
                    "summary": summary,
                    "errors": [{**error, "errors": _readable(error["errors"])} for error in summary["errors"][:100]],
                    "updates": summary["to_update"][:100],
                    "token": _save_pending(rows),
                    "team": team,
                    "author": form.cleaned_data["author"],
                    "mark_as_flashed": form.cleaned_data["mark_as_flashed"],
                },
            )
    return render(request, "admin/invaders/invader/import_invaders.html", {**context, "form": form})


def upload_photos_view(model_admin, request):
    context = {**model_admin.admin_site.each_context(request), "opts": Invader._meta, "title": "Envoyer des photos"}
    form = PhotoUploadForm(request.POST or None, request.FILES or None, request=request)
    report = None
    if request.method == "POST" and form.is_valid():
        team, author = form.cleaned_data["team"], form.cleaned_data["author"]
        invaders = {invader.name: invader for invader in Invader.objects.filter(team=team)}
        report = {"imported": [], "skipped": [], "problems": []}
        for photo in form.cleaned_data["photos"]:
            name = invader_name_from_filename(photo.name)
            invader = invaders.get(name)
            if invader is None:
                report["problems"].append(f"{photo.name} : aucun invader « {name or '?'} » dans l'équipe.")
            elif invader.image and not form.cleaned_data["overwrite"]:
                report["skipped"].append(invader.name)
            else:
                try:
                    attach_photo(invader, photo, author=author, square=form.cleaned_data["square"])
                    report["imported"].append(invader.name)
                except InvalidImage as exc:
                    report["problems"].append(f"{photo.name} : {exc}")
        if report["imported"]:
            messages.success(request, f"{len(report['imported'])} photo(s) ajoutée(s) dans « {team} ».")
    return render(request, "admin/invaders/invader/upload_photos.html", {**context, "form": form, "report": report})
