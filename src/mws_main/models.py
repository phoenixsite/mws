from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
import django.contrib.auth.models as auth_models
from django.contrib.auth.validators import UnicodeUsernameValidator

import mws_main.utils as utils

import os

DEV_GROUP = "developers"
CLIENT_GROUP = "clients"

class DescriptionField(models.TextField):
    """
    Large text field used to create a description.

    It allows Markdown markup.
    """
    
    max_length = 1000
    blank = True
    help_text = "1000 characters max. Markdown markup available",


class VersionEntry(models.Model):
    """
    A field for storing a package version change.
    """

    version = models.CharField(max_length=25)
    update_date = models.DateField(auto_now_add=True)
    changes = DescriptionField("changes description")
    package = models.ForeignKey("Package", on_delete=models.CASCADE)


def store_dir_path(instance, filename):
    """Return the path for a uploaded file within a service"""
    store_url = Tenant.objects.get(pk=instance.service.tenant.pk).store_url
    filename = os.path.split(filename)[-1]
    return f"{store_url}/{instance.service.name}/{filename}"

def image_dir_path(instance, filename):
    """Return the path for a uploaded file within a service"""
    store_url = Tenant.objects.get(pk=instance.tenant.pk).store_url
    return f"{store_url}/{instance.name}/image/{filename}"


class Package(models.Model):
    """
    Represent a package file that can be downloaded and used.
    """
    
    name = models.CharField(
        "package name",
        max_length=60,
        blank=False,
    )

    package_file = models.FileField(
        "package file",
        max_length=150,
        upload_to=store_dir_path,
    )
    size = models.BigIntegerField(help_text="Package size")
    package_type = models.CharField(
        max_length=3,
        choices=[
            ("APK", "Android Package (APK)"),
            ("IPA", "iOS App (IPA)"),
        ]
    )

    date_uploaded = models.DateField(
        auto_now_add=True,
        help_text="Date when the package was firstly uploaded.",
    )

    os_name = models.CharField("operative system's name", max_length=75)
    last_version = models.CharField(max_length=25)
    descrp = DescriptionField(
        "package description",
        help_text="Describes specific features of this package. For information "
        "related to the service, use the description field of the service.",
        default="",
    )
    service = models.ForeignKey("Service", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.package_type} ({self.pk})"

    def update_package(self, package_file, changes):
        """
        Upload a new version of the current package.

        :param package_file: File-like object containing the file.
        :param changes: Description of the included changes in the package.
        """

        if not self.versionentry_set.all().exists():

            VersionEntry.objects.create(
                version=self.last_version,
                update_date=self.service.datetime_published,
                changes="Initial upload.",
                package=self,
            )

        parsed_package = utils.ParsedPackage(package_file)

        VersionEntry.objects.create(
            version=parsed_package.version,
            changes=changes,
            package=self,
        )

        parsed_dict = parsed_package.to_dict()
        self.size = parsed_dict["size"]
        self.package_file = parsed_package.file
        self.os_name = parsed_dict["os_name"]
        self.last_version = parsed_dict["last_version"]
        self.save()


class PackageNotFoundError(Exception):
    pass

        
class Service(models.Model):
    """
    Represent a software component that offer grouped functionalities.

    A service may be executed in multiple platforms or limit their functionalities,
    so it may contain multiple packages.
    """

    name = models.CharField(
        "service name",
        max_length=25,
        blank=False
    )

    brief_descrp = models.TextField(
        "brief description",
        blank=False,
        help_text="Brief description of the service (What is and main function)",
    )

    descrp = models.TextField(
        "description",
        blank=False,
        help_text="General description of the service. Markdown markup available.",
    )

    icon = models.ImageField(
        upload_to=image_dir_path,
        help_text="Copied from the first package icon.",
    )

    datetime_published = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the service was firstly published."
    )

    # This field is in Service and not in Package because as Package is an abstract
    # model we cannot avoid race conditions when incrementing the number of downloads
    # of a Package instance and updating the whole packages array of a Service is
    # too expensive
    n_downloads = models.PositiveIntegerField("number of downloads", default=0)

    class Meta:
        permissions = [
            ("view_admin_service", "Can view detailed information of a service"),
        ]

    def __str__(self):
        return f"{self.name} ({self.pk})"
    
    def new_acquirement(self, user):
        """
        Update the number of acquirements and downloads if a client has
        acquired the service and assign the client to this instance.

        :param tenants.models.User user: client who acquired the service.
        """

        if user.groups.filter(name=CLIENT_GROUP).exists():

            self.n_downloads = models.F("n_downloads") + 1
            
            if self not in user.services_acq.get_queryset():
                user.services_acq.add(self)

            self.save(update_fields=["n_downloads"])


def get_nupdates():
    """
    Return the number of packages updates that has been made in a store.
    """
    return VersionEntry.objects.all().count()


def get_monthly_nupdates():
    """
    Return the number of packages updates that has been made in the
    current month.
    """
    
    return VersionEntry.objects.filter(update_date__month=timezone.now().month).count()
    

