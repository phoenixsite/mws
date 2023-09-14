from djongo import models
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage

import mws_main.utils as utils
from tenants.models import TenantAwareModel, Tenant, get_user_group, User

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
    update_date = models.DateField()
    changes = DescriptionField("changes description")

    class Meta:
        abstract = True


def store_dir_path(instance, filename):
    """Return the path for a uploaded file within a service"""
    store_url = Tenant.objects.get(_id=instance.tenant._id).store_url
    return f"{store_url}/{instance.name}/{filename}"

class Object(object):
    """Class used to set arbitrary attributes"""
    pass


def abstract_store_dir_path(tenant, name, filename):

    instance = Object()
    instance.tenant = tenant
    instance.name = name
    return store_dir_path(instance, filename)

def image_dir_path(instance, filename):
    """Return the path for a uploaded file within a service"""
    store_url = Tenant.objects.get(_id=instance.tenant._id).store_url
    return f"{store_url}/{instance.name}/image/{filename}"


class Package(models.Model):
    """
    Represent a package file that can be downloaded and used.

    Because of the abstract behaviour of the model, all the fields options
    will not be checked, so the function
    that initialize a package must manually checked that the options
    are valid.
    """

    n_package = models.BigIntegerField(
        "package number",
        help_text="Identify the package in a service.",
    )
    
    name = models.CharField(
        "package name",
        max_length=30,
        blank=False,
    )

    package_file = models.FileField("package file", upload_to=store_dir_path)
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

    version_history = models.ArrayField(
        model_container=VersionEntry,
        help_text="Previous uploaded versions and its changes",
    )

    def __str__(self):
        return f"{self.package_type} ({self.n_package})" 

    class Meta:
        abstract = True


class PackageNotFoundError(Exception):
    pass
        
class Service(TenantAwareModel):
    """
    Represent a software component that offer grouped functionalities.

    A service may be executed in multiple platforms or limit their functionalities,
    so it may contain multiple packages.
    """

    _id = models.ObjectIdField()
    name = models.CharField(
        "service name",
        max_length=25,
        blank=False
    )

    brief_descrp = models.TextField(
        "brief description",
        blank=False,
    )

    descrp = models.TextField(
        "description",
        blank=False,
    )

    icon = models.ImageField(
        upload_to=image_dir_path,
        help_text="Copied from the first package icon.",
    )

    datetime_published = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the service was firstly published."
    )
    
    packages = models.ArrayField(
        model_container=Package,
        default=[],
        help_text="Concrete software packages contained by the service."
    )

    objects = models.DjongoManager()

    # This field is in Service and not in Package because as Package is an abstract
    # model we cannot avoid race conditions when incrementing the number of downloads
    # of a Package instance and updating the whole packages array of a Service is
    # too expensive
    n_downloads = models.PositiveIntegerField("number of downloads", default=0)

    autoid_for_packages = models.BigIntegerField(
        help_text="Last id used to create a package within the service.",
    )

    class Meta:
        permissions = [
            ("view_admin_service", "Can view detailed information of a service"),
        ]

    def __str__(self):
        return f"{self.name} ({self._id})"

    def update_package(self, npackage, package_file, changes):
        """
        Upload a new version of a package of the current service.

        :param npackage: Number of the updated package.
        :param package_file: File-like object containing the file.
        :param changes: Description of the included changes in the package.
        """

        package = self.packages[npackage]
        parsed_package = utils.ParsedPackage(package_file)
        package.update(parsed_package.to_dict())
        
        # This is a dangerous operation because the packages files
        # are being saved before creating the service
        path = abstract_store_dir_path(self.tenant, self.name, parsed_package.package_name)
        path = default_storage.generate_filename(path)
        package["package_file"] = default_storage.save(path, parsed_package.file)
        
        new_version_entry = {
            'version': package["last_version"],
            'update_date': timezone.now(),
            'changes': changes,
        }

        new_history = [new_version_entry]

        if not package["version_history"]:

            package["version_history"] = []

            initial_version_entry = {
                'version': package["last_version"],
                'update_date': self.datetime_published,
                'changes': "Initial upload."
            }
            new_history = [new_version_entry, initial_version_entry]

        # Version history should behave like a stack, so the
        # newer updates appear first
        print(package["version_history"])
        new_history.extend(package["version_history"])
        package["version_history"] = new_history
        
        self.packages[npackage] = package
        self.save()
    
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
    
    # unwind to deconstruct the packages array of every service
    # project to get only the versions array of each package
    # group to count the array of versions array
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$unwind": "$packages"},
        {"$project": {"versions": "$packages.version_history"}},
        {"$group": {"_id": None, "updates": {
            "$sum": {"$size": "$versions"}
        }}}
    ]

    result = list(Service.objects.mongo_aggregate(pipeline))

    if result:
        return result[0]["updates"]
    else:
        return 0

def get_monthly_nupdates(tenant_id):
    """
    Return the number of packages updates that has been made in the
    current month.
    """

    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$unwind": "$packages"},
        {"$project": {"versions": "$packages.version_history"}},
        {"$unwind": "$versions"},
        {"$match": {"$expr": {"$eq": [{"$month": "$versions.update_date"}, {"$month": timezone.now()}]}}},
        {"$group": {"_id": None, "updates": {
            "$sum": 1
        }}}
    ]

    result = list(Service.objects.mongo_aggregate(pipeline))

    if result:
        return result[0]["updates"]
    else:
        return 0
    

def create_service(name, brief_descrp, descrp, packages, tenant, creator, developers):

    packages_objs = []
    icon = None

    for n_package, package in enumerate(packages):

        # Due to a package is an abstract class, we must fill manually all its
        # fields, even the file field (storage class interaction)
        parsed_package = utils.ParsedPackage(package["package"])
        package_obj = parsed_package.to_dict()
        package_obj["descrp"] = package["descrp"]
        package_obj["date_uploaded"] = timezone.now()
        package_obj["version_history"] = []
        package_obj["n_package"] = n_package

        # This is a dangerous operation because the packages files
        # are being saved before creating the service
        path = abstract_store_dir_path(tenant, name, parsed_package.package_name)
        path = default_storage.generate_filename(path)
        package_obj["package_file"] = default_storage.save(path, parsed_package.file)
        packages_objs.append(package_obj)

        if not icon:
            icon = parsed_package.get_icon()
    
    service = Service.objects.create(
        name=name,
        icon=icon,
        brief_descrp=brief_descrp,
        descrp=descrp,
        tenant=tenant,
        packages=packages_objs,
        autoid_for_packages=len(packages_objs),
    )

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

    _id = models.ObjectIdField()
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

    _id = models.ObjectIdField()
    services_acq = models.ArrayReferenceField(
        to=Service,
        on_delete=models.CASCADE,
        default=[],
        help_text="""An acquisition can be defined as the first time a"""\
        """service is downloaded."""
    )

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
