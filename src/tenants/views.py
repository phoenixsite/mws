from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import (
    UserPassesTestMixin,
    LoginRequiredMixin,)

import tenants.forms as forms
import tenants.models as models

from django.utils import timezone
import datetime


class NotAuthenticatedMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_anonymous


class RegistrationView(NotAuthenticatedMixin, TemplateView):

    template_name = "tenants/registration.html"
    tenant_form_class = forms.TenantForm
    admin_form_class = forms.AdminForm
    http_method_names = ["get", "post"]
    tenant_initial = {}
    admin_initial = {}
    
    def get(self, request, *args, **kwargs):

        tenant_form = self.tenant_form_class(initial=self.tenant_initial)
        admin_form = self.admin_form_class(initial=self.admin_initial)
        return render(
            request,
            self.template_name,
            {
                "tenant_form": tenant_form,
                "admin_form": admin_form,
                "agreements": models.DefaultSubsAgreement.objects.all()
            })
            

    def post(self, request, *args, **kwargs):

        admin_form = self.admin_form_class(request.POST)
        tenant_form = self.tenant_form_class(request.POST)
        
        if tenant_form.is_valid() and admin_form.is_valid():

            tenant = models.register_tenant(
                tenant_form.cleaned_data['name'],
                tenant_form.cleaned_data['repo_addr'],
                admin_form.cleaned_data['card_number'],
                tenant_form.cleaned_data['subs_agree_number']
            )
            
            tenant_admin = admin_form.save(commit=False)
            tenant_admin.tenant = tenant
            tenant_admin.save()

            return HttpResponseRedirect("/completed-registration/")
        
        return render(
            request,
            self.template_name,
            {
                "tenant_form": tenant_form,
                "admin_form": admin_form,
                "agreements": models.DefaultSubsAgreement.objects.all()
            })


class CompletedRegView(NotAuthenticatedMixin, TemplateView):
    template_name = "tenants/completed-reg.html"
    http_method_names = ["get"]


class MyRepoView(LoginRequiredMixin, TemplateView):
    template_name = "tenants/my-repo.html"
    http_method_names = ["get"]

class MyAgreementsView(LoginRequiredMixin, TemplateView):
    template_name = "tenants/my-agreements.html"
    http_method_names = ["get"]

class EditRepoView(LoginRequiredMixin, TemplateView):
    template_name = "tenants/edit-repo.html"
    http_method_names = ["get"]
    
