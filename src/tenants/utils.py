from .models import Tenant

def tenant_from_addr(repo_addr):
    return Tenant.objects.get(repo_addr=repo_addr)

def tenant_from_request(request):
    repo_addr = request.path.split('/')[1]
    return tenant_from_addr(repo_addr)
