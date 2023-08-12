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
from django.shortcuts import get_object_or_404, render, resolve_url, render
from django.forms import ModelForm
from django.urls import reverse
from django.http import Http404, HttpResponse

import bson
import mimetypes
import os
from urllib.parse import unquote

import mws_main.models as models
import mws_main.forms as forms
from tenants.models import Tenant, TenantAdmin, User, ADMIN_GROUP


class TenantMixin(ContextMixin):
    """
    Retrieve the tenant from the the mixin url.
    """

    def setup(self, request, *args, **kwargs):
        """
        Fetch the view's tenant using the url in the request.
        """
        
        super().setup(request, *args, **kwargs)
        
        self.tenant = get_object_or_404(
            Tenant,
            url=self.kwargs['store_url'])
        

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["tenant"] = self.tenant
        return context


class TenantLoginRequiredMixin(TenantMixin, AccessMixin):
    """
    Verify that the current user is authenticated and
    its tenant is the same as the view's tenant.
    """

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.login_url = reverse("mws_main:login",
                                 args=[self.tenant.repo_addr])
    
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
            next_page = reverse("mws_main:repo_home", args=[self.tenant.repo_addr])
            
        return resolve_url(next_page)


class LogoutView(TenantMixin, auth_views.LogoutView):
    """
    Log out view. Only reachable with a POST or OPTIONS
    method.
    """
    template_name = "mws_main/logout.html"
    http_method_names = ["post", "options"]


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

        template_name = "mws_main/{}__home.html"

        if self.is_client:
            return template_name.format("client")
        
        elif self.is_developer:
            return template_name.format("developer")
            
        elif self.is_admin:
            return template_name.format("admin")


    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        
        if self.is_admin:
            context["developers"] = models.Developer.objects.filter(
                tenant=self.tenant._id)
            context["clients"] = models.Client.objects.filter(
                tenant=self.tenant._id)

        context["services"] = models.Service.objects.filter(
            tenant_id=self.tenant._id)

        return context


class TQuerysetMixin(SingleObjectTemplateResponseMixin, TenantMixin):
    """
    The required queryset depends on the store (tenant).
    
    It guarantees that a view access to tenant data that does
    not correspond the its tenant.
    It requires that the views is going to access to some
    data from a single specific model (self.model).
    """
    
    def get_queryset(self):
        return self.model.objects.filter(tenant=self.tenant.pk)


class ServiceDetailView(TQuerysetMixin, TenantUserMixin, DetailView):
    model = models.Service
    context_object_name = "service"


class ClientAdminDetailView(TQuerysetMixin, TenantUserMixin, DetailView):
    model = models.Client
    template_name = "mws_main/client_admin_detail.html"


class DeveloperAdminDetailView(TQuerysetMixin, TenantUserMixin, DetailView):
    model = models.Developer
    template_name = "mws_main/developer_admin_detail.html"


class ServiceAdminDetailView(TQuerysetMixin, TenantUserMixin, DetailView):
    model = models.Service
    template_name = "mws_main/service_admin_detail.html"

    
class TModelCreateView(CreateView):
    """
    Creation view whose model depends on a tenant.
    """

    def setup(self, request, *args, **kwargs):
        """
        The store address is passed to the form 
        instance as an initial value so the tenant can 
        be identified when the form is saved
        """
        
        super().setup(request, *args, **kwargs)
        self.initial = {'store_url': self.kwargs['store_url']}
        self.success_url = reverse("mws_main:store_home",
                                 args=[self.tenant.store_url])

    def get_success_url(self):
        return self.success_url


class ClientCreateView(TenantMixin, TModelCreateView):
    
    form_class = forms.ClientCreationForm
    template_name = "mws_main/client_form.html"

    def setup(self, request, *args, **kwargs):
        
        super().setup(request, *args, **kwargs)
        self.success_url = reverse("mws_main:signup_success", args=[self.tenant.store_url])


class DeveloperCreateView(TenantUserMixin, TModelCreateView):
    form_class = forms.DeveloperCreationForm
    template_name = "mws_main/developer_form.html"


class ServiceCreateView(TenantUserMixin, TModelCreateView):

    form_class = forms.ServiceCreationForm
    model = models.Service

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)
        
        # The service could be created by the tenant admin,
        # so the service should not be added to it.
        if self.is_developer:
            self.initial.update({"creator": self.user._id})


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
        self.success_url = reverse("mws_main:view_profile", args=[self.tenant.repo_addr])


    def get_object(self, queryset=None):
        return self.user


class DownloadServiceView(TenantUserMixin, View):

    def get(self, request, *args, **kwargs):

        service = get_object_or_404(
            models.Service,
            pk=kwargs["service_id"])
    
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = BASE_DIR + unquote(service.package.url)
        path = open(filepath, 'rb')
        mime_type, _ = mimetypes.guess_type(filepath)

        response = HttpResponse(path, content_type=mime_type)
        response['Content-Disposition'] = f"attachment; filename={service.name}"

        service.new_acquirement(self.user)
        return response
