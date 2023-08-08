import django.forms as forms
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import authenticate
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


class AuthenticationForm(auth_forms.AuthenticationForm):

    def __init__(self, request=None, *args, **kwargs):

        super().__init__(request, *args, **kwargs)

        repo_addr = request.path.split('/')[2]
        tenant = Tenant.objects.get(repo_addr=repo_addr)
        self.tenant_id = str(tenant._id)

    def clean(self):

        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:
            self.user_cache = authenticate(
                self.request,
                tenant_id=self.tenant_id,
                username=username,
                password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


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


class ServiceCreationForm(forms.Form):

    repo_addr = forms.CharField(widget=forms.HiddenInput)
    descrp = forms.CharField(
        max_length=1000,
        help_text="1000 characters max.",
        widget=forms.Textarea
    )
    package = forms.FileField(
        label="Package file",
        help_text="Only APK and iPhone IPA packages supported.",
        widget=forms.FileInput
    )

    def save(self, commit=True):

        
        service = models.create_service(
            self.cleaned_data["package"],
            self.cleaned_data["descrp"]
        )
        service.tenant = Tenant.objects.get(
            repo_addr=self.cleaned_data["repo_addr"])

        if commit:
            service.save()

        return service


class ClientUpdateForm(forms.ModelForm):

    class Meta:
        model = models.Client
        fields = ["username",
                  "first_name",
                  "last_name",
                  "email",
                  ]

class DeveloperUpdateForm(forms.ModelForm):

    class Meta:
        model = models.Developer
        fields = ["username",
                  "first_name",
                  "last_name",
                  "email",]
