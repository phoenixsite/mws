from django import forms
from tenants.models import Tenant
from mws_main.models import TenantAdmin


class TenantForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs["autofocus"] = True

    class Meta:
        model = Tenant
        fields = [
            "name",
            "subdomain_prefix",
            "email",
        ]
