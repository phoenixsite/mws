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
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth import views as auth_views
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, render, resolve_url, redirect
from django.urls import reverse
from django.http import Http404, HttpResponse
from django.forms import formset_factory
from django.utils import timezone

import bson
import mimetypes
import os
from urllib.parse import unquote
import datetime

import mws_main.models as models
import mws_main.forms as forms
import mws_metadata.models as meta_models
from tenants.models import Tenant, TenantAdmin, User, ADMIN_GROUP


class TenantMixin(ContextMixin):
    """
    Retrieve the tenant from the url.
    """

    def setup(self, request, *args, **kwargs):
        
        super().setup(request, *args, **kwargs)
        
        self.tenant = get_object_or_404(
            Tenant,
            store_url=self.kwargs['store_url'])
        
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["tenant"] = self.tenant
        context["metadata"] = self.tenant.metadata
        return context


class TenantLoginRequiredMixin(TenantMixin, AccessMixin):
    """
    Verify that the current user is authenticated and
    its tenant is the same as the view's tenant.
    """

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.login_url = reverse("mws_main:login",
                                 args=[self.tenant.store_url])
    
    def dispatch(self, request, *args, **kwargs):
        """
        Check the user login information and dispatch to
        an HTTP method.
        """
        if not (self.user.is_authenticated
            and self.user.tenant
            and self.tenant == self.user.tenant):

            return self.handle_no_permission()
            
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        """
        If an authenticated user try to access to another
        view which doesn't correspond to the users's tenant, 
        then a the page should appear as it doesn't exist,
        ensuring tenant isolation.
        """ 
        if (self.user.is_authenticated
            and self.user.tenant
            and self.tenant != self.user.tenant):
            raise Http404()
        else:
            return super().handle_no_permission()


class TenantUserMixin(TenantLoginRequiredMixin):
    """
    Represent a view contained in a tenant store and
    its access is restricted to authenticated tenant users.
    
    The contents provided by the view may depend on the
    the user permissions.
    """
    
    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)

        self.user = self.request.user
        self.is_client = False
        self.is_developer = False
        self.is_admin = False
        
        if self.user.groups.filter(name=models.CLIENT_GROUP).exists():
            self.user = self.user.client
            self.is_client = True
            
        elif self.user.groups.filter(name=models.DEV_GROUP).exists():
            self.user = self.user.developer
            self.is_developer = True
            
        elif self.user.groups.filter(name=ADMIN_GROUP).exists():
            self.user = self.user.tenantadmin
            self.is_admin = True

        
class LoginView(TenantMixin, auth_views.LoginView):
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
            next_page = reverse("mws_main:store_home", args=[self.tenant.store_url])
            
        return resolve_url(next_page)


class LogoutView(TenantMixin, auth_views.LogoutView):
    
    template_name = "mws_main/logout.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.next_page = reverse("mws_main:login", args=[self.tenant.store_url])


class SignupSuccessView(TenantMixin, TemplateView):
    template_name = "mws_main/signup-success.html"


class PasswordResetView(TenantUserMixin, auth_views.PasswordResetView):
    pass


class PasswordResetDoneView(TenantUserMixin, auth_views.PasswordResetDoneView):
    pass


class PasswordResetConfirmView(TenantUserMixin, auth_views.PasswordResetConfirmView):
    pass


class PasswordResetCompleteView(TenantUserMixin, auth_views.PasswordResetCompleteView):
    pass


class StoreHomeView(TenantUserMixin, TemplateView):
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
        context["services"] = models.Service.objects.filter(
            tenant_id=self.tenant._id)

        if self.is_admin:
            context["developers"] = models.Developer.objects.filter(
                tenant=self.tenant._id)
            context["clients"] = models.Client.objects.filter(
                tenant=self.tenant._id)
            context["monthly_reg_clients"] = context["clients"].filter(date_joined__month=timezone.now().month).count()
            context["reg_clients"] = context["clients"].count()
            context["acquisitions"] = sum([client.services_acq.get_queryset().count() for client in context["clients"]])
            context["updates"] = models.get_nupdates(self.tenant.pk)
            context["monthly_updates"] = models.get_monthly_nupdates(self.tenant.pk)
            
        if self.is_client:
            context["last_updated_services"] = context["services"][:3]
            context["last_uploaded_services"] = context["services"].order_by("-datetime_published")[:3]

        return context


class TQuerysetMixin(SingleObjectTemplateResponseMixin, TenantMixin):
    """
    The required queryset depends on the store (tenant).
    
    It guarantees that a view access to the data that belongs to its
    tenant.
    It requires that the view is going to access to some
    data from a single specific model (self.model).
    """
    
    def get_queryset(self):
        return self.model.objects.filter(tenant=self.tenant.pk)


class ServiceDetailView(TQuerysetMixin, TenantUserMixin, DetailView):
    model = models.Service
    context_object_name = "service"


class ClientAdminDetailView(PermissionRequiredMixin, TQuerysetMixin,
                            TenantUserMixin, DetailView):
    model = models.Client
    template_name = "mws_main/client_admin_detail.html"
    permission_required = "mws_main.view_admin_client"


class DeveloperAdminDetailView(PermissionRequiredMixin, TQuerysetMixin,
                               TenantUserMixin, DetailView):
    model = models.Developer
    template_name = "mws_main/developer_admin_detail.html"
    permission_required = "mws_main.view_admin_developer"


