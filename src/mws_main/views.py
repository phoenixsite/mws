from django.shortcuts import render
from django.views import View
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import (
    UserPassesTestMixin,
    LoginRequiredMixin,)
from django.contrib.auth.models import User
from django.http import Http404

from mws_main.models import Developer, Client
from tenants.utils import tenant_from_addr
from tenants.models import Tenant, TenantAdmin

class HomeView(TemplateView):
    template_name = "mws_main/home.html"

    

class TenantView(LoginRequiredMixin, UserPassesTestMixin, View):
    def setup(self, request, *args, **kwargs):

        super().setup(request, *args, **kwargs)
        
        try:
            self.tenant = tenant_from_addr(self.kwargs['repo_addr'])
        except Tenant.DoesNotExist:
            raise Http404("The repository does not exists")
        
        if self.tenant:
            self.raise_exception = False
            self.login_url = f"/repo/{kwargs['repo_addr']}/login/"
        
        self.is_admin = False
        self.is_developer = False
        self.is_client = False
        self.user = None
        self.UserModel = None

        # The User heir class of the user must be found
        tenant_models = [Client, Developer, TenantAdmin]

        # Also, we need to identify the role of the user within
        # the repository with the same procedure
        user_group = [self.is_client, self.is_developer, self.is_admin]

        for i, UserModel in enumerate(tenant_models):
            try:
                self.user = UserModel.objects.select_related().get(
                    username=self.request.user.username)
            except UserModel.DoesNotExist:
                continue
            else:
                # If found, stop searching
                self.UserModel = UserModel
                user_group[i] = True
                break
                        
            
    def test_func(self):
        return self.user.tenant == self.tenant._id if self.user else False



class RepoHomeView(TenantView, TemplateView):
    template_name = "repo-home.html"

    def get(self, request, *args, **kwargs):
        pass
        

class AddDeveloperView(TenantView, TemplateView):
    pass
