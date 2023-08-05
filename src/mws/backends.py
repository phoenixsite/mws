from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User

class TenantBackend(BaseBackend):
    """
    Authenticates against User and also checks that this
    user belongs to the given repository (tenant).
    """

    def authenticate(self, request, tenant_id, username, password):
        username = f"{tenant_id}:{username}"

        try:
            user = User.objects.select_related().get(
                username=username)
        except User.DoesNotExist:
            return None
        
        if not user:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User.set_password(password)
        else:
            if user.check_password(password):
                return user


    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user
