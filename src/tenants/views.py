from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import (
    UserPassesTestMixin,
    LoginRequiredMixin,)

import tenants.forms as forms
import tenants.models as models


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
        context["agreements"] = models.DefaultSubsAgreement.objects.all()
        return context

    def post(self, request, *args, **kwargs):

        admin_form = self.admin_form_class(request.POST)
        tenant_form = self.tenant_form_class(request.POST)
        
        if tenant_form.is_valid() and admin_form.is_valid():

            tenant = models.register_tenant(
                tenant_form.cleaned_data['name'],
                tenant_form.cleaned_data['repo_addr'],
                tenant_form.cleaned_data['card_number'],
                tenant_form.cleaned_data['subs_agree_number']
            )
            
            tenant_admin = admin_form.save(commit=False)
            tenant_admin.tenant = tenant
            tenant_admin.save()

            return HttpResponseRedirect(
                "/completed-registration/",
            )
        
        return render(
            request,
            self.template_name,
            {
                "tenant_form": tenant_form,
                "admin_form": admin_form,
                "agreements": models.DefaultSubsAgreement.objects.all()
            })


class CompletedRegView(TemplateView):
    template_name = "tenants/registration-success.html"
    


