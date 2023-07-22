from .models import Tenant

def tenant_from_request(request):
    hostname = request.get_host().split(':')[0].lower()
    repo_addr = hostname.split('/')[1]
    return Tenant.objects.filter(repo_addr=repo_addr).first()
