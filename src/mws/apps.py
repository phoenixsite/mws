from django.contrib.admin.apps import AdminConfig

class MWSAdminConfig(AdminConfig):
    default_site = "mws.admin.MWSAdminSite"
