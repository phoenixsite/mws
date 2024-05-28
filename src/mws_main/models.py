import os
import datetime

from django.apps import apps
from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
import django.contrib.auth.models as auth_models

import mws_main.utils as utils
from tenants.middlewares import get_current_db_name


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
    Store the a version change of a package.
    """

    version = models.CharField(max_length=25)
    update_date = models.DateField(auto_now_add=True)
    changes = DescriptionField("changes description")
    package = models.ForeignKey("Package", on_delete=models.CASCADE)


def store_dir_path(instance, filename):
    """Return the path for a uploaded file within a service"""
    filename = os.path.split(filename)[-1]
    return f"{get_current_db_name()}/{instance.service.name}/{filename}"

def image_dir_path(instance, filename):
    """Return the path for a uploaded file within a service"""
    return f"{get_current_db_name()}/{instance.name}/image/{filename}"


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

        If the package hasn't been updated yet, it creates a version `
        entry for the initial package and another for the current
        update. 

        :param package_file: File-like object containing the file.
        :param changes: Description of the included changes in the
        package.
        :type changes: str
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

    n_downloads = models.PositiveIntegerField("number of downloads", default=0)

    class Meta:
        permissions = [
            ("view_admin_service", "Can view detailed information of a service"),
        ]

    def __str__(self):
        return f"{self.name} ({self.pk})"
    
    def new_acquirement(self, user, is_client):
        """
        Increase the number of acquirements and assign the service to
        the client.

        If `user` is not a client, the number of downloads isn't
        increased nor assigned.

        :param user: client who acquired the service.
        :type user: Client
        :param is_client: Indicate if `user` is a client.
        :type is_client: boolean
        """

        if is_client:

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


class TenantAdmin(auth_models.User):
    """
    Administrator of a tenant. It's the only user who can manage
    the core information of its tenant. 
    """

    # Must be synchronised with the admin group
    # name 003_auto migration file
    group_name = "admins"

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if not self.groups.filter(name=self.__class__.group_name).exists():
            group = auth_models.Group.objects.get(name=self.__class__.group_name)
            self.groups.add(group)


class Developer(auth_models.User):
    """
    User who can access to the store services and
    modify their information, upload new versions and
    create new services
    """
    
    # Must be synchronised with the admin group
    # name 003_auto migration file
    group_name = "developers"
    
    assigned_services = models.ManyToManyField(Service)

    class Meta:
        permissions = [
            ("view_admin_developer",
             "Can view detailed information of a developer"),
        ]
    
    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if not self.groups.filter(name=self.__class__.group_name).exists():
            group = auth_models.Group.objects.get(name=self.__class__.group_name)
            self.groups.add(group)


class Client(auth_models.User):
    """
    User who can access the store services and acquired
    them. Once acquired, they can download it whenever they want.
    """

    # Must be synchronised with the admin group
    # name 003_auto migration file
    group_name = "clients"
    
    services_acq = models.ManyToManyField(Service)

    class Meta:
        permissions = [
            ("view_admin_client",
             "Can view detailed information of a client"),
        ]

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if not self.groups.filter(name=self.__class__.group_name).exists():
            group = auth_models.Group.objects.get(name=self.__class__.group_name)
            self.groups.add(group)

    def has_services(self):
        return self.services_acq.get_queryset()
    
    def get_services(self):

        if not self.services_acq:
            return list()

        return list(self.services_acq.get_queryset())

    
class Metadata(models.Model):

    FOOT_FIELD = "footer"
    MAIN_THEME_FIELD = "main_theme_color"
    TITLE_FIELD = "title"
    ROWS_FIELD = "rows"
    URL_FIELD = "url"
    TEXT_FIELD = "text"

    # The value on this field should have this structure:
    #{
    #    "main_theme_color":,
    #	 "footer": [
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

    #{
    #    "2024-05-24": 2223212,
    #    "2024-05-25": 761128,
    #    ...
    #}
    download_bandwidth = models.JSONField()

    def date_key():
        """Return today's string date for using it as a JSON key"""
        return datetime.date.today().isoformat()

    def downloaded_package(self, size):
        self.download_bandwidth[self.__class__.date_key()] += size
        self.save(update_fields=["download_bandwidth"])
