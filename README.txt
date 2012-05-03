Django Multi-Schema
====================

Use Postgres Schemas for multi-tenant applications (or other segmenting).



Migrations
-----------

pre_migrate (app)

  * find any models in app that are _not_ schema_aware.
    set their db_table to "public"."<db_table>"
  
  * (db) set the search path to __template__,public

post_migrate (app)

  * find any models in app that are not schema_aware
    remove a prefix of `"public".`
  
  * (db) set the search path to public.

ran_migration (app, migration, method)

  * for schema in Schema.objects.all()
    * (db) set the search path to schema.schema,public
    * re-run the migration
  * (db) set the search path to __template__,public


Syncing DB
-----------

Before we syncdb, we need to:

  * look for models that will be created
  * if a model is not schema aware, set it's db_table to public.
  * (db) set the search path to __template__,public
  
post_syncdb (sender, app, created_models)

  * if any models are schema_aware
  * for schema in Schema.objects.all()
    * activate schema
    * for each model in created_models that is schema aware
      * issue create statements for model

Creating New Schema
------------

  * (db) create the new schema
  * (db) copy the required table structure into the new schema
  