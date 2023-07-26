from djongo import models
from django.utils.translation import gettext_lazy as _
import django.contrib.auth.models as auth_models
from django import forms


class ResourcesType(models.TextChoices):
    CT = "CT", _("CPU time")
    ST = "ST", _("Storage usage")


class IResourcePlan(models.Model):

    res_name = models.CharField(
        "resource name",
        max_length=2,
        choices=ResourcesType.choices
    )
    
    limit = models.FloatField("maximum usage")
    charge_per_unit = models.FloatField()

    class Meta:
        abstract = True

    def __str__(self):
        return self.res_name


class DefaultSubsAgreement(models.Model):
    """
    Define some default conditions and limits of usage of the
    application that a tenant must agree onto use the
    platform.

    A subscription agreement includes a time duration
    when the agreement is effective. It also includes
    some resource limits.
    """

    name = models.CharField(max_length=25, unique=True,
                            help_text="Agreement name")
    plans = models.ArrayField(
        model_container=IResourcePlan,
        help_text="Show the maximum usage for a resource that can be used"
    )
    
    duration = models.DurationField(
        help_text="Units in days"
    )
    
    objects = models.DjongoManager()

    def __str__(self):
        return f"Agreement {self.name}"

    class Meta:
        verbose_name = "available subscription agreement"

    
class IResourceUsage(models.Model):

    res_name = models.CharField(
        "resource name",
        max_length=2,
        choices=ResourcesType.choices
    )
    usage = models.FloatField("resource usage", default=0)

    class Meta:
        abstract = True

class SubsLoup(models.Model):

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    charge = models.FloatField()
    usages = models.ArrayField(
        model_container=IResourceUsage)

    class Meta:
        abstract = True


class SubsAgreement(models.Model):
    """
    Define the conditions of usage that a tenant has
    signed to use the platformand that must be 
    fulfilled during a period of time.
    """

    date_regs = models.DateTimeField(
        "registration date",
        auto_now_add=True
    )
    end_date = models.DateTimeField()
    card_number = models.CharField(max_length=100, blank=False)
    plans = models.ArrayField(
        model_container=IResourcePlan)

    current_loup = models.EmbeddedField(
        model_container=SubsLoup)

    old_loups = models.ArrayField(
        model_container=SubsLoup
    )

    class Meta:
        abstract = True
        verbose_name = "subscription agreement"


class Tenant(models.Model):
    """
    Represent the core data of those whose services
    are hosted in the platform. 

    A tenant are the users of their part of the platform,
    the resources used by them and thier clients.
    """
    
    _id = models.ObjectIdField()

    name = models.CharField(
        "repository name",
        max_length=25,
        blank=False,
        unique=True)

    repo_addr = models.CharField(
        "repository address",
        max_length=25,
        blank=False,
        help_text="address to the hosted tenant store"
    )
    
    current_agree = models.EmbeddedField(
        model_container=SubsAgreement,
        null=False,
        blank=False)
    
    old_agrees = models.ArrayField(
        model_container=SubsAgreement,
        null=False
    )

    def __str__(self):
        return self.name


def register_tenant(name, repo_addr, card_number, subs_agree_name):
    """
    Return the tenant created given its properties and the
    choosen subscription agreement.

    Create a new tenant instance in the database.
    """

    # Choosen subscription agreement
    def_agree = models.DefaultSubsAgreement.objects.get(
        name=subs_agree_name)

    # Per-resource consumption in the first month
    iresources = [
        {
            'res_name': plan['res_name'],
            'usage': 0,
        } for plan in def_agree.plans]
            
    # The first month loup
    empty_loup = {
        'start_date': timezone.now(),
        'end_date': timezone.now() + datetime.timedelta(days=30),
        'charge': 0,
        'usages': iresources
    }

    subs_agree = {
        'date_regs': timezone.now(),
        'end_date': timezone.now() + def_agree.duration,
        'card_number': card_number,
        'plans': def_agree.plans,
        'current_loup': empty_loup,
        'old_loups': []}

    return models.Tenant.objects.create(
        name=tenant_form.cleaned_data["name"],
        repo_addr=tenant_form.cleaned_data["repo_addr"],
        current_agree=subs_agree,
        old_agrees=[]
    )

class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class TenantAdmin(TenantAwareModel, auth_models.User):
    """
    Main user of a tenant. It's the only user who can manage
    the core information of its tenant. 
    """
    pass
