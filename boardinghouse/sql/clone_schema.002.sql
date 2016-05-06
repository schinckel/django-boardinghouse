CREATE OR REPLACE FUNCTION clone_schema(
  source_schema   text,
  dest_schema     text,
  include_records boolean
) RETURNS void AS $$

DECLARE
  source_schema_oid     oid;
  "sequence"            record;
  fq_table_name         text;
  object                text;
  buffer                text;
  default_              text;
  column_               text;
  trigger_              text;
  view_                 record;
  constraint_           record;
  function_             text;
  insert_query          text;

BEGIN
  -- I seemed to be getting errors if I didn't do this.
  SET search_path TO public;

  -- Check that the source_schema exists.
  SELECT oid INTO source_schema_oid
    FROM pg_namespace
   WHERE nspname = quote_ident(source_schema);
  IF NOT FOUND THEN
         RAISE NOTICE 'Source schema % does not exist.', source_schema;
         RETURN;
  END IF;

  -- Check that the dest_schema does not yet exist.
  PERFORM nspname
     FROM pg_namespace
    WHERE nspname = quote_ident(dest_schema);
  IF FOUND THEN
     RAISE NOTICE 'Destination schema % already exists', dest_schema;
     RETURN;
  END IF;

  RAISE INFO 'CREATE SCHEMA %', dest_schema;
  EXECUTE 'CREATE SCHEMA ' || quote_ident(dest_schema);

  -- Create sequences.
  -- TODO: Find a way to make this sequence's owner is the correct column: Not a huge priority.
  FOR buffer, object IN
    SELECT quote_ident(dest_schema) || '.' || quote_ident(sequence_name::text),
           quote_ident(sequence_name::text)
      FROM information_schema.sequences
     WHERE sequence_schema = quote_ident(source_schema)
  LOOP
    EXECUTE 'SELECT last_value,
                    max_value,
                    start_value,
                    increment_by,
                    min_value,
                    cache_value,
                    log_cnt,
                    is_cycled,
                    is_called
               FROM ' || quote_ident(source_schema) || '.' || object
       INTO "sequence";

      RAISE DEBUG 'CREATE SEQUENCE % ...', buffer;
    EXECUTE 'CREATE SEQUENCE ' || buffer
            || ' INCREMENT BY ' || "sequence"."increment_by"
            || ' MINVALUE '     || "sequence"."min_value"
            || ' MAXVALUE '     || "sequence"."max_value"
            || ' START WITH '   || "sequence"."start_value"
            || ' RESTART '      || "sequence"."min_value"
            || ' CACHE '        || "sequence"."cache_value"
            || CASE WHEN "sequence"."is_cycled"
                    THEN ' CYCLE '
                    ELSE ' NO CYCLE '
                    END
            || ';';
    IF include_records THEN
      RAISE DEBUG 'SELECT setval(%, %, %)', buffer,
                                            "sequence"."last_value",
                                            "sequence"."is_called";
      EXECUTE 'SELECT setval('
        || quote_literal(buffer)
        || ', ' || "sequence"."last_value"
        || ', ' || "sequence"."is_called"
        || ');';
    END IF;
  END LOOP;

  -- Create tables.
  FOR buffer, object IN
    SELECT quote_ident(dest_schema) || '.' || quote_ident(table_name::text),
           quote_ident(table_name::text)
      FROM information_schema.tables
     WHERE table_schema = quote_ident(source_schema)
       AND table_type = 'BASE TABLE'
  LOOP
    RAISE DEBUG 'CREATE TABLE % (LIKE %.% INCLUDING ALL)', buffer,
                                                           source_schema,
                                                           object;
    EXECUTE 'CREATE TABLE '
            || buffer
            || ' (LIKE ' || quote_ident(source_schema) || '.' || object
            || ' INCLUDING ALL);';

    IF include_records THEN
    -- RAISE NOTICE 'INSERT INTO % SELECT * FROM %.%', buffer, quote_ident(source_schema), object;
      EXECUTE 'INSERT INTO ' || buffer || ' SELECT * FROM '
              || quote_ident(source_schema) || '.' || object || ';';
    END IF;

    -- Ensure any default values that refer to the old schema now refer to the new schema.
    FOR column_, default_ IN
      SELECT column_name::text,
             replace(column_default::text, source_schema || '.', dest_schema || '.')
        FROM information_schema.columns
       WHERE table_schema = dest_schema
         AND table_name = object
         AND column_default LIKE 'nextval(%' || quote_ident(source_schema) || '%::regclass)'
    LOOP
      RAISE DEBUG 'ALTER TABLE % ALTER COLUMN % SET DEFAULT %', buffer, column_, default_;
      EXECUTE 'ALTER TABLE ' || buffer || ' ALTER COLUMN ' || column_ || ' SET DEFAULT ' || default_;
    END LOOP;

    -- Ensure any triggers also come across...
    -- We can do the same trick we did for the default values.
    -- Hmm. Need to test this, because I think that triggers may already come
    -- across...
    FOR trigger_ IN
      SELECT replace(pg_catalog.pg_get_triggerdef(oid, false)::text,
                     source_schema || '.', dest_schema || '.')
        FROM pg_catalog.pg_trigger
       WHERE tgrelid = (source_schema || '.' || object)::regclass::pg_catalog.oid
     AND NOT tgisinternal
    LOOP
      RAISE DEBUG '%', trigger_;
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
                   source_schema || '.', dest_schema || '.') AS definition,
           t.table_name
      FROM source_tables t
INNER JOIN pg_catalog.pg_constraint r
        ON (r.conrelid = t.oid)
       AND r.contype = 'f'
  LOOP
    RAISE DEBUG 'ALTER TABLE %.% ADD CONSTRAINT % %', dest_schema,
                                                      constraint_.table_name,
                                                      constraint_.name,
                                                      constraint_.definition;
    EXECUTE 'ALTER TABLE '
            || quote_ident(dest_schema) || '.' || quote_ident(constraint_.table_name)
            || ' ADD CONSTRAINT ' || quote_ident(constraint_.name)
            || ' '                || constraint_.definition;
  END LOOP;

  -- Create views.
  FOR view_ IN
    SELECT quote_ident(dest_schema) || '.' || quote_ident(viewname) AS name,
           replace(definition,
                   source_schema || '.',
                   dest_schema || '.') AS definition
      FROM pg_views
     WHERE schemaname = source_schema
  LOOP
    RAISE DEBUG 'CREATE VIEW % AS %', view_.name, view_.definition;
    EXECUTE 'CREATE VIEW ' || view_.name || ' AS ' || view_.definition;
  END LOOP;

  -- Create functions. This is in here for completeness, although I'm not sure
  -- it's the best idea to have functions in the client schema. I guess you
  -- could have that as a way of having different business logic per-schema,
  -- but that seems like a tricky thing to manage.

  FOR function_ IN
    SELECT replace(
             pg_get_functiondef(oid),
             source_schema || '.',
             dest_schema || '.'
           )
      FROM pg_proc
     WHERE pronamespace = source_schema_oid
 LOOP
   -- RAISE DEBUG '%', function_;
   EXECUTE function_;
 END LOOP;

END;

$$ LANGUAGE plpgsql VOLATILE;

CREATE OR REPLACE FUNCTION clone_schema(source_schema text, dest_schema text)
RETURNS void AS $$
  SELECT clone_schema($1, $2, false);
$$ LANGUAGE sql VOLATILE;