class ServiceAdminDetailView(PermissionRequiredMixin, TQuerysetMixin,
                             TenantUserMixin, DetailView):
    model = models.Service
    template_name = "mws_main/service_admin_detail.html"
    permission_required = "mws_main.view_admin_service"


class ClientCreateView(TenantMixin, CreateView):
    
    form_class = forms.ClientCreationForm
    template_name = "mws_main/client_form.html"

    def setup(self, request, *args, **kwargs):
        
        super().setup(request, *args, **kwargs)
        self.initial = {'store_url': self.kwargs['store_url']}
        self.success_url = reverse("mws_main:signup_success", args=[self.tenant.store_url])

    def get_success_url(self):
        return self.success_url


class DeveloperCreateView(PermissionRequiredMixin, TenantUserMixin,
                          CreateView):
    form_class = forms.DeveloperCreationForm
    template_name = "mws_main/developer_form.html"
    permission_required = "mws_main.add_developer"

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)
        self.initial = {'store_url': self.kwargs['store_url']}
        self.success_url = reverse("mws_main:store_home",
                                 args=[self.tenant.store_url])

    def get_success_url(self):
        return self.success_url


class ServiceCreateView(PermissionRequiredMixin, TenantUserMixin,
                        TemplateView):

    template_name = "mws_main/service_form.html"
    basic_form_class = forms.ServiceBasicInfoForm
    platform_form_class = forms.PlatformServiceForm
    permission_required = "mws_main.add_service"

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)

        self.initial = {'store_url': self.kwargs['store_url']}
        
        # The service could be created by the tenant admin,
        # so the service should not be added to it.
        if self.is_developer:
            creator_key = {"creator": self.user._id}
        else:
            creator_key = {"creator": None}

        self.initial.update(creator_key)

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
                self.tenant,
                self.basic_form.cleaned_data["creator"],
                self.basic_form.cleaned_data["developers"]
            )

            return redirect(
                "mws_main:service_detail",
                store_url=self.tenant.store_url,
                pk=service.pk)
        else:
            return render(request, self.template_name, self.get_context_data())


class UserDetailView(TQuerysetMixin, TenantUserMixin, DetailView):

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)

        if self.is_client:
            self.model = models.Client
        
        elif self.is_developer:
            self.template_name = "mws_main/developer_detail.html"
            self.model = models.Developer

        elif self.is_admin:
            self.template_name = "mws_main/tenantadmin_detail.html"
            self.model = TenantAdmin

    def get_object(self, queryset=None):
        return self.user


class UserUpdateView(TQuerysetMixin, TenantUserMixin, UpdateView):

    template_name = "mws_main/update_user.html"
    form_class = forms.UserUpdateForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.success_url = reverse("mws_main:view_profile", args=[self.tenant.store_url])


    def get_object(self, queryset=None):
        return self.user


class PackageMixin(TenantUserMixin):
    """
    View whose functionality depends on a service package.

    Due to the abstract feature of the `package model, some previous
    steps are required to get a package.
    """

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.service = get_object_or_404(
            models.Service,
            pk=kwargs["service_id"])

        n_package = kwargs["n_package"]
        
        try:
            self.package = self.service.packages[n_package]
        except IndexError:
            raise Http404()

    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        context["service"] = self.service
        context["package"] = self.package
        return context


class DownloadServiceView(PackageMixin, View):

    def get(self, request, *args, **kwargs):
        
        package_url = self.package["package_file"].url
        package_name = self.package["name"]

        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = BASE_DIR + unquote(package_url)
        path = open(filepath, 'rb')
        mime_type, _ = mimetypes.guess_type(filepath)

        response = HttpResponse(path, content_type=mime_type)
        response['Content-Disposition'] = f"attachment; filename={package_name}"

        self.service.new_acquirement(self.user)
        return response

class UpdatePackageView(PackageMixin, FormView):

    template_name = "mws_main/update_package.html"
    form_class = forms.UpdatePackageForm
    success_url = "mws_main:service_admin_detail"

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)
        self.success_url = f"/store/{self.tenant.store_url}/admin/service/{str(self.service.pk)}/"
        self.initial = {"n_package": self.package["n_package"]}
        """
        self.success_url = resolve_url(
            self.success_url,
            args=[self.tenant.store_url, self.service.pk]
        )
        """

    def form_valid(self, form):

        self.service.update_package(
            self.package["n_package"],
            form.cleaned_data["package"],
            form.cleaned_data["changes"]
        )

        return super().form_valid(form)

    
class StoreInfoView(PermissionRequiredMixin, TenantUserMixin,
                    TemplateView):

    template_name = "mws_main/store_detail.html"
    permission_required = "tenants.view_tenant"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context
        return context

class UpdateStoreInfo(PermissionRequiredMixin, TenantUserMixin,
                        UpdateView):
    template_name = "mws_main/update_store.html"
    permission_required = "tenants.change_tenant"
    model = meta_models.StoreMetadata
    success_url = "mws_main:store_home"
    fields = "__all__"

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)
        self.success_url = f"/store/{self.tenant.store_url}/"

    def get_object(self):
        return self.get_queryset().filter(pk=self.tenant.metadata.pk).get()
