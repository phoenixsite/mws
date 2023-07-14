import os
from urllib.parse import unquote
import datetime

from django.views import View
from django.views.generic import (
    TemplateView,
    FormView,
    DetailView,
    CreateView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.base import ContextMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import views as auth_views
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, render, resolve_url, redirect
from django.urls import reverse
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.forms import formset_factory
from django.utils import timezone

import mws_main.models as models
import mws_main.forms as forms
import tenants.models as tmodels
from tenants.middlewares import get_current_db_name

class ThemeMixin(ContextMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.metadata = models.Metadata.objects.all().first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tenant"] = tmodels.Tenant.objects.get(
            subdomain_prefix=get_current_db_name()
        )
        context["metadata"] = self.metadata.appearance_metadata
        return context


class UserMixin(LoginRequiredMixin, ThemeMixin):

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)
        self.is_client = request.is_client
        self.is_developer = request.is_developer
        self.is_admin = request.is_admin
        self.user = request.user
    

class LoginView(auth_views.LoginView, ThemeMixin):
    """
    Login view. It lets client, developers and tenant
    administrators log in to its store.

    When a user is already logged in, it is redirected to the
    repository home page. 
    """

    template_name = "mws_main/login.html"
    form_class = forms.AuthenticationForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        
        if self.next_page:
            next_page = self.next_page
        else:
            next_page = reverse("mws_main:store_home")
            
        return resolve_url(next_page)


class LogoutView(auth_views.LogoutView, ThemeMixin):
    
    template_name = "mws_main/logout.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.next_page = reverse("mws_main:login")


class SignupSuccessView(TemplateView, ThemeMixin):
    template_name = "mws_main/signup-success.html"


class PasswordResetView(UserMixin, auth_views.PasswordResetView):
    pass

class PasswordResetDoneView(UserMixin, auth_views.PasswordResetDoneView):
    pass

class PasswordResetConfirmView(UserMixin, auth_views.PasswordResetConfirmView):
    pass

class PasswordResetCompleteView(UserMixin, auth_views.PasswordResetCompleteView):
    pass


class StoreHomeView(UserMixin, TemplateView):
    """
    Home view of the tenant's store.

    The template is determined by the group the authenticated
    user belongs to.
    """
    
    def get_template_names(self):

        template_name = "mws_main/{}_home.html"

        if self.is_client:
            return template_name.format("client")
        
        elif self.is_developer:
            return template_name.format("developer")
            
        elif self.is_admin:
            return template_name.format("admin")

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["services"] = models.Service.objects.all()

        if self.is_client:
            context["last_updated_services"] = context["services"][:3]
            context["last_uploaded_services"] = context["services"].order_by("-datetime_published")[:3]
        elif self.is_developer:
            context["services"] = self.user.assigned_services.all()
            context["updates"] = models.get_nupdates()
            context["monthly_updates"] = models.get_monthly_nupdates()
            
        elif self.is_admin:
            context["developers"] = models.Developer.objects.all()
            context["clients"] = models.Client.objects.all()
            context["monthly_reg_clients"] = context["clients"].filter(date_joined__month=timezone.now().month).count()
            context["reg_clients"] = context["clients"].count()
            context["acquisitions"] = sum([client.services_acq.get_queryset().count() for client in context["clients"]])
            context["updates"] = models.get_nupdates()
            context["monthly_updates"] = models.get_monthly_nupdates()

        return context


class ServiceDetailView(UserMixin, DetailView):
    model = models.Service
    context_object_name = "service"


class ClientAdminDetailView(PermissionRequiredMixin, UserMixin, DetailView):
    model = models.Client
    template_name = "mws_main/client_admin_detail.html"
    permission_required = "mws_main.view_admin_client"


class DeveloperAdminDetailView(PermissionRequiredMixin, UserMixin, DetailView):
    model = models.Developer
    template_name = "mws_main/developer_admin_detail.html"
    permission_required = "mws_main.view_admin_developer"


class ServiceAdminDetailView(PermissionRequiredMixin, UserMixin, DetailView):
    model = models.Service
    template_name = "mws_main/service_admin_detail.html"
    permission_required = "mws_main.view_admin_service"

    def dispatch(self, *args, **kwargs):
        """
        Check that if the user is a developer, the service is assigned to it.
        """
        
        if (
                self.is_developer
                and self.get_object() not in self.user.assigned_services.all()
        ):
            return HttpResponseForbidden("You cannot access the administrative page of this service")

        return super().dispatch(*args, **kwargs)


class ClientCreateView(CreateView, ThemeMixin):
    
    form_class = forms.ClientCreationForm
    template_name = "mws_main/client_form.html"

    def setup(self, request, *args, **kwargs):
        
        super().setup(request, *args, **kwargs)
        self.success_url = reverse("mws_main:signup_success")

    def get_success_url(self):
        return self.success_url


class DeveloperCreateView(PermissionRequiredMixin, UserMixin, CreateView):
    form_class = forms.DeveloperCreationForm
    template_name = "mws_main/developer_form.html"
    permission_required = "mws_main.add_developer"

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)
        self.success_url = reverse("mws_main:store_home")

    def get_success_url(self):
        return self.success_url


