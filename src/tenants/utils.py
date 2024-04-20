import psycopg
import psycopg.sql as sql
from django.conf import settings

# We cannot access the model Tenant from the tenants app
# because there would be a circular import, so the explicit name
# of the table is placed here.
TENANTS_TABLE = "tenants_tenant"

def subdomain_from_request(request):
    "Extract the subdomain from the request address"
    return request.get_host().split(':')[0].lower().split('.')[0]

def get_tenant_db(subdomain_prefix):
    """
    Get the Django' id of the database related to the given subdomain.

    It creates a new connection to the default Django's database,
    where the registered
    tenants are. Onced the db name is retrieved, it closes the connection.

    :param subdomain_prefix: Request address subdomain.
    :type subdomain_prefix: str
    :return: Django's database name (not the real Postgres database name)
    :rtype: str
    """

    conn =  psycopg.connect(
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
                sql.SQL("""
                SELECT subdomain_prefix, db_name
                FROM {}
                WHERE subdomain_prefix = %s;
                """).format(sql.Identifier(TENANTS_TABLE)),
                (subdomain_prefix,)
            )
            db_name = cur.fetchone()

    conn.close()

    if db_name:
        db_name = db_name[1]
    
    return db_name

def tenant_db_from_request(request):
    subdomain = subdomain_from_request(request)
    return get_tenant_db(subdomain)
