from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from preupload.models import Preupload
from preupload.storage import save as storage_save
from preupload import tokens


class TokensTestCase(TestCase):
    def setUp(self):
        storage_ref = storage_save(__import__("io").BytesIO(b"x"), name="x.txt")
        self.preupload = Preupload.objects.create(
            token=None,
            storage_ref=storage_ref,
            original_filename="x.txt",
        )
        self.preupload.token = tokens.generate_token(self.preupload)
        self.preupload.save(update_fields=["token"])

    def test_generate_and_resolve(self):
        resolved = tokens.resolve_preupload_token(self.preupload.token)
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.pk, self.preupload.pk)

    def test_resolve_invalid_token_returns_none(self):
        self.assertIsNone(tokens.resolve_preupload_token("invalid"))
        self.assertIsNone(tokens.resolve_preupload_token(""))

    def test_resolve_expired_token_returns_none(self):
        Preupload.objects.filter(pk=self.preupload.pk).update(
            created_at=timezone.now() - timedelta(minutes=61)
        )
        self.assertIsNone(tokens.resolve_preupload_token(self.preupload.token))
