from django.forms.models import (
    ModelForm,
    ModelChoiceField
)
from django.forms.widgets import Select
from mws_main.models import Client
from tenants.models import Tenant

from bson import ObjectId


class SelectTenant(Select):

    def value_from_datadict(self, data, files, name):
        return ObjectId(data.get(name))
    
    
class TenantChoiceField(ModelChoiceField):
    widget = SelectTenant


class ClientForm(ModelForm):

    tenant = TenantChoiceField(
        queryset=Tenant.objects.all(),
    )
    
    class Meta:
        model = Client
        exclude = ['services_acq', 'tenant']
