from django.forms import ClearableFileInput, FileInput
from django.urls import reverse


class PreuploadWidgetMixin:
    """Adds hidden token input and preupload URL/CSRF to context; subclasses set super_template."""

    template_name = "preupload/widgets/preupload.html"

    class Media:
        js = ("preupload/js/preupload.js",)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["super_template"] = self.super_template
        context["widget"]["name_token"] = name + "_token"
        context["widget"]["token_value"] = (
            value if (value and isinstance(value, str)) else ""
        )
        context["widget"]["preupload_url"] = getattr(
            self, "preupload_url", None
        ) or reverse("preupload:preupload")
        context["widget"]["preupload_csrf_token"] = getattr(
            self, "preupload_csrf_token", ""
        )
        return context

    def value_from_datadict(self, data, files, name):
        return data.get(name + "_token", "")

    def value_omitted_from_data(self, data, files, name):
        return (name + "_token") not in (data or {}) and name not in (files or {})


class PreuploadFileWidget(PreuploadWidgetMixin, FileInput):
    """FileInput + hidden token input."""

    super_template = FileInput.template_name


class PreuploadClearableFileWidget(PreuploadWidgetMixin, ClearableFileInput):
    """ClearableFileInput + hidden token input; use for optional file/image fields."""

    super_template = ClearableFileInput.template_name

    def value_from_datadict(self, data, files, name):
        if not self.is_required and data.get(self.clear_checkbox_name(name)):
            return False
        return super().value_from_datadict(data, files, name)


PreuploadImageWidget = PreuploadClearableFileWidget
