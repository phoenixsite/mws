from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Tenant, TenantAdmin

admin.site.register(User)
admin.site.register(Tenant)
admin.site.register(TenantAdmin)
