from django.urls import path

import tenants.views as views

app_name = "tenants"
urlpatterns = [
    path("register/", views.RegistrationView.as_view(), name="registration"),
    path("completed-registration", views.CompletedReg.as_view(), name="completed"),
    path("my-repo/", views.repo_info, name="repo info"),
    path("my-agreements/", views.agreements, name="agreements"),
    path("edit-repo/", views.edit_repo, name="edit repo"),
]
