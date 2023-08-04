from django.urls import path, include

from . import views

app_name = "mws_main"
urlpatterns = [
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
                 

                 path("admin/clients/<slug:slug>/",
                      views.ClientAdminDetailView.as_view(),
                      name="client_detail"),

                 path("admin/developers/<slug:slug>/",
                      views.DeveloperAdminDetailView.as_view(),
                      name="developer_detail"),

                 path("admin/add-dev/",
                      views.AddDeveloperView.as_view(),
                      name="add_developer"),

                 path("services/<slug:slug>/",
                      views.ServiceDetailView.as_view(),
                      name="service_detail"),

                 path("add-service/",
                      views.AddServiceView.as_view(),
                      name="add_service"),

                 path("view-profile/",
                      views.UserDetailView.as_view(),
                      name="view_profile"),

                 path("update-profile/",
                      views.UserUpdateView.as_view(),
                      name="update_profile"),

                 path("download-service/<str:service_id>",
                      views.download_service,
                      name="download_service"),
             ])),
]
