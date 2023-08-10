from djongo import models
from django.core.validators import RegexValidator
from tenants.models import TenantAwareModel, Tenant, get_user_group, TenantUser

from pyaxmlparser import APK
import biplist

import re
import zipfile

DEV_GROUP = "developers"
CLIENT_GROUP = "clients"


class VersionEntry(models.Model):

    version = models.CharField(max_length=25)
    update_date = models.DateField()
    changes = models.TextField()

    class Meta:
        abstract = True


def repo_dir_path(instance, filename):
    """Return the path for a uploaded file within a service"""
    repo_addr = Tenant.objects.get(_id=instance.tenant._id).repo_addr
    return f"{repo_addr}/{instance.name}/{filename}"


def image_dir_path(instance, filename):
    """Return the path for a uploaded file within a service"""
    repo_addr = Tenant.objects.get(_id=instance.tenant._id).repo_addr
    return f"{repo_addr}/{instance.name}/image/{filename}"


class Service(TenantAwareModel):

    _id = models.ObjectIdField()
    name = models.CharField(
        "service name",
        max_length=25,
        blank=False
    )
    icon = models.ImageField(upload_to=image_dir_path)

    package = models.FileField("package file", upload_to=repo_dir_path)
    package_type = models.CharField(
        max_length=3,
        choices=[
            ("APK", "Android Package (APK)"),
            ("IPA", "iOS App (IPA)"),])

    date_uploaded = models.DateField()

    os_version = models.CharField("operative system version", max_length=50)
    os_name = models.CharField("operative system's name", max_length=75)
    last_version = models.CharField(max_length=25)

    n_downloads = models.PositiveIntegerField("number of downloads", default=0)
    
    descrp = models.TextField(
        "description",
        help_text="1000 characters max. Markdown markup available",
    )
    
    version_history = models.ArrayField(
        model_container=VersionEntry)

    def save(
            self,
            force_insert=False,
            force_update=False,
            using=None,
            update_fields=None
    ):        
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    
    def new_acquirement(self, user):
        """
        Update the number of acquirements if a client has
        acquired the service package and assign the client
        this instance.

        :param django.contrib.auth.model.User user: client
        who acquired the service.
        """

        if user.groups.filter(name=CLIENT_GROUP).exists():

            self.n_downloads = models.F("n_downloads") + 1

            if self not in user.services_acq.get_queryset():
                user.services_acq.add(self)

            self.save(update_fields=["n_downloads"])


class InvalidPackage(Exception):
    pass

class Package:

    IOS_INFO_FILE = "Info.plist"
    IOS_VALID_BUNDLE = "APPL"

    def __init__(self, package_file):

        if not package_file:
            raise FileNotFoundError("A file must be provided to create a package object.")
            
        if not zipfile.is_zipfile(package_file):
            raise InvalidPackage("The package is not a ZIP file.")

        self.package_file = package_file

        # Identify the package type (APK or IPA)
        # Both are zips internally, so we if there is an
        # AndroidManifest.xml file, it is probably an
        # Android package.
        pack_info = APK(self.package_file)

        if pack_info.is_valid_APK():
            
            self.metadata = pack_info        
            self.type = "APK"
            self.app_name = pack_info.get_app_name()
            self.icon_filename = pack_info.get_app_icon()
            self.package_name = pack_info.get_package()
            self.os_version = pack_info.get_min_sdk_version()
            self.os_name = "Android"
            self.version = pack_info.get_androidversion_code()
        else:

            info_filename = None

            with zipfile.ZipFile(self.package_file, 'r') as zip_package:
                pattern = re.compile(f".*/?{self.IOS_INFO_FILE}")
                
                # Look for the package information file
                for filename in zip_package.namelist():

                    if pattern.fullmatch(filename):
                        info_filename = zip_package.open(filename)
                        break

                if not info_filename:
                    raise InvalidPackage("The package uploaded is not supported.")

            plist = biplist.readPlist(info_filename)

            
            if (plist["CFBundlePackageType"]
                and plist["CFBundlePackageType"] != self.IOS_VALID_BUNDLE):
                raise InvalidPackage("The package uploaded is not supported")

            self.metadata = plist
            self.type = "IPA"
            self.app_name = plist["CFBundleDisplayName"]
            self.os_version = plist["DTPlatformVersion"]
            self.os_name = plist["CFBundleSupportedPlatforms"]
            self.icon_filename = plist["CFBundleIconFiles"][0]
            self.version = plist["CFBundleInfoDictionaryVersion"]

    def __str__(self):
        string = f"Type: {self.type}\n"
        string += f"App name: {self.app_name}\n"
        string += f"OS version: {self.os_version}\n"
        string += f"OS name: {self.os_name}\n"
        string += f"Icon filename: {self.icon_filename}\n"
        string += f"Version: {self.version}\n"
        return string


def create_service(package_file, descrp):
    
    package = Package(package_file)
    return Service(
        name=package.app_name,
        last_version=package.version,
        package=package_file,
        package_type=package.type,
        descrp=descrp,
    )
        

def get_developer_group():
    """
    Return the group of the clients. If it doesn't exist, 
    it is created.
    """

    codenames = ['view_client', 'change_client',
                 'view_service']
        
    return get_user_group(DEV_GROUP, codenames)

        
class Developer(TenantUser):
    """
    User who can access to the repository services and
    modify their information, upload new versions and
    create new services
    """

    _id = models.ObjectIdField()
    assigned_services = models.ManyToManyField(Service)

    
    def save(self, commit=True):

        super().save(commit)
        
        if commit:

            group = get_developer_group()
            self.groups.add(group)


def get_client_group():
    """
    Return the group of the developers. If it doesn't exist,
    it is created.
    """
    
    codenames = ['add_service', 'view_service',
                 'change_service', 'view_developer',
                 'change_developer']

    return get_user_group(CLIENT_GROUP, codenames)


class Client(TenantUser):
    """
    User who can access the repository services and acquired
    them. Once acquired, they can download it whenever they want.
    """

    _id = models.ObjectIdField()
    services_acq = models.ArrayReferenceField(
        to=Service,
        on_delete=models.CASCADE,
        default=[]
    )

    def save(self, commit=True):

        super().save(commit)

        if commit:

            group = get_client_group()
            self.groups.add(group)

    def has_services(self):
        return self.services_acq.get_queryset()
    
    def get_services(self):

        if not self.services_acq:
            return list()

        return list(self.services_acq.get_queryset())
