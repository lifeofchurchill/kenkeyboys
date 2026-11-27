"""
One-off: copies every file in the local media folder into the site's
file storage (the Neon bucket), keeping the same names, so the database's
references like "players/kwame.jpg" still point at the right file.

    python manage.py upload_media
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Upload the local media folder to the site's file storage, keeping file names."

    def handle(self, *args, **options):
        # Stop if uploads would still go to the local folder (no bucket in .env)
        if "s3" not in settings.STORAGES["default"]["BACKEND"].lower():
            raise CommandError("No bucket is set up. Add the AWS_ lines to .env first.")

        media = Path(settings.MEDIA_ROOT)
        if not media.exists():
            raise CommandError(f"There's no media folder at {media}")

        uploaded = skipped = 0
        for path in sorted(media.rglob("*")):
            if not path.is_file():
                continue

            # The name the database uses, with forward slashes (Windows uses backslashes)
            name = path.relative_to(media).as_posix()

            # Already in the bucket (e.g. running this a second time): leave it
            if default_storage.exists(name):
                skipped += 1
                continue

            with path.open("rb") as handle:
                saved = default_storage.save(name, File(handle))

            if saved != name:
                # Shouldn't happen, but if it does, the database won't find this file
                self.stdout.write(self.style.WARNING(f"  Saved {name} as {saved}"))
            else:
                self.stdout.write(f"Uploaded {name}")
            uploaded += 1

        self.stdout.write(self.style.SUCCESS(f"Done: {uploaded} uploaded, {skipped} already there."))