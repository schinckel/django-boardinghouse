from django.db.backends.postgresql_psycopg2.creation import *


class DatabaseCreation(DatabaseCreation):
    def sql_create_model(self, model, style, known_models=set(), schema="__template__"):
        final_output, pending_references = super(DatabaseCreation, self).sql_create_model(model, style, known_models)
        if model._is_schema_aware:
            for i in range(len(final_output)):
                final_output[i] = final_output[i].replace("CREATE TABLE ", 'CREATE TABLE "%s".' % schema)
        return final_output, pending_references