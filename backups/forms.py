from django import forms
from django.utils.translation import gettext_lazy as _


class RestoreUploadFileForm(forms.Form):
    file = forms.FileField()

    def clean_file(self):
        restore_file = self.cleaned_data.get("file",  None)

        if not restore_file:
            raise forms.ValidationError(_("Please upload a restore file"))  # handle empty image
        elif len(str(restore_file)) <= 7:
            raise forms.ValidationError(_("File must have a name longer than 7 characters"))
        elif restore_file.name[-7:] != ".tar.xz":
            raise forms.ValidationError(_("Restore file must be a .tar.xz file"))

        # Note - Because the file isn't written out, we can't test here if the file passed in is actually a valid
        # archive. That test must take place in the view, after the file is written to disk.

        return restore_file
