from django.urls import path

from . import views

app_name = "mws_main"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
]

