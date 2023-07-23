from django.shortcuts import render
from django.views.generic.base import TemaplateView
from django.contrib.auth.mixins import UserPassesTestMixin

import tenants.forms as forms
import tenant.models as models

from django.utils import timezone
import datetime


class NotAuthenticatedMixin(UserPassesTestMixin):

    def test_func(self):
        return not self.request.user.is_authenticated()


class RegistrationView(NotAuthenticatedMixin, TemplateView):

    template_name = "registration.html"
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

        admin_form = self.tenant_form_class(request.POST.fromkeys([
            "username",
             "password",
             "email",
             "first_name",
             "last_name"]))

        tenant_form = self.admin_form_class(request.POST.fromkeys([
            "card_number",
            "subs_agreement_number",
            "name",
            "repo_addr",
            "url"]))

        if tenant_form.is_valid() and admin_form.is_valid():

            # Choosen subscription agreement
            def_agree = models.DefaultSubsAgreement.objects.get(
                name=tenant_form.cleaned_data["subs_agreement_number"])
            # Per-resource consumption in the first month
            iresources = [models.IResourceUsage.objects.create(
                res_name=plan.name) for plan in def_agree.plans]

            # The first month loup
            empty_loup = models.SubsLoup.objects.create(
                end_date=timezone.now() + datetime.timedelta(month=1),
                usages=iresources)
            
            subs_agree = models.SubsAgreement.objects.create(
                date_regs=timezone.now(),
                end_date=timezone.now() + def_agree.end_date,
                card_number=tenant_form.cleaned_data["card_number"],
                plans=def_agree.plans,
                current_loop=empty_loup)

            tenant = models.Tenant.objects.create(
                name=tenant_form.cleaned_data["name"],
                repo_addr=tenant_form.cleaned_data["repo_addr"],
                url=tenant_form.cleaned_data["url"],
                current_agree=subs_agree)

            tenant_admin = admin_form.save(commit=False)
            tenant_admin.tenant = tenant
            tenant.save()
            tenant_admin.save()

            return HttpResponseRedirect("completed-registration/")
        
        return render(
            request,
            self.template_name,
            {
                "tenant_form": tenant_form,
                "admin_form": admin_form,
                "agreements": models.DefaultSubsAgreement.objects.all()
            })


class CompletedReg(NotAuthenticatedMixin, TemplateView):
    template_name = "completed-reg.html"
    http_method_names = ["get"]

