from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "mws_main"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("repo/<str:repo_addr>/",
         views.RepoHomeView.as_view(), name="repo_home"),
    path("repo/<str:repo_addr>/login/",
         auth_views.LoginView.as_view(next_page="repo/<str:repo_addr>"),
         name="repo_login"),
    path("repo/<str:repo_addr>/logout/",
         auth_views.LogoutView.as_view(),
         name="repo_logout"),
    path("repo/<str:repo_addr>/password-reset",
         auth_views.PasswordResetView.as_view(),
         name="password_reset"),
    path("repo/<str:repo_addr>/password-reset-done",
         auth_views.PasswordResetDoneView.as_view(),
         name="password_reset_done"),
    path("repo/<str:repo_addr>/password-reset-confirm",
         auth_views.PasswordResetConfirmView.as_view(),
         name="password_reset_confirm"),
    path("repo/<str:repo_addr>/password-reset-complete",
         auth_views.PasswordResetCompleteView.as_view(),
         name="password_reset_complete"),

    path("repo/<str:repo_addr>/admin/add-dev/",
         views.AddDeveloperView.as_view(), name="add_developer"),  
]
