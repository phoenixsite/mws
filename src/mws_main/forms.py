import django.forms as forms
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from mws_main import models
from tenants.models import Tenant, TenantUser

from bson import ObjectId


class SelectMongoObject(forms.Select):

    def value_from_datadict(self, data, files, name):
        return ObjectId(data.get(name))
    
    
class MongoObjectChoiceField(forms.ModelChoiceField):
    widget = SelectMongoObject


class ClientAdminForm(forms.ModelForm):

    tenant = MongoObjectChoiceField(
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
    repository.
    """

    def __init__(self, request=None, *args, **kwargs):

        super().__init__(request, *args, **kwargs)

        try:
            repo_addr = request.path.split('/')[2]
        except KeyError:
            raise URLNotValidError("The URL provided does not"
                                   "include the tenant info")
            
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
        exclude = ['tenant', 'assigned_services']


class ModelMultipleChoiceField(forms.ModelMultipleChoiceField):

    def prepare_value(self, value):
        if value and hasattr(value, "__iter__"):
            return [ObjectId(v) for v in value]
        else:
            return super().prepare_value(value)
    

class ServiceCreationForm(forms.ModelForm):
    
    repo_addr = forms.CharField(
        widget=forms.HiddenInput,
        disabled=True,
    )

    package = forms.FileField(
        label="Package file",
        help_text="Only APK and iPhone IPA packages supported.",
    )

    creator = forms.ModelChoiceField(
        widget=forms.HiddenInput,
        queryset=None,
        disabled=True,
        required=False,
    )

    developers = ModelMultipleChoiceField(
        queryset=None,
        help_text="The selected developers can acces, "
        "modify and upload new versions to the service",
    )

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.fields["creator"].queryset = models.Developer.objects.filter(tenant__repo_addr=self.initial["repo_addr"])
        self.fields["developers"].queryset = models.Developer.objects.filter(tenant__repo_addr=self.initial["repo_addr"])

    def save(self, commit=True):

        service = models.create_service(
            self.cleaned_data["package"],
            self.cleaned_data["descrp"],
        )
        service.tenant = Tenant.objects.get(
            repo_addr=self.cleaned_data["repo_addr"])

        service.save(commit)

        if commit:
            # Assign the service to the developer creator and
            # the selected developers
            if self.cleaned_data["creator"]:
                self.cleaned_data["creator"].assigned_services.add(service)
                for developer in self.cleaned_data["developers"]:
                    developer.assigned_services.add(service)

    class Meta:
        model = models.Service
        fields = ["descrp"]


class UserUpdateForm(forms.ModelForm):

    template_name = "mws_main/update_user.html"

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

    def save(self, commit=True):
        """
        Save the user in the DB.
        
        It first checks if the data has changed to avoid
        unnecessary DB access.
        """

        if self.has_changed():
            return super().save(commit)
        else:
            return self.instance
    
    class Meta:
        model = TenantUser
        fields = ["username",
                  "first_name",
                  "last_name",
                  "email",
                  ]
