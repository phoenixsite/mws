from django.contrib import admin

from mws_main.models import Client, Developer
from mws_main.forms import ClientForm

class ClientAdmin(admin.ModelAdmin):
    form = ClientForm


    
admin.site.register(Client, ClientAdmin)
admin.site.register(Developer)
