import django.forms as forms
from django.db.models import Q
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import authenticate
from mws_main import models
from tenants.models import Tenant, User


class ClientAdminForm(forms.ModelForm):

    tenant = forms.ModelChoiceField(
        queryset=Tenant.objects.all(),
    )
    
    class Meta:
        model = models.Client
        exclude = ['services_acq', 'tenant']


class URLNotValidError(Exception):
    pass


class AuthenticationForm(auth_forms.AuthenticationForm):
    """
    Form the user fill to authenticate in corresponding
    store.
    """

    def __init__(self, request=None, *args, **kwargs):

        super().__init__(request, *args, **kwargs)

        try:
            store_url = request.path.split('/')[2]
        except KeyError:
            raise URLNotValidError("The URL provided does not"
                                   "include the tenant info")
            
        tenant = Tenant.objects.get(store_url=store_url)
        self.tenant_pk = str(tenant.pk)

    def clean(self):

        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:

            username = f"{self.tenant_pk}:{username}"
            
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password)
            
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class TenantUserCreationForm(auth_forms.UserCreationForm):

    store_url = forms.CharField(widget=forms.HiddenInput,
                                disabled=True)
    
    def save(self, commit=True):

        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.tenant = Tenant.objects.get(
            store_url=self.cleaned_data["store_url"])

        if commit:
            user.save()

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
        exclude = ['services_acq']


class DeveloperCreationForm(TenantUserCreationForm):

    class Meta(TenantUserCreationForm.Meta):
        model = models.Developer
        exclude = ['assigned_services']


class PlatformServiceForm(forms.Form):

    package = forms.FileField(
        label="Package file",
        help_text="Only APK and iPhone IPA packages are supported.",
    )

    descrp = forms.CharField(
        label="Description",
        required=False,
        help_text="Details specifically for the platform. Markdown markup available.",
        widget=forms.Textarea(attrs={"cols": 80, "rows": 20})
    )
    

class ServiceBasicInfoForm(forms.ModelForm):

    creator = forms.ModelChoiceField(
        widget=forms.HiddenInput,
        queryset=None,
        disabled=True,
        required=False,
    )

    developers = forms.ModelMultipleChoiceField(
        queryset=None,
        help_text="The selected developers can acces, "
        "modify and upload new versions to the service's packages.",
        required=False,
    )

    class Meta:
        model = models.Service
        exclude = ["icon", "datetime_published", "tenant", "n_downloads"]
        widgets = {
            "brief_descrp": forms.Textarea(attrs={"cols": 80, "rows": 10}),
            "descrp": forms.Textarea(attrs={"cols": 80, "rows": 20}),
        }
        

    def __init__(self, *args, **kwargs):
        """
        Set the querysets for the creator and developers field.

        The developers field should not include the developer
        who is creating the service. However, the creator field may
        be empty in case the service is being created by a tenant
        administrator, so all the developers must be included in the
        developers field.
        """

        super().__init__(*args, **kwargs)
        self.fields["creator"].queryset = models.Developer.objects.filter(
            tenant__store_url=self.initial["store_url"])
        
        self.fields["developers"].queryset = models.Developer.objects.filter(
            tenant__store_url=self.initial["store_url"])

        # The service is being created by a developer
        if self.initial["creator"]:
            self.fields["creator"].queryset = self.fields["creator"].queryset.filter(
                pk=self.initial["creator"])
            
            self.fields["developers"].queryset = self.fields["developers"].queryset.filter(~Q(pk=self.initial["creator"]))


class UpdateServiceForm(forms.ModelForm):

    class Meta:
        model = models.Service
        fields = [
            "name",
            "brief_descrp",
            "descrp",
        ]
        widgets = {
            "brief_descrp": forms.Textarea(attrs={"cols": 80, "rows": 10}),
            "descrp": forms.Textarea(attrs={"cols": 80, "rows": 20}),
        }


class UserUpdateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        """
        The username without the tenant id must be passed 
        as an initial value because there is no way
        to do it with the model in the code. It could be
        done in the template by explicitely calling the 
        get_username method, but the automatic creation of
        the form would be lost.
        """
        
        super().__init__(*args, **kwargs)
        self.initial["username"] = self.instance.get_username()

    
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
        ]


class UpdatePackageForm(forms.Form):

    changes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 20, "cols": 80}),
        help_text="Markdown markup available",
    )
    package = forms.FileField()
