from django import forms
from tenants.models import Tenant

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

        error_messages = {
            "subdomain_prefix": {
                "unique": "There is already a store with that subdomain."
            }
        }
