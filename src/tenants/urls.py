from django.urls import path

import tenants.views as views

app_name = "tenants"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    
    path("register/",
         views.RegistrationView.as_view(),
         name="registration"),
    
    path("completed-registration/",
         views.CompletedRegView.as_view(),
         name="completed"),
]
