from django.forms.models import (
    ModelForm,
    ModelChoiceField
)
from django.forms import HiddenInput
from django.forms.fields import CharField
from django.contrib.auth import forms as auth_forms
from django.forms.widgets import Select
from mws_main.models import Client
from tenants.models import Tenant

from bson import ObjectId


class SelectTenant(Select):

    def value_from_datadict(self, data, files, name):
        return ObjectId(data.get(name))
    
    
class TenantChoiceField(ModelChoiceField):
    widget = SelectTenant


class ClientAdminForm(ModelForm):

    tenant = TenantChoiceField(
        queryset=Tenant.objects.all(),
    )
    
    class Meta:
        model = Client
        exclude = ['services_acq', 'tenant']
        
        
class ClientCreationForm(auth_forms.UserCreationForm):

    repo_addr = CharField(widget=HiddenInput)
    
    def save(self, commit=True):
        client = super().save(commit=False)
        client.tenant = Tenant.objects.get(
            repo_addr=self.cleaned_data["repo_addr"])

        if commit:
            client.save()

        return client
    
    class Meta:
        model = Client
        fields = ["first_name",
                  "last_name",
                  "email",
                  "username"]
        exclude = ['services_acq', 'tenant']
