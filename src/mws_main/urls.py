from django.urls import path, include

from . import views

app_name = "mws_main"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("repo/<str:repo_addr>/",
         include(
             [
                 path("",
                      views.RepoHomeView.as_view(),
                      name="repo_home"),
    
                 path("login/",
                      views.LoginView.as_view(),
                      name="login"),
    
                 path("logout/",
                      views.LogoutView.as_view(),
                      name="logout"),
    
                 path("signup/",
                      views.SignupView.as_view(),
                      name="signup"),
    
                 path("signup-success/",
                      views.SignupSuccessView.as_view(),
                      name="signup_success"),
    
                 path("password-reset/",
                      views.PasswordResetView.as_view(),
                      name="password_reset"),
    
                 path("password-reset-done/",
                      views.PasswordResetDoneView.as_view(),
                      name="password_reset_done"),
    
                 path("password-reset-confirm/",
                      views.PasswordResetConfirmView.as_view(),
                      name="password_reset_confirm"),
    
                 path("password-reset-complete/",
                      views.PasswordResetCompleteView.as_view(),
                      name="password_reset_complete/"),

    
                 path("<str:pk>/",
                      views.ServiceDetailView.as_view(),
                      name="service_detail"),

                 path("clients/<str:client_id>/",
                      views.ClientDetailView.as_view(),
                      name="client_detail"),

                 path("developers/<str:developer_id>/",
                      views.DeveloperDetailView.as_view(),
                      name="developer_detail"),
         
                 path("admin/add-dev/",
                      views.AddDeveloperView.as_view(), name="add_developer"),
             ])),
]
