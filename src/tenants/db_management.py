import logging

import psycopg.sql as sql
import psycopg

from django.conf import settings
from django.db import connections
from django.core.management import call_command

from tenants.middlewares import set_db_for_router
import tenants.exceptions as exceptions

def save_cached_db_settings(db_settings, id):

    if id in settings.DATABASES:
        raise CachingDatabaseError(
            f"The identifier {id} of the database is already in the"
            "settings DATABASE property."
        )

    if id in connections.databases:
        raise CachingDatabaseError(
            f"The identifier {id} of the database is already in the "
            "connections databases property."
        )
    
    settings.DATABASES[id] = db_settings
    connections.databases[id] = db_settings
    

def revert_cached_db_settings(id):
    """
    Remove the database `id` from the cached database connections.

    The argument `id` must be different from `default`.

    :param id: Identifier of the database.
    :type id: str
    """

    if id == 'default':
        raise ValueError(
            "There has been an attempt to remove the cached settings"
            "of the default database."
        )

    if id in connections.databases:
        del connections.databases[id]

    if id in settings.DATABASES[id]:
        del settings.DATABASES[id]

def revert_creation_of_database(db_name, db_settings):
    """
    Drop a tenant's database in case of error during the process
    of registration.

    The parameter `db_name` must be different from the name of the
    `default` database name. If the tenant has been already created,
    the drop operation is aborted.

    :param db_name: Name of tenant's database.
    :type db_name: str
    """

    if db_name == settings.DATABASES['default']:
        raise ValueError(
            "Default database attempted to be removed!"
        )

    conn = psycopg.connect(
        host=db_settings["HOST"],
        port=db_settings["PORT"],
        user=db_settings["USER"],
        password=db_settings["PASSWORD"],
        dbname=settings.DATABASES["default"]["NAME"],
        autocommit=True
    )

    try:
        with conn:

            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("DROP DATABASE {}")
                    .format(sql.Identifier(tenant_db))
                )
    except psycopg.OperationalError as e:
        raise e
    finally:
        conn.close()    
        

def migrate_new_db(new_db_name, id):
    """
    Migrate the platform model to the newly created tenant's database.
    """

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

def create_db(subdomain):

    tenant_db = generate_tenant_db(subdomain)
    new_db_settings = {
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

    try:
        with conn:

            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("CREATE DATABASE {} WITH ENCODING 'UTF8'")
                    .format(sql.Identifier(tenant_db))
                )

        save_cached_db_settings(new_db_settings, subdomain)
        set_db_for_router(subdomain)
        migrate_new_db(tenant_db, subdomain)
        load_permissions(subdomain)

    except psycopg.Error as e:

        set_db_for_router()
        revert_cached_db_settings(subdomain)
        
        try:
            revert_creation_of_database(tenant_db, new_db_settings)

        except ValueError as e:
            logger.error(str(e))
        except psycopg.OperationalError as e:
            logging.critical(f"Couldn't drop an invalid database: {e}")

        raise exceptions.TenantRegistrationError(
            "There has been an internal error trying"
            "to register your data. Please, try again"
            "later."
        )
    
    finally:
        conn.close()

    return {
        "db_host": new_db_settings["HOST"],
        "db_port": new_db_settings["PORT"],
        "db_name": new_db_settings["NAME"],
        "db_user": new_db_settings["USER"],
        "db_password": new_db_settings["PASSWORD"]
    }
