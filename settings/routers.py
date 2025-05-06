class ReadOnlyRouter:
    """
    A router to control all database operations on models in certain tables.
    """

    # List of table names that should be read from the read-only database
    readonly_tables = ['all_routes']

    def db_for_read(self, model, **hints):
        """
        Routes read operations for specific tables to the read-only database.
        """
        if model._meta.db_table in self.readonly_tables:
            return 'chartr'
        return None

    def db_for_write(self, model, **hints):
        """
        Prevent write operations on the read-only tables.
        """
        if model._meta.db_table in self.readonly_tables:
            raise Exception("Attempted write on read-only table.")
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the readonly_tables is not involved.
        """
        if obj1._meta.db_table in self.readonly_tables or \
            obj2._meta.db_table in self.readonly_tables:
            return False
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Do not allow migrations on the read-only database.
        """
        if db == 'chartr':
            return False
        return True
