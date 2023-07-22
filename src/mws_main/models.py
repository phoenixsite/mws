from djongo import models
import django.contrib.auth.models as auth_models
from django.core.validators import RegexValidator
from tenants.models import TenantAwareModel

import re


class VersionField(models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 9
        kwargs["validators"] =  [RegexValidator(
            r"^\d{1,2}\.\d{1,2}(.\d{1,2})?$",
            flags=re.ASCII)]
        super().__init__(*args, **kwargs)


class VersionEntry(models.Model):

    version = VersionField()
    upload_date = models.DateField()
    changes = models.TextField()

    class Meta:
        abstract = True


class Service(TenantAwareModel):

    serv_id = models.ObjectIdField()
    name = models.CharField(
        "service name",
        max_length=25,
        blank=False
    )
    last_version = VersionField()

    def repo_dir_path(instance, filename):
        """Return the path for a uploaded file within a service"""
        
        return f"repo_{instance.repo_id}/{instance.serv_id}/filename"
    
    package = models.FileField(repo_dir_path)
    package_type = models.CharField(
        max_length=3,
        choices=[
            ("APK", "Android Package (APK)"),
            ("IPA", "iOS App (IPA)"),
        ]
        
    )
    size = models.PositiveIntegerField()
    n_downloads = models.PositiveIntegerField("number of downloads")
    descrp = models.TextField("description")
    categories = models.JSONField()
    version_history = models.ArrayField(
        model_container=VersionEntry
    )
    

class Developer(auth_models.User, TenantAwareModel):

    dev_id = models.ObjectIdField()


class Client(auth_models.User, TenantAwareModel):

    client_id = models.ObjectIdField()
    services_acq = models.ArrayReferenceField(
        to=Service,
        on_delete=models.CASCADE,
    )
