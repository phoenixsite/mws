from django.contrib import admin

from mws_main.models import Client, Developer
from mws_main.forms import ClientAdminForm

class ClientAdmin(admin.ModelAdmin):
    form = ClientAdminForm


admin.site.register(Client, ClientAdmin)
admin.site.register(Developer)
