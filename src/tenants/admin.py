from django.contrib import admin
from djongo.admin import ModelAdmin

from .models import DefaultSubsAgreement, Tenant, TenantAdmin

admin.site.register(DefaultSubsAgreement)
admin.site.register(Tenant)
admin.site.register(TenantAdmin)
