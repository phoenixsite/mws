import django.forms as forms
from django.contrib.auth import forms as auth_forms
from mws_main import models
from tenants.models import Tenant

from bson import ObjectId


class SelectTenant(forms.Select):

    def value_from_datadict(self, data, files, name):
        return ObjectId(data.get(name))
    
    
class TenantChoiceField(forms.ModelChoiceField):
    widget = SelectTenant


class ClientAdminForm(forms.ModelForm):

    tenant = TenantChoiceField(
        queryset=Tenant.objects.all(),
    )
    
    class Meta:
        model = models.Client
        exclude = ['services_acq', 'tenant']


class TenantUserCreationForm(auth_forms.UserCreationForm):

    repo_addr = forms.CharField(widget=forms.HiddenInput)
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.tenant = Tenant.objects.get(
            repo_addr=self.cleaned_data["repo_addr"])

        if commit:
            user.save()

            if not user.groups:
                group = self._meta.model.get_group()
                user.add(group)

        return user


    class Meta:
        model = None
        fields = ["username",
                  "first_name",
                  "last_name",
                  "email",]
        exclude = ['tenant']
        

class ClientCreationForm(TenantUserCreationForm):
    
    class Meta(TenantUserCreationForm.Meta):
        model = models.Client
        exclude = ['services_acq', 'tenant']


class DeveloperCreationForm(TenantUserCreationForm):

    class Meta(TenantUserCreationForm.Meta):
        model = models.Developer
        exclude = ['tenant']

class ServiceCreationForm(forms.ModelForm):

    repo_addr = forms.CharField(widget=forms.HiddenInput)

    def save(self, commit=True):
        service = super().save(commit=False)
        service.tenant = Tenant.objects.get(
            repo_addr=self.cleaned_data["repo_addr"])

        if commit:
            service.save()

        return service


    class Meta:
        model = models.Service
        exclude = ["size",
                   "n_downloads",
                   "version_history",
                   "tenant",
                   ]


class ClientUpdateForm(auth_forms.UserChangeForm):

    class Meta:
        model = models.Client
        fields = ["username",
                  "first_name",
                  "last_name",
                  "email"]

class DeveloperUpdateForm(auth_forms.UserChangeForm):

    class Meta:
        model = models.Developer
        fields = ["username",
                  "first_name",
                  "last_name",
                  "email",]
    
