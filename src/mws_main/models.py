from djongo import models
import django.contrib.auth.models as auth_models
from django.core.validators import RegexValidator
from tenants.models import TenantAwareModel, Tenant, get_user_group

import re


class VersionField(models.CharField):

    def __init__(self, **kwargs):
        
        kwargs["max_length"] = 9
        kwargs["validators"] = [RegexValidator(
            r"^\d{1,2}\.\d{1,2}(.\d{1,2})?$",
            flags=re.ASCII)]
        super().__init__(**kwargs)


class VersionEntry(models.Model):

    version = VersionField()
    upload_date = models.DateField()
    changes = models.TextField()

    class Meta:
        abstract = True


def repo_dir_path(instance, filename):
    """Return the path for a uploaded file within a service"""
    repo_addr = Tenant.objects.get(_id=instance.tenant._id).repo_addr
    return f"{repo_addr}/{instance.name}/{filename}"
    

class Service(TenantAwareModel):

    _id = models.ObjectIdField()
    name = models.CharField(
        "service name",
        max_length=25,
        blank=False
    )
    last_version = VersionField()

    package = models.FileField("package file", upload_to=repo_dir_path)
    package_type = models.CharField(
        max_length=3,
        choices=[
            ("APK", "Android Package (APK)"),
            ("IPA", "iOS App (IPA)"),])
    
    size = models.PositiveIntegerField()
    n_downloads = models.PositiveIntegerField("number of downloads", default=0)
    descrp = models.TextField("description")
    #categories = models.JSONField(default=list)
    version_history = models.ArrayField(
        model_container=VersionEntry)

    def save(self, *args, **kwargs):
        self.size = self.package.size
        super().save(*args, **kwargs)


DEV_GROUP = "developers"
CLIENT_GROUP = "clients"


def get_developer_group():
    """
    Return the group of the clients. If it doesn't exist, 
    it is created.
    """

    codenames = ['view_client', 'change_client',
                 'view_service']
        
    return get_user_group(DEV_GROUP, codenames)

        
class Developer(TenantAwareModel, auth_models.User):

    _id = models.ObjectIdField()


    def save(self, commit=True):

        super().save(commit)

        if commit:

            group = get_developer_group()
            self.groups.add(group)
            super().save()


def get_client_group():
    """
    Return the group of the developers. If it doesn't exist,
    it is created.
    """
    
    codenames = ['add_service', 'view_service',
                 'change_service', 'view_developer',
                 'change_developer']

    return get_user_group(CLIENT_GROUP, codenames)


class Client(TenantAwareModel, auth_models.User):

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
            super().save()
