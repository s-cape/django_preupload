"""PreuploadFileField (token resolution in clean) and PreuploadFormMixin."""

import copy

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile

from .storage import open_file
from . import tokens
from .widgets import PreuploadFileWidget, PreuploadImageWidget


def _wrap_preupload_as_uploaded_file(preupload):
    """Open preuploaded file and wrap as UploadedFile-like for form validation."""
    f = open_file(preupload.storage_ref)
    content = f.read()
    f.close()
    return SimpleUploadedFile(
        name=preupload.original_filename,
        content=content,
        content_type="application/octet-stream",
    )


class PreuploadFileField(forms.FileField):
    """Like FileField but resolves token from POST when no new file; injects preuploaded file."""

    def clean(self, value, initial=None):
        name = getattr(self, "_preupload_name", None)
        if not name:
            return super().clean(value, initial=initial)
        files = (getattr(self.form, "files", None) or {}) if self.form else {}
        data = (getattr(self.form, "data", None) or {}) if self.form else {}
        token_name = name + "_token"
        file_from_post = files.get(name)
        if file_from_post:
            return super().clean(file_from_post, initial=initial)
        token = data.get(token_name) or (value if isinstance(value, str) else "")
        if not token:
            return super().clean(value, initial=initial)
        preupload = tokens.resolve_preupload_token(token.strip())
        if preupload is None:
            raise forms.ValidationError(
                "Invalid or expired upload. Please upload again."
            )
        try:
            uploaded = _wrap_preupload_as_uploaded_file(preupload)
        except Exception:
            raise forms.ValidationError(
                "Invalid or expired upload. Please upload again."
            )
        return super().clean(uploaded, initial=initial)


class PreuploadFormMixin:
    """
    Replaces FileField/ImageField with PreuploadFileField and PreuploadWidget.
    Override preupload_field_widgets to customize which widget is used for which field type
    (first matching type wins; list (field_type, widget_class) tuples).
    """

    preupload_field_widgets = [
        (forms.ImageField, PreuploadImageWidget),
        (forms.FileField, PreuploadFileWidget),
    ]

    def __init__(self, *args, **kwargs):
        kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self._wrap_file_fields()

    def _get_preupload_widget_class(self, field):
        for field_cls, widget_cls in self.preupload_field_widgets:
            if isinstance(field, field_cls):
                return widget_cls
        return PreuploadFileWidget

    def _wrap_file_fields(self):
        from django.forms import FileField as BaseFileField
        from django.forms import ImageField

        for name, field in list(self.fields.items()):
            if getattr(field, "preupload_skip", False):
                continue
            if isinstance(field, PreuploadFileField):
                continue
            if not isinstance(field, (BaseFileField, ImageField)):
                continue
            new_field = copy.copy(field)
            new_field.__class__ = PreuploadFileField
            new_field._preupload_name = name
            new_field.widget = self._get_preupload_widget_class(field)(
                attrs=field.widget.attrs
            )
            self.fields[name] = new_field
        for name, field in self.fields.items():
            if isinstance(field, PreuploadFileField):
                field.form = self
