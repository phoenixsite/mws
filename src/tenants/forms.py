from django import forms
from django.contrib.auth.forms import UserCreationForm
from tenants.models import (
    Tenant, TenantAdmin, DefaultSubsAgreement,
    IResourcePlan,
    )


class TenantForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs["autofocus"] = True

    """
    subs_agree_number = forms.ModelChoiceField(
        label="Subscription agreement",
        queryset=DefaultSubsAgreement.objects.all(), to_field_name="name")
    """
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
                  'email',]
        
class DefaultSubsAgreementForm(forms.ModelForm):

    class Meta:
        model = DefaultSubsAgreement
        fields = ["name", "plans", "duration"]
