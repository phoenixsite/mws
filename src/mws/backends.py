from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from mws_main.models import Client
from tenants.utils import tenant_from_addr

class TenantBackend(BaseBackend):
    """
    Authenticates against User and also checks that this
    user belongs to the given repository (tenant).
    """

    def authenticate(self, request, tenant_id, username, password):
        # The User heir class of the user must be found
        tenant_models = [Client, Developer, TenantAdmin]
        user = None
        
        for i, UserModel in enumerate(tenant_models):
            try:
                # select_related method is needed to fetch
                # the base User attributes in a single
                # access to the db
                user = UserModel.objects.select_related().get(
                    username=self.request.user.username)
            except UserModel.DoesNotExist:
                continue
            else:
                # If found, stop searching
                break
        
        if not user:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User.set_password(password)
        else:
            tenant = tenant_from_request(request)
            if (
                    tenant._id == user.tenant
                    and user.check_password(password)
                    and self.user_can_authenticate(user)):
                return user


    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None
