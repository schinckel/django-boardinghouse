CREATE OR REPLACE FUNCTION clone_schema(source_schema text, dest_schema text)
RETURNS void AS $$

DECLARE
  object text;
  buffer text;
  default_ text;
  column_ text;
  trigger_ text;
  view_ record;
  constraint_ record;
BEGIN
  SET search_path TO public;

  RAISE NOTICE 'CREATE SCHEMA %', dest_schema;
  EXECUTE 'CREATE SCHEMA ' || dest_schema ;

  -- TODO: Find a way to make this sequence's owner is the correct column.
  -- Not a huge priority.
  FOR object IN
    SELECT sequence_name::text
      FROM information_schema.SEQUENCES
     WHERE sequence_schema = source_schema
  LOOP
    RAISE NOTICE 'CREATE SEQUENCE %.%', dest_schema, object;
    EXECUTE 'CREATE SEQUENCE ' || dest_schema || '.' || object;
  END LOOP;

  -- Iterate through all tables in the source schema.
  FOR object IN
    SELECT table_name::text
      FROM information_schema.TABLES
     WHERE table_schema = source_schema
       AND table_type = 'BASE TABLE'
  LOOP

    -- Create a table with the relevant data in the new schema.
    buffer := dest_schema || '.' || object;
    RAISE NOTICE 'CREATE TABLE % (LIKE %.% INCLUDING ALL)', buffer, source_schema, object;
    EXECUTE 'CREATE TABLE ' || buffer || ' (LIKE ' || source_schema || '.' || object || ' INCLUDING ALL)';

    -- Ensure any default values that refer to the old schema now refer to the new schema.
    FOR column_, default_ IN
      SELECT column_name::text,
             replace(column_default::text, source_schema, dest_schema)
        FROM information_schema.COLUMNS
       WHERE table_schema = dest_schema
         AND table_name = object
         AND column_default LIKE 'nextval(%' || source_schema || '%::regclass)'
    LOOP
      RAISE NOTICE 'ALTER TABLE % ALTER COLUMN % SET DEFAULT %', buffer, column_, default_;
      EXECUTE 'ALTER TABLE ' || buffer || ' ALTER COLUMN ' || column_ || ' SET DEFAULT ' || default_;
    END LOOP;

    -- Ensure any triggers also come across...
    -- We can do the same trick we did for the default values.
    FOR trigger_ IN
      SELECT replace(pg_catalog.pg_get_triggerdef(oid, false)::text,
                     source_schema, dest_schema)
        FROM pg_catalog.pg_trigger
       WHERE tgrelid = (source_schema || '.' || object)::regclass::pg_catalog.oid
     AND NOT tgisinternal
    LOOP
      RAISE NOTICE '%', trigger_;
      EXECUTE trigger_;
    END LOOP;

  END LOOP;

  -- Copy across any foreign key constraints. This happens after creating
  -- all of the tables.
  FOR constraint_ IN
  WITH source_tables AS (
    SELECT table_name,
           (source_schema || '.' || table_name)::regclass AS oid
      FROM information_schema.tables
     WHERE table_schema = source_schema
  )
    SELECT conname AS name,
           replace(pg_catalog.pg_get_constraintdef(r.oid, true),
                   source_schema, dest_schema) AS definition,
           t.table_name
      FROM source_tables t
INNER JOIN pg_catalog.pg_constraint r
        ON (r.conrelid = t.oid)
       AND r.contype = 'f'
  LOOP
    RAISE NOTICE 'ALTER TABLE %.% ADD CONSTRAINT % %', dest_schema, constraint_.table_name, constraint_.name, constraint_.definition;
    EXECUTE 'ALTER TABLE ' || dest_schema || '.' || constraint_.table_name || ' ADD CONSTRAINT ' || constraint_.name || ' ' || constraint_.definition;
  END LOOP;

  -- Finally, repeat for any views.
  FOR view_ IN
    SELECT viewname,
           definition
      FROM pg_views
     WHERE schemaname = source_schema
  LOOP
    RAISE NOTICE 'CREATE VIEW %.% AS %', dest_schema, quote_ident(view_.viewname), replace(view_.definition, source_schema || '.', dest_schema || '.');
    EXECUTE 'CREATE VIEW ' || dest_schema || '.' || quote_ident(view_.viewname) || ' AS ' ||
      replace(view_.definition, source_schema || '.', dest_schema || '.');
  END LOOP;

END;

$$ LANGUAGE plpgsql VOLATILE;