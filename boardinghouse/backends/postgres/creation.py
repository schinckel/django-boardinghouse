from django.db.backends.postgresql_psycopg2.creation import *

class DatabaseCreation(DatabaseCreation):
    """
    The only change we make to the original Postgres `DatabaseCreation`
    class is to allow a schema name.
    """
    def sql_create_model(self, model, style, known_models=set(), schema="__template__"):
        """
        Override the creation of a table for a schema-aware model, so that
        it inserts it into the correct schema.
        """
        from ...schema import is_shared_model
        
        final_output, pending_references = super(DatabaseCreation, self).sql_create_model(model, style, known_models)
        if not is_shared_model(model):
            for i in range(len(final_output)):
                final_output[i] = final_output[i].replace("CREATE TABLE ", 'CREATE TABLE "%s".' % schema)
        return final_output, pending_references