from djongo import models
from django.utils.translation import gettext_lazy as _
import django.contrib.auth.models as auth_models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.hashers import make_password
from django.apps import apps
from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings

import datetime

from mws_metadata.models import StoreMetadata


class Tenant(models.Model):
    """
    Represent the core data of those whose services
    are hosted in the platform. 

    A tenant are the users of their part of the platform,
    the resources used by them and thier clients (not
    implemented yet).
    """
    
    _id = models.ObjectIdField()

    name = models.CharField(
        "store name",
        max_length=25,
        blank=False,
    )

    store_url = models.CharField(
        max_length=25,
        blank=False,
        unique=True,
        help_text="Address to the tenant store.",
    )

    metadata = models.OneToOneField(
        StoreMetadata,
        on_delete=models.CASCADE,
    )

    objects = models.DjongoManager()

    def __str__(self):
        return self.name


def register_tenant(name, url):
    """
    Create a new tenant instance in the database.
    """

    metadata = StoreMetadata.objects.create()
    return Tenant.objects.create(
        name=name,
        store_url=url,
        metadata=metadata,
    )

class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):

    use_in_migrations = True
    
    def create_user(self, username, email, tenant, password=None, **extra_fields):

        if not username:
            raise ValueError("The given username must be set")
        if not (tenant
                and Tenant.objects.exists(pk=tenant)):
            raise ValueError("The given tenant must be set and exists")

        email = self.normalize_email(email)

        # Inspired by the original Django UserManager
        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        username = GlobalUserModel.normalize_username(username)
        user = self.model(
            username=username,
            email=email,
            tenant=tenant,
            **extra_fields
        )
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_superuser():
        """Superusers has not been established in the app."""
        pass

        
class User(TenantAwareModel, AbstractBaseUser, auth_models.PermissionsMixin):
    """
    Represents a user that is associated with one and
    only one tenant. Its username is composed of the 
    tenant id and a typical username separated by two dots (:).

    With this approach, users with the
    same username can exist if they are in different tenants,
    ensuring tenant isolation.
    """

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 75 characteres or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last_name"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), blank=True)
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active."
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "tenant"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def get_full_name(self):
        """
        Return the first name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
        
    def get_username(self):

        if ':' not in self.username:
            return self.username
        else:
            return self.username.split(':')[1]

    def save(self, *args, **kwargs):
        """
        Before saving the instance to the DB, the username
        must be composed of the tenant id and the username.
        """

        if ':' not in self.username:
            self.username = f"{self.tenant._id}:{self.username}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_username()})"


def get_user_group(group_name, codenames=None):
    """
    Return the group of the users whose model is given.

    If it doesn't exist, it is created.

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
                 "view_admin_service",
                 "change_service",
                 "delete_service",
                 "add_developer",
                 "view_developer",
                 "view_admin_developer",
                 "change_developer",
                 "delete_developer",
                 "add_client",
                 "view_client",
                 "view_admin_client",
                 "change_client",
                 "delete_client",
                 "view_tenant",
                 "change_tenant",]
    return get_user_group(ADMIN_GROUP, codenames)


class TenantAdmin(User):
    """
    Administrator of a tenant. It's the only user who can manage
    the core information of its tenant. 
    """

    _id = models.ObjectIdField()

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)
        group = get_admin_group()

        if not self.groups.filter(name=group.name).exists():
            self.groups.add(group)
