from django.db import migrations


def add_space2iss(apps, schema_editor):
    from apps.invaders.space2iss import add_to_teams

    add_to_teams(apps)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("invaders", "0003_invader_address1_invader_address2_invader_comment_and_more"),
    ]

    # Not reverted: the invader may have flashes and edits by then.
    operations = [migrations.RunPython(add_space2iss, migrations.RunPython.noop)]