class ServiceCreateView(PermissionRequiredMixin, UserMixin, TemplateView):

    template_name = "mws_main/service_form.html"
    basic_form_class = forms.ServiceBasicInfoForm
    platform_form_class = forms.PlatformServiceForm
    permission_required = "mws_main.add_service"

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)
        
        # The service could be created by the tenant admin,
        # so the service should not be added to it.
        if self.is_developer:
            self.initial = {"creator": self.user.pk}
        else:
            self.initial = {"creator": None}

        self.basic_form = None
        self.platform_formset = None

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        if not self.basic_form:
            self.basic_form = self.basic_form_class(initial=self.initial)

        if not self.platform_formset:
            self.platform_formset = formset_factory(
                self.platform_form_class,
                extra=3,
                max_num=5,
                absolute_max=5)(prefix="platforms")
        
        context["basic_form"] = self.basic_form
        context["platform_formset"] = self.platform_formset
        return context

    def post(self, request, *args, **kwargs):

        self.basic_form = self.basic_form_class(request.POST, initial=self.initial)
        self.platform_formset = formset_factory(self.platform_form_class)(
            request.POST,
            request.FILES,
            prefix="platforms"
        )

        if self.basic_form.is_valid() and self.platform_formset.is_valid():

            service = models.create_service(
                self.basic_form.cleaned_data["name"],
                self.basic_form.cleaned_data["brief_descrp"],
                self.basic_form.cleaned_data["descrp"],
                [form.cleaned_data for form in self.platform_formset if form.cleaned_data and form.cleaned_data["package"] is not None],
                self.basic_form.cleaned_data["creator"],
                self.basic_form.cleaned_data["developers"]
            )

            return redirect(
                "mws_main:service_detail", pk=service.pk)
        else:
            return render(request, self.template_name, self.get_context_data())


class UserDetailView(UserMixin, DetailView):

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)

        if self.is_client:
            self.model = models.Client
        
        elif self.is_developer:
            self.template_name = "mws_main/developer_detail.html"
            self.model = models.Developer

        elif self.is_admin:
            self.template_name = "mws_main/tenantadmin_detail.html"
            self.model = models.TenantAdmin


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.is_developer:
            context["assigned_services"] = self.object.assigned_services.all()

        return context
    
    def get_object(self, queryset=None):
        return self.user


class UserUpdateView(UserMixin, UpdateView):

    template_name = "mws_main/update_user.html"
    form_class = forms.UserUpdateForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.success_url = reverse("mws_main:view_profile")


    def get_object(self, queryset=None):
        return self.user


class UpdateServiceView(UserMixin, UpdateView):

    template_name = "mws_main/update_service.html"
    form_class = forms.UpdateServiceForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.queryset = models.Service.objects.all()
        self.success_url = reverse("mws_main:service_admin_detail", args=[self.get_object().pk])
    

class PackageMixin(UserMixin):
    """
    Fetch the selected package and service.
    """

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.service = get_object_or_404(
            models.Service,
            pk=kwargs["service_id"])

        self.package = get_object_or_404(
            models.Package,
            pk=kwargs["package_id"]
        )

    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        context["service"] = self.service
        context["package"] = self.package
        return context


class DownloadServiceView(PackageMixin, View):

    def get(self, request, *args, **kwargs):
        
        package_url = self.package.package_file.url
        self.service.new_acquirement(self.user, self.is_client)

        if self.is_client:
            self.metadata.download_bandwidth
            
        return redirect(package_url)


class UpdatePackageView(PackageMixin, FormView):

    template_name = "mws_main/update_package.html"
    form_class = forms.UpdatePackageForm
    success_url = "mws_main:service_admin_detail"

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)
        self.success_url = f"/store/admin/service/{str(self.service.pk)}/"

    def form_valid(self, form):

        self.package.update_package(
            form.cleaned_data["package"],
            form.cleaned_data["changes"]
        )

        return super().form_valid(form)

    
class StoreInfoView(PermissionRequiredMixin, UserMixin, TemplateView):

    template_name = "mws_main/store_detail.html"
    permission_required = "mws_main.view_metadata"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        return context

class UpdateStoreInfo(PermissionRequiredMixin, UserMixin, FormView):
    template_name = "mws_main/update_store.html"
    permission_required = "mws_main.change_metadata"
    form_class = forms.StoreMetadataForm
    success_url = "mws_main:store_home"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.success_url = reverse("mws_main:store_home")

    def get(self, request, *args, **kwargs):
        """
        Fetch all the personalization metadata and put them
        available to the update form.
        """

        self.initial[self.metadata.MAIN_THEME_FIELD] = self.metadata.appearance_metadata[self.metadata.MAIN_THEME_FIELD]

        if self.metadata.FOOT_FIELD in self.metadata.appearance_metadata:
            metadata_foot = self.metadata.appearance_metadata[self.metadata.FOOT_FIELD]
        
            for ncol, col in enumerate(metadata_foot):
                
                self.initial[f"footer_col{ncol + 1}_title"] = col[self.metadata.TITLE_FIELD]
                
                for nrow, row in enumerate(col[self.metadata.ROWS_FIELD]):

                    field = f"footer_col{ncol + 1}_row{nrow + 1}"

                    self.initial[f"{field}_text"] = row[self.metadata.TEXT_FIELD]
                    self.initial[f"{field}_url"] = row[self.metadata.URL_FIELD]
        return super().get(request, *args, **kwargs)
        
    def form_valid(self, form):
        
        self.metadata.appearance_metadata["main_theme_color"] = form.cleaned_data["main_theme_color"]

        if form.has_footer():
            self.metadata.appearance_metadata["footer"] = []

            for col in form.get_non_empty_cols():
                col_dict = {"title": col[0]}
                col_dict["rows"] = [{'text': row[0], 'url': row[1]} for row in col[1]]

                self.metadata.appearance_metadata["footer"].append(col_dict)

        self.metadata.save(update_fields=["appearance_metadata"])
        return super().form_valid(form)
