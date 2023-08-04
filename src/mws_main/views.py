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
from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
from django.contrib.auth import forms as auth_forms
from django.shortcuts import get_object_or_404, render, resolve_url, render
from django.forms import ModelForm
from django.urls import reverse
from django.http import HttpResponseNotFound, Http404, HttpResponse

import bson
import mimetypes
import os

import mws_main.models as models
import mws_main.forms as forms
from tenants.models import Tenant, TenantAdmin, ADMIN_GROUP
import mws.settings as settings


class TenantMixin(ContextMixin):
    """
    Retrieve the tenant where the mixin , so
    to ensure a correct view functionality the view saves
    the tenant information.
    """

    def setup(self, request, *args, **kwargs):
        """
        Fetch the view's tenant using the url in the request.
        """
        
        super().setup(request, *args, **kwargs)
        
        self.tenant = get_object_or_404(
            Tenant,
            repo_addr=self.kwargs['repo_addr'])
        

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
        then a PermissionDenied exception is raised. This 
        approach violates the isolation between tenants, as
        a user from one tenant might acknoledge the existence
        of other tenants.
        """
        if (self.user.is_authenticated
            and self.user.tenant
            and self.tenant != self.user.tenant):
            raise Http404()
        else:
            return super().handle_no_permission()


class TenantUserMixin(TenantLoginRequiredMixin):
    """
    Represent a view contained in a tenant repository and
    its access is restricted to authenticated tenant users.
    
    The contents provided by the view depends on the
    permissions of the user.
    """
    
    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)

        self.user = self.request.user
        self.user.tenant = None
        self.is_client = False
        self.is_developer = False
        self.is_admin = False

        
        if self.user.groups.filter(name=models.CLIENT_GROUP).count() == 1:
            self.user = self.user.client
            self.is_client = True
            
        elif self.user.groups.filter(name=models.DEV_GROUP).count() == 1:
            self.user = self.user.developer
            self.is_developer = True
            
        elif self.user.groups.filter(name=ADMIN_GROUP).count() == 1:
            self.user = self.user.tenantadmin
            self.is_admin = True

        
class LoginView(auth_views.LoginView, TenantMixin):
    """
    Login view. It lets client, developers and tenant
    administrators log in to its repository.

    When a user is already logged in, it is redirected to the
    repository home page. 
    """

    template_name = "mws_main/login.html"
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
    
        if self.next_page:
            next_page = self.next_page
        else:
            next_page = reverse("mws_main:repo_home", args=[self.tenant.repo_addr])
        return resolve_url(next_page)


class LogoutView(auth_views.LogoutView, TenantMixin):
    """
    Log out view. Only reachable with a POST or OPTIONS
    method.
    """
    template_name = "mws_main/logout.html"
    http_method_names = ["post", "options"]


class SignupView(auth_views.RedirectURLMixin, FormView, TenantMixin):

    form_class = forms.ClientCreationForm
    template_name = "mws_main/signup.html"

    def setup(self, request, *args, **kwargs):
        
        super().setup(request, *args, **kwargs)
        self.initial = {'repo_addr': self.kwargs['repo_addr']}
        self.next_page = reverse("mws_main:signup_success",
                                args=[self.tenant.repo_addr])

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class SignupSuccessView(TenantMixin, TemplateView):
    template_name = "mws_main/signup-success.html"
        
class PasswordResetView(auth_views.PasswordResetView, TenantUserMixin):
    pass

class PasswordResetDoneView(auth_views.PasswordResetDoneView, TenantUserMixin):
    pass

class PasswordResetConfirmView(auth_views.PasswordResetConfirmView, TenantUserMixin):
    pass

class PasswordResetCompleteView(auth_views.PasswordResetCompleteView, TenantUserMixin):
    pass

class RepoHomeView(TenantUserMixin, TemplateView):
    """
    Home view of the tenant's repository.

    The template is determined by the group the authenticated
    user belongs to.
    """
    
    def get_template_names(self):

        template_name = "mws_main/{}_repo_home.html"

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


class URLDetailMixin(SingleObjectTemplateResponseMixin, TenantUserMixin):
    """
    Detail view whose object depends on the repository (tenant),
    so the queryset is fixed by it and the object primary key
    is obtained from the url.
    """
    slug_field = "_id"

    def get_queryset(self):
        return self.model.objects.filter(tenant=self.tenant.pk)

    def dispatch(self, request, *args, **kwargs):
        self.kwargs.update(
            {self.slug_url_kwarg: bson.ObjectId(kwargs.get(self.slug_url_kwarg))})
        return super().dispatch(request, *args, **kwargs)
    

class ServiceDetailView(URLDetailMixin, DetailView):
    model = models.Service
    context_object_name = "service"

class ClientAdminDetailView(URLDetailMixin, DetailView):
    model = models.Client
    context_object_name = "client"
    template_name = "mws_main/client_admin_detail.html"

class DeveloperAdminDetailView(URLDetailMixin, DetailView):
    model = models.Developer
    context_object_name = "developer"
    template_name = "mws_main/developer_admin_detail.html"

class AddRepoEntityView(FormView):
    """
    Form view whose model depends on the tenant.
    """

    def setup(self, request, *args, **kwargs):
        
        super().setup(request, *args, **kwargs)
        self.initial = {'repo_addr': self.kwargs['repo_addr']}
        self.success_url = reverse("mws_main:repo_home",
                                 args=[self.tenant.repo_addr])

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)



class AddDeveloperView(AddRepoEntityView, TenantUserMixin):

    form_class = forms.DeveloperCreationForm
    template_name = "mws_main/add_developer.html"
    
    
class AddServiceView(AddRepoEntityView, TenantUserMixin):

    form_class = forms.ServiceCreationForm
    template_name = "mws_main/add_service.html"

class UserDetailMixin(SingleObjectTemplateResponseMixin, TenantUserMixin):
    """
    Retrieve an object that depends on the repository (tenant),
    so the queryset is fixed by it and the object primary key
    is obtained from the current authenticated user.

    It is similar to URLDetailMixin, but the difference is
    where the primary key of the object comes from.
    """
    slug_field = "_id"

    def get_queryset(self):
        return self.model.objects.filter(tenant=self.tenant.pk)

    def dispatch(self, request, *args, **kwargs):
        self.kwargs.update(
            {self.slug_url_kwarg: bson.ObjectId(self.user.pk)})
        return super().dispatch(request, *args, **kwargs)


class UserDetailView(UserDetailMixin, DetailView):

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)

        if self.is_client:
            self.model = models.Client
            context_object_name = "client"
        
        elif self.is_developer:
            self.model = models.Developer
            context_object_name = "developer"


class UserUpdateView(TenantUserMixin, UpdateView):

    slug_field = "_id"
    
    def get_queryset(self):
        return self.model.objects.filter(tenant=self.tenant.pk)

    def get_object(self, queryset=None):

        self.kwargs.update(
            {self.slug_url_kwarg: bson.ObjectId(self.user.pk)})
        return super().get_object(queryset)

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)

        if self.user.groups.filter(name=models.CLIENT_GROUP).count() == 1:
            self.form_class = forms.ClientUpdateForm
            self.model = models.Client
        
        elif self.user.groups.filter(name=models.DEV_GROUP).count() == 1:
            self.form_class = forms.DeveloperUpdateForm
            self.model = models.Developer

    def get_template_names(self):

        template_name = "mws_main/update_{}.html"

        if self.is_client:
            return template_name.format("client")
        
        elif self.is_developer:
            return template_name.format("developer")
            
        elif self.is_admin:
            return template_name.format("admin")


def download_service(request, repo_addr, service_id):

    try:
        service = models.Service.objects.get(_id=bson.ObjectId(service_id))
    except (models.Service.DoesNotExist,
            bson.objectid.InvalidId):
        raise Http404()

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = BASE_DIR + service.package.url
    path = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filepath)

    response = HttpResponse(path, content_type=mime_type)
    response['Content-Disposition'] = f"attachment; filename={service.name}"

    return response
