from typing import Any, Dict

from django.http import HttpRequest, HttpResponse
from django.views.generic import ListView, DetailView, FormView, CreateView, UpdateView, DeleteView
from .models import Backup
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django_downloadview.views.path import PathDownloadView
from .forms import RestoreUploadFileForm
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import PermissionRequiredMixin

import tarfile

from django.contrib.messages.views import SuccessMessageMixin


# Abstract Views
class ModelCreateView(CreateView):
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['model'] = self.model
        return context


class ModelUpdateView(UpdateView):
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['model'] = self.model
        return context


class SuccessMessageDeleteView(DeleteView):
    """Mirrors the functionality of SuccessMessageMixin, but on a DeleteView"""
    success_message = _("Successfully deleted %(object)s")

    def get_success_message(self):
        obj_name = {'object': str(self.get_object())}

        return self.success_message % obj_name

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        success_message = self.get_success_message()
        if success_message:
            messages.success(self.request, success_message)
        return super().post(request, *args, **kwargs)


# Backup Views
class BackupListView(PermissionRequiredMixin, ListView):
    model = Backup
    permission_required = 'backups.view_backup'


class BackupDetailView(PermissionRequiredMixin, DetailView):
    model = Backup
    permission_required = 'backups.view_backup'


class BackupCreateView(PermissionRequiredMixin, SuccessMessageMixin, ModelCreateView):
    model = Backup
    fields = []
    permission_required = 'backups.add_backup'
    success_message = _("Successfully created backup")

    def form_valid(self, form):
        backup = form.instance
        self.object = backup
        backup.perform_backup()  # TODO - Replace with task
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("backups:backup_detail", kwargs={"pk": self.object.pk})


class BackupDeleteView(PermissionRequiredMixin, SuccessMessageDeleteView):
    model = Backup
    success_url = reverse_lazy('backups:backup_list')
    permission_required = 'backups.delete_backup'
    success_message = _("Successfully deleted backup")


# def upload_file(request):
#     if request.method == 'POST':
#         form = UploadFileForm(request.POST, request.FILES)
#         if form.is_valid():
#             handle_uploaded_file(request.FILES['file'])
#             return HttpResponseRedirect('/success/url/')
#     else:
#         form = UploadFileForm()
#     return render(request, 'upload.html', {'form': form})


class RestoreView(PermissionRequiredMixin, FormView):
    template_name = 'backups/backup_restore.html'
    form_class = RestoreUploadFileForm
    success_url = reverse_lazy('taplist:combined_list')
    permission_required = 'backups.restore_backup'  # Custom permission

    def form_valid(self, form):
        """Process the upload and restore the data"""
        restore_file = form.cleaned_data['file']
        output_path = settings.BACKUP_STAGING_DIR.parent / restore_file.name  # Just keep the file name
        with open(output_path, 'wb+') as destination:
            for chunk in restore_file.chunks():
                destination.write(chunk)

        if not tarfile.is_tarfile(output_path):
            output_path.unlink(missing_ok=True)
            messages.error(self.request, _("Restore file must be a valid .tar.xz archive"))
            return redirect(reverse('backups:backup_restore'))

        new_backup, created = Backup.objects.get_or_create(filename_prefix=restore_file.name[:-7])

        new_backup.perform_restore()

        return super().form_valid(form)

    # def get_context_data(self, **kwargs):
    #     """Add the hostname from the request to the context for display"""
    #     context = super().get_context_data(**kwargs)
    #     context['hostname_accessed_at'] = self.request.META['HTTP_HOST']
    #     return context

    # def get_initial(self):
    #     """Returns the initial data to use for forms on this view, as loaded from Constance"""
    #     initial = super().get_initial()
    #     initial['cast_enable'] = config.CAST_ENABLE
    #     initial['cast_hostname'] = config.CAST_HOSTNAME
    #     return initial


class BackupDownloadView(PermissionRequiredMixin, SingleObjectMixin, PathDownloadView):
    model = Backup
    permission_required = 'backups.view_backup'

    def get_path(self):
        """Return path to the linked backup file"""
        object = self.get_object()
        return object.outfile_path

    def get_basename(self):
        object = self.get_object()
        return f"{object.filename_prefix}.tar.xz"


    # def get(self, request, *args, **kwargs):
    #     return super().get(request, *args, **kwargs)
