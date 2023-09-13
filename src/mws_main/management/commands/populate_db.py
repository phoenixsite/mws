import random
import names
import loremipsum
import os

from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.core.files.temp import NamedTemporaryFile
from django.forms import formset_factory
from django.http import QueryDict
from django.utils.datastructures import MultiValueDict

import tenants.models as tmodels
import tenants.forms as tforms
import mws_main.models as mmodels
import mws_main.forms as mforms


BOUNDS = {
    "store": (7, 10),
    "service": (10, 13),
    "client": (9, 20),
    "developer": (4, 8),
    "package": (1, 6),
    "acquired_services": (0, 4),
    "assigned_services": (1, 5),
}

PREFIX_STORE = ["", "mega", "super", "my", "the", "a"]
STORE_MAIN_NAMES = ["repo", "store", "app store", "play store", "tech app"]

store_names = []

# Generate store names
for prefix in PREFIX_STORE:
    for name in STORE_MAIN_NAMES:
        store_names.append(" ".join([prefix, name]))

PASSWD = "Ab12345678"
PACKAGES_DIR = os.path.dirname(__file__) + "/_packages/"

packages_paths = os.listdir(PACKAGES_DIR)
packages_paths = [PACKAGES_DIR + package for package in packages_paths]
packages_paths = [os.path.normpath(package) for package in packages_paths]

SERVICE_NAMES = [
    "Simple Gallery Pro",
    "IPFS Lite",
    "Presence Publisher",
    "Meshenger",
    "Estado de F-Droid Build",
    "Unexpected keyboard",
    "Simple Text Editor",
    "Unciv",
    "Beat Feet",
    "Les Pas",
    "Mumla",
    "Ultrasonic",
    "openHAB Beta",
    "Catima",
    "Mis gastos",
    "Jellyfin"
]

def generate_user():

    user = {"first_name": names.get_first_name()}
    user["last_name"] = names.get_last_name()
    user["username"] = "_".join([user["first_name"], user["last_name"]]).lower() + str(random.randint(1, 10000000))
    user["email"] = f"{user['username']}@test.com"
    user["password1"] = user["password2"] = PASSWD

    return user

def get_number(bound_t):

    bound = BOUNDS[bound_t]
    return random.randrange(bound[0], bound[1])


def populate():

    # Generate stores (tenants)
    nstores = get_number("store")

    generated_snames = random.sample(store_names, nstores)

    for i, store_name in enumerate(generated_snames):

        print(f"Creating store {i}: {store_name}...")

        url = store_name.lower().replace(" ", "-") + str(random.randint(1, 100000))
        tenant = tmodels.register_tenant(
            name=store_name.title(),
            url=url
        )

        # Generate admins
        print("\tCreating admin...")
        user = generate_user()
        user["username"] = "admin"
        admin_form = tforms.AdminForm(user)

        if admin_form.is_valid():
            admin = admin_form.save(commit=False)
            admin.tenant = tenant
            admin.save()
        else:
            print(f"\tError: {admin_form.errors}")

        # Generate developers
        print("\tCreating developers...")
        ndevs = get_number("developer")
        developers = []
        
        for i_dev in range(ndevs):
            print(f"\t\tCreating developer {i_dev}...")
            user = generate_user()
            initial = {'store_url': tenant.store_url}
            developer_form = mforms.DeveloperCreationForm(user, initial=initial)

            if developer_form.is_valid():
                developer = developer_form.save()
                developers.append(developer)
            else:
                print(f"\t\tError: {developer_form.errors}")


        # Generate clients
        print("\tCreating clients...")
        nclients = get_number("client")
        clients = []

        for i_client in range(nclients):
            print(f"\t\tCreating client {i_client}...")
            user = generate_user()
            initial = {"store_url": tenant.store_url}
            client_form = mforms.ClientCreationForm(user, initial=initial)

            if client_form.is_valid():
                client = client_form.save()
                clients.append(client)
            else:
                print(f"\t\tError: {client_form.errors}")

        # Generate services
        print("\tCreating services...")
        nservices = get_number("service")
        service_names = random.sample(SERVICE_NAMES, nservices)

        for i_service, service_name in enumerate(service_names):
            
            print(f"\t\tCreating service {i_service}: {service_name}...")
            # Generate packages
            npackages = get_number("package")
            packages = random.sample(packages_paths, npackages)
            
            packages = [{
                "package": package,
                "descrp": loremipsum.generate(1, loremipsum.ParagraphLength.SHORT)}
                for package in packages]

            # Generate service info
            brief_descrp = loremipsum.generate(1, loremipsum.ParagraphLength.SHORT)
            descrp = loremipsum.generate(1, loremipsum.ParagraphLength.MEDIUM)
            # Randomly select the developers assigned to this service
            nselected_devs = get_number("assigned_services")
            selected_devs = random.sample(developers, nselected_devs)

            service = mmodels.create_service(
                service_name,
                brief_descrp,
                descrp,
                packages,
                tenant,
                None,
                selected_devs
            )


class Command(BaseCommand):

    def handle(self, *args, **options):
        populate()
