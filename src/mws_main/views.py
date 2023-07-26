from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import (
    UserPassesTestMixin,
    LoginRequiredMixin,)

from mws_main.models import Developer, Client


class HomeView(TemplateView):
    template_name = "mws_main/home.html"

class HasLoggedInMixin(UserPassesTestMixin):
    pass
    """
    def test_func(self):

        try:
            user = User.objects.get(self.request.username
    """ 
