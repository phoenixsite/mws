import time

from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
import  mws_main.models as mmodels

class StatsMiddleware:
    """
    Calculate the time passed since the request is received
    until a response is sent.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        start_time = time.time()        
        response = self.get_response(request)
        duration = time.time() - start_time
        response["X-Page-Generation_duration-ms"] = int(duration * 1000)
        return response


def is_usertype(user, user_model):
    return True if user.groups.filter(name=user_model.group_name).exists() else False

def is_client(user):
    return is_usertype(user, mmodels.Client)

def is_developer(user):
    return is_usertype(user, mmodels.Developer)

def is_admin(user):
    return is_usertype(user, mmodels.TenantAdmin)
    

class UserTypeMiddleware:
    """
    Check the type of the authenticated user.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if not hasattr(request, "user"):
            raise ImproperlyConfigured(
                "The user type middleware requires Django authentication "
                "middleware to be installed. Edit your MIDDLEWARE setting to "
                "insert "
                "'django.contrib.sessions.middleware.AuthenticationMiddleware' before "
                "'mws_main.middleware.UserTypeMiddleware'."
            )

        request.is_client = request.is_developer = request.is_admin = False
        
        if request.user.is_authenticated:
            request.is_client = is_client(request.user)

            if not request.is_client:
                request.is_developer = is_developer(request.user)

                if not request.is_developer:
                    request.is_admin = is_admin(request.user)

                    if not request.is_admin:
                        raise SuspiciousOperation(
                            "A user who is not a client, developer or admin"
                            "has logged."
                        )
                    else:
                        request.user = request.user.tenantadmin
                    
                else:
                    request.user = request.user.developer
            else:
                request.user = request.user.client
        
        response = self.get_response(request)
        return response
