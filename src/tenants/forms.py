from django import forms
from django.contrib.auth.forms import UserCreationForm
from tenants.models import (
    Tenant, TenantAdmin, DefaultSubsAgreement,
    IResourcePlan,
    )


class TenantForm(forms.ModelForm):

    card_number = forms.CharField(
        label="Card number",
        max_length=100)

    """
    subs_agree_number = forms.ModelChoiceField(
        label="Subscription agreement",
        queryset=DefaultSubsAgreement.objects.all(), to_field_name="name")
    """
    class Meta:
        model = Tenant
        fields = [
            "name",
            "repo_addr",
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
