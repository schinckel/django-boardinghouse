from django.db.backends.postgresql_psycopg2 import creation


class DatabaseCreation(creation.DatabaseCreation):
    # We need to activate the template schema before (de)serializing, so the tables exist.

    # We need to import the deactivate_/activate_template_schema functions in the methods,
    # otherwise we can't mock them out for testing properly.

    # Should we reactivate whatever was active before we did this? Should we be doing that
    # elsewhere too?

    def serialize_db_to_string(self):
        from boardinghouse.schema import activate_template_schema, deactivate_schema

        activate_template_schema()
        result = super(DatabaseCreation, self).serialize_db_to_string()
        deactivate_schema()
        return result

    def deserialize_db_from_string(self, data):
        from boardinghouse.schema import activate_template_schema, deactivate_schema

        activate_template_schema()
        super(DatabaseCreation, self).deserialize_db_from_string(data)
        deactivate_schema()
