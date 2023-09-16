from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage

import mws_main.utils as utils
from tenants.models import TenantAwareModel, Tenant, get_user_group, User

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

        
class Service(TenantAwareModel):
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


def get_nupdates(tenant_id):
    """
    Return the number of packages updates that has been made in a store.
    """
    # IMPLEMENT
    result = 0


def get_monthly_nupdates(tenant_id):
    """
    Return the number of packages updates that has been made in the
    current month.
    """

    # IMPLEMENT
    pass

def create_service(name, brief_descrp, descrp, packages, tenant, creator, developers):

    packages_objs = []
    icon = None

    service = Service.objects.create(
        name=name,
        brief_descrp=brief_descrp,
        descrp=descrp,
        tenant=tenant,
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
