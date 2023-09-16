from django import forms
from django.contrib.auth.forms import UserCreationForm
from tenants.models import (
    Tenant, TenantAdmin,
    )


class TenantForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs["autofocus"] = True

    class Meta:
        model = Tenant
        fields = [
            "name",
            "store_url",
        ]


class AdminForm(UserCreationForm):

    class Meta:
        model = TenantAdmin
        fields = ['username',
                  'first_name',
                  'last_name',
                  'email',
                  ]
