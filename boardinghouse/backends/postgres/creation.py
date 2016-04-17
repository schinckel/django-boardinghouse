from django.db.backends.postgresql import creation

from boardinghouse.schema import activate_template_schema


class DatabaseCreation(creation.DatabaseCreation):
    # We need to activate the template schema before (de)serializing, so the tables exist.
    def serialize_db_to_string(self):
        activate_template_schema()
        return super(DatabaseCreation, self).serialize_db_to_string()

    def deserialize_db_from_string(self, data):
        activate_template_schema()
        super(DatabaseCreation, self).deserialize_db_from_string(data)
