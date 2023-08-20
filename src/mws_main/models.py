from djongo import models
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files import File
from tenants.models import TenantAwareModel, Tenant, get_user_group, User


from pyaxmlparser import APK
import biplist

import re
import zipfile

DEV_GROUP = "developers"
CLIENT_GROUP = "clients"

class DescriptionField(models.TextField):
    max_length = 1000
    blank = True
    help_text = "1000 characters max. Markdown markup available",
    

class VersionEntry(models.Model):

    version = models.CharField(max_length=25)
    update_date = models.DateField()
    changes = DescriptionField()

    class Meta:
        abstract = True


def store_dir_path(instance, filename):
    """Return the path for a uploaded file within a service"""
    store_url = Tenant.objects.get(_id=instance.tenant._id).store_url
    return f"{store_url}/{instance.name}/{filename}"


def image_dir_path(instance, filename):
    """Return the path for a uploaded file within a service"""
    store_url = Tenant.objects.get(_id=instance.tenant._id).store_url
    return f"{store_url}/{instance.name}/image/{filename}"


class Package(models.Model):

    n_package = models.AutoField(
        "package number",
        unique=True,
        help_text="Identify the package within the service. It is not considered "
        "as a primary key"
    )
    package_file = models.FileField("package file", upload_to=store_dir_path)
    package_type = models.CharField(
        max_length=3,
        choices=[
            ("APK", "Android Package (APK)"),
            ("IPA", "iOS App (IPA)"),])

    date_uploaded = models.DateField(auto_now_add=True)
    os_name = models.CharField("operative system's name", max_length=75)
    last_version = models.CharField(max_length=25)
    n_downloads = models.PositiveIntegerField("number of downloads", default=0)
    descrp = DescriptionField(
        "package description"
        help_text="Describes specific features of this package. For information "
        "related to the service, use the description field of the service."
    )
    version_history = models.ArrayField(
        model_container=VersionEntry)

    def size(self):
        return self.package_file.size

    def __str__(self):
        return f"{self.package_type} ({self.n_package})" 

    class Meta:
        abstract = True


class Service(TenantAwareModel):

    _id = models.ObjectIdField()
    name = models.CharField(
        "service name",
        max_length=25,
        blank=False
    )
    icon = models.ImageField(
        upload_to=image_dir_path,
        help_text="Service icon",
    )
    packages = models.ArrayField(
        model_container=Package)

    class Meta:
        permissions = [
            ("view_admin_service", "Can view detailed information of a service"),
        ]

    def __str__(self):
        return f"{self.name} ({self._id})"

    
    def new_acquirement(self, n_package, user):
        """
        Update the number of acquirements and downloads if a client has
        acquired the service and assign the client to this instance.

        :param tenants.models.User user: client who acquired the service.
        """
        pass
        """
        if user.groups.filter(name=CLIENT_GROUP).exists():

            #self.n_downloads = models.F("n_downloads") + 1
            self.n_downloads = self.n_downloads + 1
            
            if self not in user.services_acq.get_queryset():
                user.services_acq.add(self)

            self.save(update_fields=["n_downloads"])
        """

class InvalidPackage(Exception):
    pass

class PackageFile:

    IOS_INFO_FILE = "Info.plist"
    IOS_VALID_BUNDLE = "APPL"

    def __init__(self, package_file):

        self.zip_package = None
        self.icon_file = None

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
            self.os_name = "Android"
            self.version = pack_info.get_androidversion_name()
        else:

            info_filename = None

            # Search for the information file of the IPA format
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
            self.os_name = plist["CFBundleSupportedPlatforms"]
            self.icon_filename = plist["CFBundleIconFiles"][0]
            self.version = plist["CFBundleInfoDictionaryVersion"]

    def __str__(self):
        string = f"Type: {self.type}\n"
        string += f"App name: {self.app_name}\n"
        string += f"OS name: {self.os_name}\n"
        string += f"Icon filename: {self.icon_filename}\n"
        string += f"Version: {self.version}\n"
        return string

    def is_zip_opened(self):
        return self.zip_package is not None

    def open_zip(self):

        if not self.zip_package:
            self.zip_package = zipfile.ZipFile(self.package_file)

    def close_zip(self):

        if self.zip_package:
            self.zip_package.close()
            self.zip_package = None

    def open_icon(self):
        
        if not self.icon_file:
            self.open_zip()
            self.icon_file = self.zip_package.open(self.icon_filename)

    def close_icon(self):

        if self.icon_file:
            self.icon_file.close()
            self.icon_file = None

    def close(self):
        self.close_icon()
        self.close_zip()

    def to_dict(self):
        """
        Return a dict-like object with the attributes whose value
        is not None
        """

        d = {
            'name': self.app_name,
            'last_version': self.version,
            'package': self.package_file,
            'package_type': self.type,
        }

        if self.icon_filename:
            self.open_icon()    
            d['icon'] =  File(self.icon_file)
        
        if self.os_name:
            d['os_name'] = self.os_name

        return d


def create_service(package_file, descrp, store_url, commit):
    
    package = PackageFile(package_file)
    service = Service(
        descrp=descrp,
        **package.to_dict(),
    )
    service.tenant = Tenant.objects.get(
        store_url=store_url)

    service.save(commit)

    package.close()
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

    _id = models.ObjectIdField()
    assigned_services = models.ManyToManyField(Service)


    class Meta:
        permissions = [
            ("view_admin_developer", "Can view detailed information of a developer"),
        ]
    
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
    
    codenames = ['view_service', 'view_client', 'change_client']
    return get_user_group(CLIENT_GROUP, codenames)


class Client(User):
    """
    User who can access the store services and acquired
    them. Once acquired, they can download it whenever they want.
    """

    _id = models.ObjectIdField()
    services_acq = models.ArrayReferenceField(
        to=Service,
        on_delete=models.CASCADE,
        default=[]
    )

    class Meta:
        permissions = [
            ("view_admin_client", "Can view detailed information of a client"),
        ]

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
