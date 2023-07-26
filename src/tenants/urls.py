from django.urls import path

import tenants.views as views

app_name = "tenants"
urlpatterns = [
    path("register/", views.RegistrationView.as_view(), name="registration"),
    path("completed-registration/", views.CompletedRegView.as_view(), name="completed"),
    path("my-repo/", views.MyRepoView.as_view(), name="repo info"),
    path("my-agreements/", views.MyAgreementsView.as_view(), name="agreements"),
    path("edit-repo/", views.EditRepoView.as_view(), name="edit repo"),
]