def create_service(name, brief_descrp, descrp, packages, creator, developers):

    packages_objs = []
    icon = None

    service = Service.objects.create(
        name=name,
        brief_descrp=brief_descrp,
        descrp=descrp,
    )

    for package in packages:

        parsed_package = utils.ParsedPackage(package["package"])

        Package.objects.create(
            name=parsed_package.package_name,
            last_version=parsed_package.version,
            size=parsed_package.size,
            package_type=parsed_package.type,
            os_name=parsed_package.os_name,
            descrp=package["descrp"],
            package_file=parsed_package.file,
            service=service,
        )

        if not icon:
            icon = parsed_package.get_icon()

    service.icon = icon
    service.save(update_fields=["icon"])

    if creator:
        creator.assigned_services.add(service)

    for developer in developers:
        developer.assigned_services.add(service)

    return service


class UserManager(BaseUserManager):

    use_in_migrations = True
    
    def create_user(self, username, email, password=None, **extra_fields):

        if not username:
            raise ValueError("The given username must be set")
    
        email = self.normalize_email(email)

        # Inspired by the original Django UserManager
        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        username = GlobalUserModel.normalize_username(username)
        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser():
        """Superusers has not been established in the app."""
        pass


class User(AbstractBaseUser, auth_models.PermissionsMixin):
    """
    Represents a user that is associated with one and
    only one tenant. Its username is composed of the 
    tenant id and a typical username separated by two dots (:).

    With this approach, users with the
    same username can exist if they are in different tenants,
    ensuring tenant isolation.
    """

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 75 characteres or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last_name"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), blank=True)
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active."
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def get_full_name(self):
        """
        Return the first name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
        
    def get_username(self):
        return self.username

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_username()})"


def get_user_group(group_name, codenames=None):
    """
    Return the group of the users whose model is given.

    If it doesn't exist, it is created.

    :param str group_name: Name of the group.
    :param list codenames: Permission codenames which will be
    included in the permissions group. It is ignored if the
    group is already created.
    """

    try:
        group = auth_models.Group.objects.get_by_natural_key(group_name)
    except auth_models.Group.DoesNotExist:

        permissions = auth_models.Permission.objects.filter(
            codename__in=codenames)

        group = auth_models.Group.objects.create(name=group_name
)
        group.permissions.add(*permissions)
        group.save()

    return group


ADMIN_GROUP = "admin"

def get_admin_group():
    """
    Return the group of the administrators. If doesn't exist, 
    it is created.
    """

    codenames = ["add_service",
                 "view_service",
                 "view_admin_service",
                 "change_service",
                 "delete_service",
                 "add_developer",
                 "view_developer",
                 "view_admin_developer",
                 "change_developer",
                 "delete_developer",
                 "add_client",
                 "view_client",
                 "view_admin_client",
                 "change_client",
                 "delete_client",
                 "view_tenant",
                 "change_tenant",]
    return get_user_group(ADMIN_GROUP, codenames)


class TenantAdmin(User):
    """
    Administrator of a tenant. It's the only user who can manage
    the core information of its tenant. 
    """

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)
        group = get_admin_group()

        if not self.groups.filter(name=group.name).exists():
            self.groups.add(group)

def get_developer_group():
    """
    Return the group of the clients. If it doesn't exist, 
    it is created.
    """

    codenames = ['view_client', 'view_service', 'view_admin_service',
                 'add_service', 'change_service', 'view_developer',
                 'change_developer']
        
    return get_user_group(DEV_GROUP, codenames)


class Developer(User):
    """
    User who can access to the store services and
    modify their information, upload new versions and
    create new services
    """

    assigned_services = models.ManyToManyField(Service)

    class Meta:
        permissions = [
            ("view_admin_developer", "Can view detailed information of a developer"),
        ]
    
    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)
        group = get_developer_group()

        if not self.groups.filter(name=group.name).exists():
            self.groups.add(group)


def get_client_group():
    """
    Return the group of the developers. If it doesn't exist,
    it is created.
    """
    
    codenames = ['view_service', 'view_client', 'change_client']
    return get_user_group(CLIENT_GROUP, codenames)


class Client(User):
    """
    User who can access the store services and acquired
    them. Once acquired, they can download it whenever they want.
    """

    services_acq = models.ManyToManyField(Service)

    class Meta:
        permissions = [
            ("view_admin_client", "Can view detailed information of a client"),
        ]

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)
        group = get_client_group()

        if not self.groups.filter(name=group.name).exists():
            self.groups.add(group)

    def has_services(self):
        return self.services_acq.get_queryset()
    
    def get_services(self):

        if not self.services_acq:
            return list()

        return list(self.services_acq.get_queryset())


class Metadata(models.Model):

    # The value on this field should have this structure:
    #{
    #    "main_theme_color":,
    #	"footer": [
    #		{
    #               "title": "Title1",
    #		    "rows": [
    #                   {
    #			    "text": "This is row1",
    #			    "url": ,
    #			},
    #			{
    #			    "text": "This is row2",
    #			    "url": ,
    #			},
    #			...
    #		    ]
    #		},
    #		{
    #		    "title": "Title1",
    #		    "rows": [
    #			{
    #			    "text": "This is row1",
    #			    "url": ,
    #			},
    #			{
    #			    "text": "This is row2",
    #			    "url": ,
    #			},
    #			...
    #		    ]
    #		},
    #		...		
    #	]
    #}
    #
    appearance_metadata = models.JSONField()
