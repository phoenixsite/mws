import django.forms as forms
from django.db.models import Q
import django.contrib.auth.models as auth_models
from django.contrib.auth import forms as auth_forms
from django.contrib.auth import authenticate
from mws_main import models

class AdminForm(auth_forms.UserCreationForm):

    class Meta:
        model = models.TenantAdmin
        fields = ['username',
                  'first_name',
                  'last_name',
                  'email',
                  ]

class ClientAdminForm(forms.ModelForm):
    
    class Meta:
        model = models.Client
        exclude = ['services_acq']


class URLNotValidError(Exception):
    pass


class AuthenticationForm(auth_forms.AuthenticationForm):
    """
    Form the user fill to authenticate in corresponding
    store.
    """

    def clean(self):

        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username is not None and password:
            
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password)
            
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class UserCreationForm(auth_forms.UserCreationForm):

    def save(self, commit=True):

        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user


    class Meta:
        model = None
        fields = ["username",
                  "first_name",
                  "last_name",
                  "email",]
        

class ClientCreationForm(UserCreationForm):
    
    class Meta(UserCreationForm.Meta):
        model = models.Client
        exclude = ['services_acq']


class DeveloperCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
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
        queryset=models.Developer.objects.all(),
        disabled=True,
        required=False,
    )

    developers = forms.ModelMultipleChoiceField(
        queryset=models.Developer.objects.all(),
        help_text="The selected developers can acces, "
        "modify and upload new versions to the service's packages.",
        required=False,
    )

    class Meta:
        model = models.Service
        exclude = ["icon", "datetime_published", "n_downloads"]
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
        model = auth_models.User
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


