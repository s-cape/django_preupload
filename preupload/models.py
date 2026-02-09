from django.db import models


class Preupload(models.Model):
    """Tracks a preuploaded file until commit or expiry (based on created_at + TTL)."""

    token = models.CharField(max_length=255, unique=True, db_index=True, null=True, blank=True)
    storage_ref = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
