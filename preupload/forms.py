"""PreuploadFileField (token resolution in clean) and PreuploadFormMixin."""

import copy

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile

from .storage import storage
from . import tokens
from .widgets import PreuploadClearableFileWidget, PreuploadFileWidget


def _wrap_preupload_as_uploaded_file(preupload):
    """Open preuploaded file and wrap as UploadedFile-like for form validation."""
    f = storage.open(preupload.storage_ref)
    content = f.read()
    f.close()
    return SimpleUploadedFile(
        name=preupload.original_filename,
        content=content,
        content_type="application/octet-stream",
    )


def _resolve_token_to_uploaded(token):
    """Resolve preupload token to SimpleUploadedFile; raise ValidationError on failure."""
    preupload = tokens.resolve_preupload_token(token.strip())
    if preupload is None:
        raise forms.ValidationError("Invalid or expired upload. Please upload again.")
    try:
        return _wrap_preupload_as_uploaded_file(preupload)
    except Exception:
        raise forms.ValidationError("Invalid or expired upload. Please upload again.")


class PreuploadFileField(forms.FileField):
    """FileField that resolves a preupload token (value from widget); file is only ever from token, not from request.FILES."""

    widget = PreuploadFileWidget

    def bound_data(self, data, initial):
        """Return token for display when re-rendering bound form (FileField normally returns initial only)."""
        if data and isinstance(data, str):
            stripped = data.strip()
            if stripped:
                return stripped
        return initial

    def clean(self, value, initial=None):
        name = getattr(self, "_preupload_name", None)
        if not name:
            return super().clean(value, initial=initial)
        token = (value if isinstance(value, str) else "") or ""
        if not token.strip():
            return super().clean(value, initial=initial)
        uploaded = _resolve_token_to_uploaded(token)
        return super().clean(uploaded, initial=initial)


class PreuploadImageField(forms.ImageField):
    """ImageField + preupload token resolution; same as ImageField, only adds hidden token input."""

    def bound_data(self, data, initial):
        if data and isinstance(data, str):
            stripped = data.strip()
            if stripped:
                return stripped
        return initial

    def clean(self, value, initial=None):
        name = getattr(self, "_preupload_name", None)
        if not name:
            return super().clean(value, initial=initial)
        token = (value if isinstance(value, str) else "") or ""
        if not token.strip():
            return super().clean(value, initial=initial)
        uploaded = _resolve_token_to_uploaded(token)
        return super().clean(uploaded, initial=initial)


class PreuploadFormMixin:
    """
    Replaces FileField with PreuploadFileField, ImageField with PreuploadImageField, and sets Preupload widget.
    File data is only from the preupload token (not from request.FILES).
    Widget: clearable when field is not required, else non-clearable.
    Override preupload_field_widgets with (field_type, widget_class) tuples to customize.
    """

    preupload_field_widgets = ()  # optional override; default is by field.required
    preupload_skip_fields = ()  # optional: list of field names to skip (e.g. for ModelForm)

    def __init__(self, *args, **kwargs):
        kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self._wrap_file_fields()

    def _get_preupload_widget_class(self, field):
        for field_cls, widget_cls in self.preupload_field_widgets:
            if isinstance(field, field_cls):
                return widget_cls
        return (
            PreuploadClearableFileWidget if not field.required else PreuploadFileWidget
        )

    def _wrap_file_fields(self):
        from django.forms import FileField as BaseFileField
        from django.forms import ImageField

        skip_names = getattr(self, "preupload_skip_fields", ())
        for name, field in list(self.fields.items()):
            if name in skip_names or getattr(field, "preupload_skip", False):
                continue
            if isinstance(field, (PreuploadFileField, PreuploadImageField)):
                continue
            if not isinstance(field, (BaseFileField, ImageField)):
                continue
            new_field = copy.copy(field)
            new_field.__class__ = (
                PreuploadImageField
                if isinstance(field, ImageField)
                else PreuploadFileField
            )
            new_field._preupload_name = name
            new_field.widget = self._get_preupload_widget_class(field)(
                attrs=field.widget.attrs
            )
            self.fields[name] = new_field
