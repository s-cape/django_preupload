"""Delete expired preuploads and their preuploaded files (by created_at + TTL)."""

from datetime import timedelta

from django.utils import timezone
from django.core.management.base import BaseCommand

from preupload.conf import preupload_config
from preupload.models import Preupload
from preupload.storage import storage


class Command(BaseCommand):
    help = "Remove expired preupload records and their preuploaded files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report what would be deleted.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        cutoff = timezone.now() - timedelta(minutes=preupload_config["TTL_MINUTES"])
        qs = Preupload.objects.filter(created_at__lt=cutoff)
        count = 0
        for preupload in qs.iterator():
            if not dry_run:
                try:
                    storage.delete(preupload.storage_ref)
                    preupload.delete()
                    count += 1
                except Exception as e:
                    self.stderr.write(
                        "Failed to delete storage for pk=%s: %s" % (preupload.pk, e)
                    )
            else:
                count += 1
        if dry_run:
            self.stdout.write("Would delete %d expired preupload(s)." % count)
        else:
            self.stdout.write("Deleted %d expired preupload(s)." % count)
