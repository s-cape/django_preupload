"""Signed token generation and validation for preupload resolution."""

from datetime import timedelta

from django.core.signing import Signer, BadSignature
from django.utils import timezone

from .conf import preupload_config
from .models import Preupload

_signer = Signer()


def generate_token(preupload):
    """Return a signed token that can be used to resolve this Preupload."""
    payload = str(preupload.pk)
    return _signer.sign(payload)


def resolve_preupload_token(token):
    """Verify signature, load Preupload, check expiry (created_at + TTL). Return instance or None."""
    if not (token and token.strip()):
        return None
    try:
        pk = int(_signer.unsign(token.strip()))
        preupload = Preupload.objects.get(pk=pk)
    except (BadSignature, ValueError, TypeError, Preupload.DoesNotExist):
        return None
    if timezone.now() > preupload.created_at + timedelta(minutes=preupload_config["TTL_MINUTES"]):
        return None
    return preupload
