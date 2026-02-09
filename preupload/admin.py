"""PreuploadAdminMixin: PreuploadFormMixin for admin and inlines."""

from django.contrib import admin

from .forms import PreuploadFormMixin


class PreuploadAdminMixin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj=obj, **kwargs)
        return type("FormWithPreupload", (PreuploadFormMixin, form_class), {})

    def get_formset(self, request, obj=None, **kwargs):
        formset_class = super().get_formset(request, obj=obj, **kwargs)
        form_class = formset_class.form
        new_form = type("FormWithPreupload", (PreuploadFormMixin, form_class), {})
        return type("FormSetWithPreupload", (formset_class,), {"form": new_form})
