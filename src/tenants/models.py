from djongo import models


IRESOURCES = [
    ("CT", "CPU time"),
    ("ST", "Storage usage"),
]

class IResourceUsage(models.Model):

    res_name = models.CharField(
        "resource name",
        max_length=2,
        choices=IRESOURCES
    )

    class Meta:
        abstract = True

class SubsLoup(models.Model):

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    charge = models.DecimalField("money charge", decimal_places=3)
    usages = models.ArrayField(
        model_container=IResourceUsage
    )

    class Meta:
        abstract = True


class IResourcePlan(models.Model):

    res_name = models.CharField(
        "resource name",
        max_length=2,
        choices=IRESOURCES
    )

    limit = models.DecimalField("maximum usage", decimal_places=3)
    charge_per_unit = models.DecimalField(decimal_places=3)

    class Meta:
        abstract = True

class SubsAgreement(models.Model):

    date_regs = models.DateTimeField(
        "registration date",
        auto_now_add=True
    )
    end_date = models.DateTimeField()
    card_number = models.CharField(max_length=100, blank=False)
    plans = models.ArrayField(
        model_container=IResourcePlan
    )

    current_loup = models.EmbeddedField(
        model_container=SubsLoup
    )

    old_loups = models.ArrayField(
        model_container=SubsLoup
    )

    class Meta:
        abstract = True


class Tenant(models.Model):

    tenant_id = models.ObjectIdField()
    name = models.CharField(
        "repository name",
        max_length=25,
        blank=False,
        unique=True
    )
    repo_addr = models.CharField(
        "repository address",
        max_length=25,
        blank=False
    )
    url = models.URLField()
    email = models.EmailField()
    current_agree = models.EmbeddedField(
        model_container=SubsAgreement
    )
    old_agrees = models.ArrayField(
        model_container=SubsAgreement
    )


class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True
