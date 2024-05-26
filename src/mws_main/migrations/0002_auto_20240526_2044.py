from django.db import migrations

ADMIN_GROUP = "admins"
CLIENT_GROUP = "clients"
DEV_GROUP = "developers"

def create_groups(apps, schema_editor):

    groups = {
        ADMIN_GROUP: [
            "add_service", "view_service", "view_admin_service",
            "change_service", "delete_service", "add_developer",
            "view_developer", "view_admin_developer", "change_developer",
            "delete_developer", "add_client", "view_client",
            "view_admin_client", "change_client", "delete_client",
            "view_metadata", "change_metadata",
        ],
        CLIENT_GROUP: [
            'view_service', 'view_client', 'change_client'
        ],
        DEV_GROUP: [
            'view_client', 'view_service', 'view_admin_service',
            'add_service', 'change_service', 'view_developer',
            'change_developer'
        ],
    }
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    for group_name, codenames in groups.items():

        permissions = Permission.objects.filter(codename__in=codenames)
        group = Group.objects.create(name=group_name)
        group.permissions.add(*permissions)
        group.save()

        
class Migration(migrations.Migration):

    dependencies = [
        ('mws_main', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]