class ColURLField(forms.URLField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.required = False


class ColTextField(forms.CharField):
    
    def __init__(
            self, *, max_length=None, min_length=None, strip=True, empty_value="", **kwargs
    ):
        super().__init__(
            max_length=None, min_length=None, strip=True, empty_value="", **kwargs
        )
        self.required = False
        self.max_length = 50


    
class StoreMetadataForm(forms.Form):

    COLOR_CHOICES = [
        ("purple", "Purple"),
        ("red", "Red"),
        ("blue", "Blue"),
        ("yellow", "Yellow"),
    ]
    
    main_theme_color = forms.ChoiceField(
        choices=COLOR_CHOICES,
        #default="purple",
        help_text="Please pick a color for the main theme."
    )

    # First column
    footer_col1_title = ColTextField(
        label="Title of the first footer column",
    )

    footer_col1_row1_text = ColTextField(
        label="Text of the first row of the first footer column",
    )

    footer_col1_row1_url = ColURLField(
        label="Url of the first row of first footer column",
    )

    footer_col1_row2_text = ColTextField(
        label="Text of the second row of the first footer column",
    )

    footer_col1_row2_url = ColURLField(
        label="Url of the second row of first footer column",
    )

    footer_col1_row3_text = ColTextField(
        label="Text of the third row of the first footer column",
    )

    footer_col1_row3_url = ColURLField(
        label="Url of the third row of first footer column",
    )

    footer_col1_row4_text = ColTextField(
        label="Text of the fourth row of the first footer column",
    )

    footer_col1_row4_url = ColURLField(
        label="Url of the fourth row of first footer column",
    )

    footer_col1_row5_text = ColTextField(
        label="Text of the fifth row of the first footer column",
    )

    footer_col1_row5_url = ColURLField(
        label="Url of the fifth row of first footer column",
    )


    # Second column
    footer_col2_title = ColTextField(
        label="Title of the second footer column",
    )

    footer_col2_row1_text = ColTextField(
        label="Text of the first row of the second footer column",
    )

    footer_col2_row1_url = ColURLField(
        label="Url of the first row of second footer column",
    )

    footer_col2_row2_text = ColTextField(
        label="Text of the second row of the second footer column",
    )

    footer_col2_row2_url = ColURLField(
        label="Url of the second row of second footer column",
    )

    footer_col2_row3_text = ColTextField(
        label="Text of the third row of the second footer column",
    )

    footer_col2_row3_url = ColURLField(
        label="Url of the third row of second footer column",
    )

    footer_col2_row4_text = ColTextField(
        label="Text of the fourth row of the second footer column",
    )

    footer_col2_row4_url = ColURLField(
        label="Url of the fourth row of second footer column",
    )

    footer_col2_row5_text = ColTextField(
        label="Text of the fifth row of the second footer column",
    )

    footer_col2_row5_url = ColURLField(
        label="Url of the fifth row of second footer column",
    )


    # Third column
    footer_col3_title = ColTextField(
        label="Title of the first footer column",
    )

    footer_col3_row1_text = ColTextField(
        label="Text of the first row of the third footer column",
    )

    footer_col3_row1_url = ColURLField(
        label="Url of the first row of third footer column",
    )

    footer_col3_row2_text = ColTextField(
        label="Text of the second row of the third footer column",
    )

    footer_col3_row2_url = ColURLField(
        label="Url of the second row of third footer column",
    )

    footer_col3_row3_text = ColTextField(
        label="Text of the third row of the third footer column",
    )

    footer_col3_row3_url = ColURLField(
        label="Url of the third row of third footer column",
    )

    footer_col3_row4_text = ColTextField(
        label="Text of the fourth row of the third footer column",
    )

    footer_col3_row4_url = ColURLField(
        label="Url of the fourth row of third footer column",
    )

    footer_col3_row5_text = ColTextField(
        label="Text of the fifth row of the third footer column",
    )

    footer_col3_row5_url = ColURLField(
        label="Url of the fifth row of third footer column",
    )


    # Fourth column
    footer_col4_title = ColTextField(
        label="Title of the fourth footer column",
    )

    footer_col4_row1_text = ColTextField(
        label="Text of the first row of the fourth footer column",
    )

    footer_col4_row1_url = ColURLField(
        label="Url of the first row of fourth footer column",
    )

    footer_col4_row2_text = ColTextField(
        label="Text of the second row of the fourth footer column",
    )

    footer_col4_row2_url = ColURLField(
        label="Url of the second row of fourth footer column",
    )

    footer_col4_row3_text = ColTextField(
        label="Text of the third row of the fourth footer column",
    )

    footer_col4_row3_url = ColURLField(
        label="Url of the third row of fourth footer column",
    )

    footer_col4_row4_text = ColTextField(
        label="Text of the fourth row of the fourth footer column",
    )

    footer_col4_row4_url = ColURLField(
        label="Url of the fourth row of fourth footer column",
    )

    footer_col4_row5_text = ColTextField(
        label="Text of the fifth row of the fourth footer column",
    )

    footer_col4_row5_url = ColURLField(
        label="Url of the fifth row of fourth footer column",
    )

    def get_column(self, ncol):
        """
        Return the texts and urls in the column 'ncol'.
        """
        
        COLS = [
            [
                (self.cleaned_data["footer_col1_row1_text"],
                 self.cleaned_data["footer_col1_row1_url"]),
                
                (self.cleaned_data["footer_col1_row2_text"],
                 self.cleaned_data["footer_col1_row2_url"]),
                
                (self.cleaned_data["footer_col1_row3_text"],
                 self.cleaned_data["footer_col1_row3_url"]),
                
                (self.cleaned_data["footer_col1_row4_text"],
                 self.cleaned_data["footer_col1_row4_url"]),
                
                (self.cleaned_data["footer_col1_row5_text"],
                 self.cleaned_data["footer_col1_row5_url"]),
            ],
            [
                (self.cleaned_data["footer_col2_row1_text"],
                 self.cleaned_data["footer_col2_row1_url"]),
                
                (self.cleaned_data["footer_col2_row2_text"],
                 self.cleaned_data["footer_col2_row2_url"]),
                
                (self.cleaned_data["footer_col2_row3_text"],
                 self.cleaned_data["footer_col2_row3_url"]),
                
                (self.cleaned_data["footer_col2_row4_text"],
                 self.cleaned_data["footer_col2_row4_url"]),
                
                (self.cleaned_data["footer_col2_row5_text"],
                 self.cleaned_data["footer_col2_row5_url"]),
            ],
            [
                (self.cleaned_data["footer_col3_row1_text"],
                 self.cleaned_data["footer_col3_row1_url"]),
                
                (self.cleaned_data["footer_col3_row2_text"],
                 self.cleaned_data["footer_col3_row2_url"]),
                
                (self.cleaned_data["footer_col3_row3_text"],
                 self.cleaned_data["footer_col3_row3_url"]),
                
                (self.cleaned_data["footer_col3_row4_text"],
                 self.cleaned_data["footer_col3_row4_url"]),
                
                (self.cleaned_data["footer_col3_row5_text"],
                 self.cleaned_data["footer_col3_row5_url"]),
            ],
            [
                (self.cleaned_data["footer_col4_row1_text"],
                 self.cleaned_data["footer_col4_row1_url"]),
                
                (self.cleaned_data["footer_col4_row2_text"],
                 self.cleaned_data["footer_col4_row2_url"]),
                
                (self.cleaned_data["footer_col4_row3_text"],
                 self.cleaned_data["footer_col4_row3_url"]),
                
                (self.cleaned_data["footer_col4_row4_text"],
                 self.cleaned_data["footer_col4_row4_url"]),
                
                (self.cleaned_data["footer_col4_row5_text"],
                 self.cleaned_data["footer_col4_row5_url"]),
            ],
        ]

        if ncol not in range(len(COLS)):
            return None

        return COLS[ncol]

    def has_footer_col(self, ncol):
        """
        Check if there are any non-null or non-empty text items in the
        column 'ncol'.
        """
        
        col = self.get_column(ncol)
        return any([row[0] for row in col])

    def has_footer(self):
        """Check if there are data in any of the columns."""
        return any([self.has_footer_col(ncol) for ncol in range(4)])

    def get_non_empty_cols(self):
        return [(self.get_title(ncol), self.get_non_empty_rows(ncol)) for ncol in range(4) if self.has_footer_col(ncol)]
    
    def get_non_empty_rows(self, ncol):
        """Return the non-null or non-empty items of column 'ncol'."""
        col = self.get_column(ncol)
        return [row for row in col if row[0]]

    def get_title(self, ncol):
        """Return the title of the column 'ncol'."""
        TITLES = [
            self.cleaned_data["footer_col1_title"],
            self.cleaned_data["footer_col2_title"],
            self.cleaned_data["footer_col3_title"],
            self.cleaned_data["footer_col4_title"],
        ]

        if ncol not in range(len(TITLES)):
            return None
        return TITLES[ncol]
