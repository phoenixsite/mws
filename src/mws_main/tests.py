from django.test import TestCase
import mws_main.utils as utils
import tenants.models as tmodels
import os

class PackageTestCase(TestCase):

    TEST_DIR = "mws_main/test_files/"
    APK_DIR = "APK/"
    IPA_DIR = "IPA/"

    def packages_creation(self, filenames):
        """
        Test the creation of packages given a list of 
        pacakges filenames.
        
        :param filename_sols: Filenames of the packages.
        :type filename_sols: list of str
        """
        
        for filename in filenames:
            
            package = utils.ParsedPackage(filename)
            print(package)

    def test_apk_files(self):
        """Test the parsing of APK packages."""
        base_path = f"{self.TEST_DIR}{self.APK_DIR}"
        filenames = [f for f in os.listdir(base_path)
                     if os.path.isfile(os.path.join(base_path, f))]
        
        filenames = [os.path.join(base_path, f) for f in filenames]
        self.packages_creation(filenames)

    def test_ipa_files(self):
        """Test the parsing of IPA packages."""
        base_path = f"{self.TEST_DIR}{self.IPA_DIR}"
        filenames = [f for f in os.listdir(base_path)
                     if os.path.isfile(os.path.join(base_path, f))]
        
        filenames = [os.path.join(base_path, f) for f in filenames]
        self.packages_creation(filenames)


"""
class ServiceTestCase(TestCase):

    def setUp(self):

        tenant = tmodels.register_tenant(
            "Repo5",
            "repo5",
            "123456789",
        )

        tenant_admin = tmodels.TenantAdmin(
            username="admin_repo5",
            email="admin_repo5@test.com",
            password="Ab12345678",
            first_name="Admin",
            last_name="Admin",
        )

        tenant_admin.tenant = tenant
        tenant_admin.save()
"""
