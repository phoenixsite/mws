
class MetadataRouter:
    """
    A router that control all database operations on models
    in the mws_metadata app.
    """

    route_app_labels = {"mws_metadata"}

    def db_for_read(self, model, **hints):
        """
        Attempts to read mws_metadata models go to 'metadata'.
        """

        if model._meta.app_label in self.route_app_labels:
            return "metadata"
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write mws_metadata models go to 'metadata'.
        """

        if model._meta.app_label in self.route_app_labels:
            return "metadata"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the 'mws_metadata' apps is
        involved.
        """

        if (
                obj1._meta.app_label in self.route_app_labels
                or obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the mws_metadata app only appear in the 'metadata'
        database.
        """

        if app_label in self.route_app_labels:
            return db == 'metadata'

        if db == 'metadata':
            return False
        
        return None


class DefaultRouter:

    def db_for_read(self, model, **hints):
        return "default"

    def db_for_write(self, model, **hints):
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the default pool.
        """
        db_set = {"default"}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        All non-mws_metadata models end up in this pool.
        """
        return True
