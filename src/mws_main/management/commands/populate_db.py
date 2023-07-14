import random
import names
import os

from django.utils import lorem_ipsum
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.core.files.temp import NamedTemporaryFile
from django.utils.datastructures import MultiValueDict
from django.contrib.auth.hashers import make_password

import tenants.models as tmodels
import tenants.forms as tforms
import mws_main.models as mmodels
import mws_main.forms as mforms

MAX_TENANTS = 5
# Dummy password and email
PASSWD = "Ab12345678"
ADMIN_EMAIL = "admin@test.com"

def generate_user():

    user = {"first_name": names.get_first_name()}
    user["last_name"] = names.get_last_name()
    user["username"] = "_".join([user["first_name"], user["last_name"]]).lower() + str(random.randint(1, 10000000))
    user["email"] = f"{user['username']}@test.com"
    user["password1"] = PASSWD

    return user


class Command(BaseCommand):

    help = (
        "Populates the application with multiple tenants and sample data"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "ntenants",
            type=int,
            choices=range(1, MAX_TENANTS + 1),
            default=MAX_TENANTS,
            metavar="N",
            help="Number of tenants to populate."
        )

    def handle(self, *args, **options):

        possible_subdomains = [f"tenant{nstore}" for nstore in range(1, MAX_TENANTS + 1)]
        BOUNDS = {
            "service": (10, 13),
            "client": (9, 20),
            "developer": (4, 8),
            "package": (1, 6),
            "acquired_services": (0, 4),
            "assigned_services": (1, 5),
        }

        def get_number(bound_t):
            """Return a random element in the selected bound."""
            bound = BOUNDS[bound_t]
            return random.randrange(bound[0], bound[1])

        PREFIX_STORE = ["", "mega", "super", "my", "the", "a"]
        STORE_MAIN_NAMES = ["repo", "store", "app store", "play store", "tech app"]

        # Generate store names
        store_names = [" ".join([prefix, name]) for prefix in PREFIX_STORE for name in STORE_MAIN_NAMES]

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
        
        # Generate tenants
        ntenants = options["ntenants"]
        generated_snames = random.sample(store_names, ntenants)

        for i in range(ntenants):

            store_name = generated_snames[i]
            self.stdout.write(f"Creating store {i}: {store_name}...")

            subdomain = possible_subdomains[i]
            tenant = tmodels.register_tenant(
                name=store_name.title(),
                subdomain=subdomain,
                email=ADMIN_EMAIL,
            )

            # Generate developers
            self.stdout.write("\tCreating developers...")
            ndevs = get_number("developer")
            developers = []
        
            for i_dev in range(ndevs):
                self.stdout.write(f"\t\tCreating developer {i_dev}...")
                user = generate_user()
                
                dev = mmodels.Developer.objects.create(
                    first_name=user["first_name"],
                    last_name=user["last_name"],
                    username=user["username"],
                    password=make_password(user["password1"]),
                    email=user["email"]
                )

                developers.append(dev)

            # Generate clients
            self.stdout.write("\tCreating clients...")
            nclients = get_number("client")

            for i_client in range(nclients):
                self.stdout.write(f"\t\tCreating client {i_client}...")
                user = generate_user()

                mmodels.Client.objects.create(
                    first_name=user["first_name"],
                    last_name=user["last_name"],
                    username=user["username"],
                    password=make_password(user["password1"]),
                    email=user["email"]
                )
                
            # Generate services
            self.stdout.write("\tCreating services...")
            nservices = get_number("service")
            service_names = random.sample(SERVICE_NAMES, nservices)

            for i_service, service_name in enumerate(service_names):
            
                self.stdout.write(f"\t\tCreating service {i_service}: {service_name}...")
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
        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {ntenants} tenants.")
        )
