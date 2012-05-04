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
