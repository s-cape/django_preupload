"""Model fields that use PreuploadFileField/PreuploadImageField in forms; set _preupload_name so no mixin is needed."""

from django.db import models

from .forms import PreuploadFileField, PreuploadImageField
from .widgets import PreuploadClearableFileWidget, PreuploadFileWidget


class PreuploadFileModelField(models.FileField):
    """FileField that uses PreuploadFileField in ModelForms (no mixin required)."""

    def formfield(self, **kwargs):
        kwargs.setdefault("form_class", PreuploadFileField)
        field = super().formfield(**kwargs)
        field._preupload_name = self.name
        return field


class PreuploadImageModelField(models.ImageField):
    """ImageField that uses PreuploadImageField in ModelForms (no mixin required)."""

    def formfield(self, **kwargs):
        kwargs.setdefault("form_class", PreuploadImageField)
        field = super().formfield(**kwargs)
        field._preupload_name = self.name
        field.widget = (
            PreuploadClearableFileWidget() if self.blank else PreuploadFileWidget()
        )
        return field
