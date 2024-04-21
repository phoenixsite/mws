from django.core.management import call_command
from django.db import models, connections
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model
import psycopg
import psycopg.sql as sql

import datetime
import os

from tenants.middlewares import set_db_for_router
import mws_main.models as mmodels

def save_cached_db_settings(db_settings, id):
    connections.databases[id] = db_settings

def save_db_settings_to_file(db_settings, id):

    path = "tenants/database_settings/"
    new_db_string = f"DATABASES['{id}'] = {str(db_settings)}"
    file_to_store_settings = os.path.join(path, id + ".py")
    
    with open(file_to_store_settings, "w") as file:
        file.write(new_db_string)

def migrate_new_db(new_db_name, id):

    from django.core.management import call_command
    from django.db import connection
    
    set_db_for_router(id)
    call_command("migrate", database=id, verbosity=0, interactive=False, settings=settings)


def create_tenant_db(name):
    return f"mws_{name}_db"


class Tenant(models.Model):
    """
    Represent the core data of those whose services
    are hosted in the platform. 

    A tenant are the users of their part of the platform,
    the resources used by them and thier clients (not
    implemented yet).
    """
    
    name = models.CharField(
        "store name",
        max_length=25,
        blank=False,
    )

    subdomain_prefix = models.CharField(
        max_length=25,
        blank=False,
        unique=True,
        help_text="Subdomain address to the tenant store.",
    )

    db_name = models.CharField(
        max_length=25,
        blank=False,
        unique=True,
    )

    email = models.EmailField()

    def __str__(self):
        return self.name


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

    tenant_db = create_tenant_db(subdomain_prefix)
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
    
    with  conn:

        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("CREATE DATABASE {} WITH ENCODING 'UTF8'")
                .format(sql.Identifier(tenant_db))
            )

    conn.close()

    settings.DATABASES[subdomain_prefix] = new_db
    save_cached_db_settings(new_db, subdomain_prefix)
    save_db_settings_to_file(new_db, subdomain_prefix)
    migrate_new_db(tenant_db, subdomain_prefix)
    
    tenant = Tenant.objects.create(
        name=name,
        subdomain_prefix=subdomain_prefix,
        db_name=name,
        email=email,
    )

    metadata = {"main_theme_color": "purple"}
    mmodels.Metadata.objects.create(
        appearance_metadata=metadata
    )

    mmodels.TenantAdmin.objects.create_user(
        username="admin",
        email=email,
        password="Ab12345678",
    )
    return tenant
