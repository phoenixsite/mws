
# We cannot access the model Tenant from the tenants app
# because there would be a circular import, so the explicit name
# of the table is placed here.
TENANTS_TABLE = "tenants_tenant"

def subdomain_from_request(request):
    "Extract the subdomain from the request address"
    return request.get_host().split(':')[0].lower().split('.')[0]

def get_tenant_db(subdomain):
    """
    Get the Django' id of the database related to the given subdomain.

    Currently, the database id is the same as the subdomain of the
    tenant.

    :param subdomain_prefix: Request address subdomain.
    :type subdomain_prefix: str
    :return: Django's database name (not the real Postgres database name)
    :rtype: str
    """

    db_name = subdomain
    return db_name

def tenant_db_from_request(request):
    subdomain = subdomain_from_request(request)
    return get_tenant_db(subdomain)
