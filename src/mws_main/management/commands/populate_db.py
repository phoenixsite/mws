import random
import names
import os

from django.utils import lorem_ipsum
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

NSTORES = 5
possible_subdomains = [f"tenant{nstore}" for nstore in range(1, NSTORES+1)]
BOUNDS = {
    "service": (10, 13),
    "client": (9, 20),
    "developer": (4, 8),
    "package": (1, 6),
    "acquired_services": (0, 4),
    "assigned_services": (1, 5),
}

PREFIX_STORE = ["", "mega", "super", "my", "the", "a"]
STORE_MAIN_NAMES = ["repo", "store", "app store", "play store", "tech app"]

# Generate store names
store_names = [" ".join([prefix, name]) for prefix in PREFIX_STORE for name in STORE_MAIN_NAMES]

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
ADMIN_EMAIL = "admin@test.com"

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
    nstores = NSTORES
    generated_snames = random.sample(store_names, nstores)

    for i in range(nstores):

        store_name = generated_snames[i]
        print(f"Creating store {i}: {store_name}...")

        
        subdomain = possible_subdomains[i]
        tenant = tmodels.register_tenant(
            name=store_name.title(),
            subdomain_prefix=subdomain,
            email=ADMIN_EMAIL,
        )

        # Generate developers
        print("\tCreating developers...")
        ndevs = get_number("developer")
        developers = []
        
        for i_dev in range(ndevs):
            print(f"\t\tCreating developer {i_dev}...")
            user = generate_user()
            developer_form = mforms.DeveloperCreationForm(user)

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
            client_form = mforms.ClientCreationForm(user)

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
                "descrp": lorem_ipsum.sentence()}
                for package in packages]

            # Generate service info
            brief_descrp = lorem_ipsum.sentence()
            descrp = lorem_ipsum.paragraph()
            # Randomly select the developers assigned to this service
            nselected_devs = get_number("assigned_services")
            selected_devs = random.sample(developers, min(ndevs, nselected_devs))

            service = mmodels.create_service(
                service_name,
                brief_descrp,
                descrp,
                packages,
                None,
                selected_devs
            )


class Command(BaseCommand):

    help = "Populate the application with sample data"

    def handle(self, *args, **options):
        populate()
