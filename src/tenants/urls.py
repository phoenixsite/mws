from django.urls import path

from . import views

app_name = "tenants"
urlpatterns = [
    path("register/", views.registration, name="registration"),
    path("my-repo/", views.repo_info, name="repo info"),
    path("my-agreements/", views.agreements, name="agreements"),
    path("edit-repo/", views.edit_repo, name="edit repo"),
]
