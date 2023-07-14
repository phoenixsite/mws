import datetime
import os
import time
import logging

from django.db import models

from django.utils import timezone
import mws_main.models as mmodels
import tenants.db_management as db


class Tenant(models.Model):
    """
    Represent the core data of those whose services are hosted in the
    platform. 

    A tenant are the users of their part of the platform, the resources
    used by them and thier clients.
    """
    
    name = models.CharField(
        "store name",
        max_length=25,
    )

    subdomain_prefix = models.CharField(
        max_length=25,
        unique=True,
        help_text="Subdomain address to the tenant store.",
    )

    db_name = models.CharField(
        max_length=25,
        unique=True,
    )

    db_host = models.CharField(
        max_length=45,
    )

    db_port = models.CharField(
        max_length=6,
    )

    # Careful, this should change.
    # Plain password on database
    db_password = models.CharField(
        max_length=35,
    )

    db_user = models.CharField(
        max_length=30,
    )

    email = models.EmailField()

    def __str__(self):
        return self.name


def register_tenant(name, subdomain, email):
    """
    Create a new tenant.
    """

    db_settings = db.create_db(subdomain)

    tenant = Tenant.objects.create(
        name=name,
        subdomain_prefix=subdomain,
        email=email,
        db_host=db_settings["db_host"],
        db_port=db_settings["db_port"],
        db_name=db_settings["db_name"],
        db_password=db_settings["db_password"],
        db_user=db_settings["db_user"]
    )
    
    metadata = {"main_theme_color": "purple"}
    mmodels.Metadata.objects.create(
        appearance_metadata=metadata,
        download_bandwidth={},
    )

    mmodels.TenantAdmin.objects.create_user(
        username="admin",
        email=email,
        password="Ab12345678",
    )
    
    return tenant
