from djongo import models
from django.utils.translation import gettext_lazy as _
import django.contrib.auth.models as auth_models
from django import forms
from django.utils import timezone

import datetime

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

    def __str__(self):
        return self.name

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
        help_text="Address to the hosted tenant store."
    )
    
    current_agree = models.EmbeddedField(
        model_container=SubsAgreement,
        null=False,
        blank=False,
        help_text="Subscription plan chose to measure the resource usage."
    )
    
    old_agrees = models.ArrayField(
        model_container=SubsAgreement,
        null=False
    )

    objects = models.DjongoManager()

    def __str__(self):
        return self.name


def register_tenant(name, repo_addr, card_number, subs_agree_name):
    """
    Return the tenant created given its properties and the
    choosen subscription agreement.

    Create a new tenant instance in the database.
    """

    # Choosen subscription agreement
    def_agree = DefaultSubsAgreement.objects.get(
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

    return Tenant.objects.create(
        name=name,
        repo_addr=repo_addr,
        current_agree=subs_agree,
        old_agrees=[]
    )

class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class TenantUser(TenantAwareModel, auth_models.User):
    """
    Represents a user that is associated with one and
    only one tenant. Its username is composed of the 
    tenant id and a typical User username. 

    With this approach, there can be Users with the 
    same username if they are in different tenants,
    ensuring tenant isolation.
    """

    def get_username(self):
        username = super().get_username()

        if ':' not in username:
            return username
        else:
            return username.split(':')[1]

    def save(self, commit=True):
        """
        Before saving the instance to the DB, the username
        must be composed of the tenant id and the username.
        """
        
        if ':' not in self.username:
            self.username = f"{self.tenant._id}:{self.username}"

        super().save(commit)

    class Meta:
        abstract = True
        

def get_user_group(group_name, codenames=None):
    """
    Return the group of the users whose model is given.

    If it doesn't exist, it is created.
    
    :param class model: Model class of a user. Must inherit
    from django.contrib.auth.models.User.
    :param str group_name: Name of the group.
    :param list codenames: Permission codenames which will be
    included in the permissions group. It is ignored if the
    group is already created.
    """

    try:
        group = auth_models.Group.objects.get_by_natural_key(group_name)
    except auth_models.Group.DoesNotExist:

        permissions = auth_models.Permission.objects.filter(
            codename__in=codenames)

        group = auth_models.Group.objects.create(name=group_name)
        group.permissions.add(*permissions)
        group.save()

    return group


ADMIN_GROUP = "admin"

def get_admin_group():
    """
    Return the group of the administrators. If doesn't exist, 
    it is created.
    """

    codenames = ["add_service",
                 "view_service",
                 "change_service",
                 "delete_service",
                 "add_developer",
                 "view_developer",
                 "change_developer",
                 "delete_developer",
                 "add_client",
                 "view_client",
                 "change_client",
                 "delete_client",
                 "view_tenant",
                 "change_tenant",]
    return get_user_group(ADMIN_GROUP, codenames)

class TenantAdmin(TenantUser):
    """
    Administrator of a tenant. It's the only user who can manage
    the core information of its tenant. 
    """

    _id = models.ObjectIdField()

    def save(self, commit=True):

        super().save(commit)

        if commit:

            group = get_admin_group()
            self.groups.add(group)
