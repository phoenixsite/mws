from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import (
    UserPassesTestMixin,
    LoginRequiredMixin,
)
from django.contrib import messages
from tenants import forms, models


class HomeView(TemplateView):
    template_name = "tenants/home.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        context["stores"] = models.Tenant.objects.all()
        return context


class RegistrationView(TemplateView):

    template_name = "tenants/registration.html"
    tenant_form_class = forms.TenantForm
    #success_url = reverse("tenants:completed")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tenant_form"] = self.tenant_form_class()
        context["reg_error"] = None
        return context
    
    def post(self, request, *args, **kwargs):

        tenant_form = self.tenant_form_class(request.POST)
        
        if tenant_form.is_valid():

            try:
                tenant = models.register_tenant(
                    tenant_form.cleaned_data['name'],
                    tenant_form.cleaned_data['subdomain_prefix'],
                    tenant_form.cleaned_data['email'],
                )
            except exceptions.TenantRegistrationError as error:
                
                return render(
                    request,
                    self.template_name,
                    {
                        "tenant_form": tenant_form,
                        "reg_error": str(error),
                    },
                )
            
            store_url = f"http://{tenant.subdomain_prefix}.mws.local:8000/store/"
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
            },
            status=422,
        )


class PlansView(TemplateView):
    template_name = "tenants/view_plans.html"
