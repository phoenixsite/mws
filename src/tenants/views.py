from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import (
    UserPassesTestMixin,
    LoginRequiredMixin,
)
from django.contrib import messages
from . import forms
from . import models


class HomeView(TemplateView):
    template_name = "tenants/home.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context


class RegistrationView(TemplateView):

    template_name = "tenants/registration.html"
    tenant_form_class = forms.TenantForm
    admin_form_class = forms.AdminForm
    #success_url = reverse("tenants:completed")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tenant_form"] = self.tenant_form_class()
        context["admin_form"] = self.admin_form_class()
        return context
    
    def post(self, request, *args, **kwargs):

        admin_form = self.admin_form_class(request.POST)
        tenant_form = self.tenant_form_class(request.POST)
        
        if tenant_form.is_valid() and admin_form.is_valid():

            tenant = models.register_tenant(
                tenant_form.cleaned_data['name'],
                tenant_form.cleaned_data['store_url'],
            )
            
            tenant_admin = admin_form.save(commit=False)
            tenant_admin.tenant = tenant
            tenant_admin.save()

            store_url = reverse("mws_main:store_home", args=[tenant.store_url])
            messages.success(
                request,
                'You can acces now your'
                f' store at <a href="{store_url}">{store_url}</a>.'
            )
            return HttpResponseRedirect("/")
        
        return render(
            request,
            self.template_name,
            {
                "tenant_form": tenant_form,
                "admin_form": admin_form,
            })


class PlansView(TemplateView):
    template_name = "tenants/view_plans.html"
