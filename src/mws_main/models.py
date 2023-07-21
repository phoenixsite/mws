from djongo import models
import django.contrib.auth.models as auth_models
from django.core.validators import RegexValidator

import re

IRESOURCES = [
    ("CT", "CPU time"),
    ("ST", "Storage usage"),
]

class IResourceUsage(models.Model):

    res_name = models.CharField(
        "resource name",
        max_length=2,
        choices=IRESOURCES
    )

    class Meta:
        abstract = True

class SubsLoup(models.Model):

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    charge = models.DecimalField("money charge", decimal_places=3)
    usages = models.ArrayField(
        model_container=IResourceUsage
    )

    class Meta:
        abstract = True


class IResourcePlan(models.Model):

    res_name = models.CharField(
        "resource name",
        max_length=2,
        choices=IRESOURCES
    )

    limit = models.DecimalField("maximum usage", decimal_places=3)
    charge_per_unit = models.DecimalField(decimal_places=3)

    class Meta:
        abstract = True

class SubsAgreement(models.Model):

    date_regs = models.DateTimeField(
        "registration date",
        auto_now_add=True
    )
    end_date = models.DateTimeField()
    card_number = models.CharField(max_length=100, blank=False)
    plans = models.ArrayField(
        model_container=IResourcePlan
    )

    current_loup = models.EmbeddedField(
        model_container=SubsLoup
    )

    old_loups = models.ArrayField(
        model_container=SubsLoup
    )

    class Meta:
        abstract = True


class Repo(models.Model):

    repo_id = models.ObjectIdField()
    name = models.CharField("repository name", max_length=25, blank=False)
    repo_addr = models.CharField(
        "repository address",
        max_length=25,
        blank=False
    )
    url = models.URLField()
    email = models.EmailField()
    current_agree = models.EmbeddedField(
        model_container=SubsAgreement
    )
    old_agrees = models.ArrayField(
        model_container=SubsAgreement
    )

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


class Service(models.Model):

    repo_id = models.ForeignKey(Repo, on_delete=models.CASCADE)
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
    

class Developer(auth_models.User):

    dev_id = models.ObjectIdField()
    repo_id = models.ForeignKey(Repo, on_delete=models.CASCADE)


class Client(auth_models.User):

    client_id = models.ObjectIdField()
    repo_id = models.ForeignKey(Repo, on_delete=models.CASCADE)
    services_acq = models.ArrayReferenceField(
        to=Service,
        on_delete=models.CASCADE,
    )
