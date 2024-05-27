from django.urls import path, include, register_converter

from . import views

app_name = "mws_main"
urlpatterns = [
    path("store/",
         include(
             [
                 path("",
                      views.StoreHomeView.as_view(),
                      name="store_home"),

                 path("login/",
                      views.LoginView.as_view(),
                      name="login"),

                 path("logout/",
                      views.LogoutView.as_view(),
                      name="logout"),

                 path("signup/",
                      views.ClientCreateView.as_view(),
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
                      name="password_reset_complete"),

                 path("admin/clients/<str:pk>/",
                      views.ClientAdminDetailView.as_view(),
                      name="client_detail"),

                 path("admin/developers/<str:pk>/",
                      views.DeveloperAdminDetailView.as_view(),
                      name="developer_detail"),

                 path("admin/service/<str:pk>/",
                      views.ServiceAdminDetailView.as_view(),
                      name="service_admin_detail"),

                 path("admin/add-dev/",
                      views.DeveloperCreateView.as_view(),
                      name="add_developer"),

                 path("services/<int:pk>/",
                      views.ServiceDetailView.as_view(),
                      name="service_detail"),

                 path("add-service/",
                      views.ServiceCreateView.as_view(),
                      name="add_service"),

                 path("view-profile/",
                      views.UserDetailView.as_view(),
                      name="view_profile"),

                 path("update-profile/",
                      views.UserUpdateView.as_view(),
                      name="update_profile"),

                 path("download-service/<str:service_id>/<str:package_id>",
                      views.DownloadServiceView.as_view(),
                      name="download_service"),

                 path("update-package/<str:service_id>/<str:package_id>",
                      views.UpdatePackageView.as_view(),
                      name="update_package"),

                 path("update-service/<str:pk>/",
                      views.UpdateServiceView.as_view(),
                      name="update_service"),

                 path("store-info/",
                      views.StoreInfoView.as_view(),
                      name="store_info"),

                 path("update-store-info/",
                      views.UpdateStoreInfo.as_view(),
                      name="update_store")
             ])),
]
