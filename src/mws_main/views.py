from django.views import View
from django.views.generic import (
    TemplateView,
    FormView,
    DetailView,
)
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
from django.shortcuts import get_object_or_404, render
from django.forms import ModelForm
from django.urls import reverse

import mws_main.models as models
import mws_main.forms as forms
from tenants.models import Tenant, TenantAdmin

class HomeView(TemplateView):
    template_name = "mws_main/home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context


class TenantLoginRequiredMixin(AccessMixin):
    """
    Verify that the current user is authenticated and 
    its tenant is the same as the view's tenant.
    """
    
    def dispatch(self, request, *args, **kwargs):
        
        if not (self.user.is_authenticated
            and self.user.tenant
            and self.tenant == self.user.tenant):

            return self.handle_no_permission()
            
        return super().dispatch(request, *args, **kwargs)


class TenantView(TemplateView):
    """
    Represent a tenant-dependant view, so the functionality
    of the view depends on the tenant that it is associated
    with.
    """

    def setup(self, request, *args, **kwargs):
        """
        Fetch the specific tenant of the repository given
        url in the request.
        """
        
        super().setup(request, *args, **kwargs)
        
        self.tenant = get_object_or_404(
            Tenant,
            repo_addr=self.kwargs['repo_addr'])
        
        if self.tenant:
            self.login_url = reverse("mws_main:login",
                                     args=[self.tenant.repo_addr])

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["tenant"] = self.tenant
        return context


class TenantUserView(TenantLoginRequiredMixin, TenantView):

    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)

        self.is_admin = False
        self.is_developer = False
        self.is_client = False
        self.user = self.request.user
        self.user.tenant = None
        self.UserModel = None

        # The User heir class of the user must be found
        tenant_models = [models.Client, models.Developer, TenantAdmin]

        # Also, we need to identify the role of the user within
        # the repository with the same procedure
        user_group = ["is_client", "is_developer", "is_admin"]

        for i, UserModel in enumerate(tenant_models):
            try:
                self.user = UserModel.objects.get(
                    user_ptr_id=self.request.user.id)
            except UserModel.DoesNotExist:
                continue
            else:
                
                # If found, stop searching and set
                # the type of user
                self.UserModel = UserModel
                setattr(self, user_group[i], True)
                break

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_client"] = self.is_client
        context["is_developer"] = self.is_developer
        context["is_admin"] = self.is_admin
        return context


class LoginView(auth_views.LoginView, TenantView):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.next_page = reverse("mws_main:repo_home",
                                 args=[self.tenant.repo_addr])


class LogoutView(auth_views.LogoutView, TenantView):
    template_name="registration/logout.html"


class SignupView(auth_views.RedirectURLMixin, FormView, TenantView):

    form_class = forms.ClientCreationForm
    template_name = "registration/signup.html"

    def setup(self, request, *args, **kwargs):
        
        super().setup(request, *args, **kwargs)
        self.initial = {'repo_addr': self.kwargs['repo_addr']}
        self.next_page = reverse("mws_main:signup_success",
                                args=[self.tenant.repo_addr])

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class SignupSuccessView(TenantView):
    template_name = "registration/signup-success.html"
        
class PasswordResetView(auth_views.PasswordResetView, TenantUserView):
    pass

class PasswordResetDoneView(auth_views.PasswordResetDoneView, TenantUserView):
    pass

class PasswordResetConfirmView(auth_views.PasswordResetConfirmView, TenantUserView):
    pass

class PasswordResetCompleteView(auth_views.PasswordResetCompleteView, TenantUserView):
    pass

class RepoHomeView(TenantUserView):
    template_name = "mws_main/repo-home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.is_client:
            context["services"] = models.Service.objects.filter(tenant_id=self.tenant._id)
            
        elif self.is_developer:
            context["services"] = models.Service.objects.filter(tenant_id=self.tenant._id)
            
        elif self.is_admin:
            context["services"] = models.Service.objects.filter(tenant=self.tenant._id)
            context["developers"] = models.Developer.objects.filter(tenant=self.tenant._id)
            context["clients"] = models.Client.objects.filter(tenant=self.tenant._id)

        return context

class ServiceDetailView(DetailView, TenantUserView):
    model = models.Service
    context_object_name = "service"

    def get_queryset(self):
        return models.Service.objects.filter(tenant=self.tenant.pk)


class ClientDetailView(DetailView, TenantUserView):
    model = models.Client
    context_object_name = "client"
    template_name = "mws_main/client_detail.html"
    #object = 

    def get_queryset(self):
        return models.Client.objects.filter(tenant=self.tenant.pk)

class DeveloperDetailView(DetailView, TenantUserView):
    model = models.Developer
    context_object_name = "developer"

    def get_queryset(self):
        return models.Developer.objects.filter(tenant=self.tenant.pk)

class AddDeveloperView(TenantUserView):
    pass

