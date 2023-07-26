from django import forms
from tenants.models import (
    Tenant, TenantAdmin, DefaultSubsAgreement,
    IResourcePlan,
    )


class TenantForm(forms.ModelForm):

    card_number = forms.CharField(
        label="Card number",
        max_length=100)
               
    subs_agree_number = forms.ModelChoiceField(
        label="Subscription agreement",
        queryset=DefaultSubsAgreement.objects.all(), to_field_name="name")
    
    class Meta:
        model = Tenant
        fields = [
            "name",
            "repo_addr",
        ]


class AdminForm(forms.ModelForm):

    class Meta:
        model = TenantAdmin
        fields = [
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
        ]


class DefaultSubsAgreementForm(forms.ModelForm):

    class Meta:
        model = DefaultSubsAgreement
        fields = ["name", "plans", "duration"]
