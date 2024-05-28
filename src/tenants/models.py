import datetime
import os
import time

from django.core.management import call_command
from django.db import models, connections
from django.conf import settings

from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model
import psycopg
import psycopg.sql as sql

from tenants.middlewares import set_db_for_router
import mws_main.models as mmodels


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


def save_cached_db_settings(db_settings, id):
    connections.databases[id] = db_settings


def migrate_new_db(new_db_name, id):
    
    call_command("migrate",
                 database=id,
                 verbosity=0,
                 interactive=False,
                 settings=settings)

def load_permissions(id):

    call_command("loaddata",
                 [settings.PERMISSIONS_FIXTURE],
                 database=id,
                 verbosity=0,
                 settings=settings)


def generate_tenant_db(name):
    return f"mws_{name}_db"


def register_tenant(name, subdomain_prefix, email):
    """
    Create a new tenant.

    It creates a new connection to the default Django's database.
    Onced the db name is created, it closes the connection.
    The connection is made to this database because the connection to a
    Postgres DB server must be directed to a specific database.

    The new database has the same parameters as the default one, but
    this behaviour can be easily extended to more complex configurations.
    """

    tenant_db = generate_tenant_db(subdomain_prefix)
    new_db = {
        "NAME": tenant_db,
        "ENGINE": "django.db.backends.postgresql",
        "USER": settings.DATABASES["default"]["USER"],
        "PASSWORD": settings.DATABASES["default"]["PASSWORD"],
        "HOST": settings.DATABASES["default"]["HOST"],
        "PORT": settings.DATABASES["default"]["PORT"],
        "TIME_ZONE": None,
        "CONN_MAX_AGE": 0,
        "AUTOCOMMIT": True,
        "ATOMIC_REQUESTS": False,
        "CONN_HEALTH_CHECKS": False,
        "OPTIONS": {},
        "DISABLE_SERVER_SIDE_CURSORS": False,
        "TEST":  {},
    }

    # Create the tenant database
    conn = psycopg.connect(
        host=settings.DATABASES["default"]["HOST"],
        port=settings.DATABASES["default"]["PORT"],
        user=settings.DATABASES["default"]["USER"],
        password=settings.DATABASES["default"]["PASSWORD"],
        dbname=settings.DATABASES["default"]["NAME"],
        autocommit=True
    )
    
    with conn:

        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE DATABASE {} WITH ENCODING 'UTF8'")
                .format(sql.Identifier(tenant_db))
            )

    settings.DATABASES[subdomain_prefix] = new_db
    save_cached_db_settings(new_db, subdomain_prefix)
    set_db_for_router(subdomain_prefix)
    migrate_new_db(tenant_db, subdomain_prefix)
    load_permissions(subdomain_prefix)
    
    tenant = Tenant.objects.create(
        name=name,
        subdomain_prefix=subdomain_prefix,
        db_name=tenant_db,
        db_user=new_db["USER"],
        db_host=new_db["HOST"],
        db_port=new_db["PORT"],
        db_password=new_db["PASSWORD"],
        email=email,
    )

    conn.close()

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
