

class CachingDatabaseError(Exception):
    """
    There was some problem when adding a database setting to Django
    global variables.
    """
    pass


class TenantRegistrationError(Exception):
    pass
