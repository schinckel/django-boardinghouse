-- http://wiki.postgresql.org/wiki/Clone_schema
-- All on one line to satisfy the django syncdb sql loader

CREATE OR REPLACE FUNCTION clone_schema(source_schema text, dest_schema text) RETURNS void AS
$$

DECLARE
  object text;
  buffer text;
  default_ text;
  column_ text;
BEGIN
  EXECUTE 'CREATE SCHEMA ' || dest_schema ;
 
  -- TODO: Find a way to make this sequence's owner is the correct column.
  -- Not a huge priority.
  FOR object IN
    SELECT sequence_name::text FROM information_schema.SEQUENCES WHERE sequence_schema = source_schema
  LOOP
    EXECUTE 'CREATE SEQUENCE ' || dest_schema || '.' || object;
  END LOOP;
 
  FOR object IN
    SELECT table_name::text FROM information_schema.TABLES WHERE table_schema = source_schema
  LOOP
    buffer := dest_schema || '.' || object;
    EXECUTE 'CREATE TABLE ' || buffer || ' (LIKE ' || source_schema || '.' || object || ' INCLUDING CONSTRAINTS INCLUDING INDEXES INCLUDING DEFAULTS)';
   
    FOR column_, default_ IN
      SELECT column_name::text, replace(column_default::text, source_schema, dest_schema) FROM information_schema.COLUMNS where table_schema = dest_schema AND table_name = object AND column_default LIKE '%' || source_schema || '%'
    LOOP
      EXECUTE 'ALTER TABLE ' || buffer || ' ALTER COLUMN ' || column_ || ' SET DEFAULT ' || default_;
    END LOOP;
  END LOOP;
 
END;

$$ LANGUAGE plpgsql VOLATILE;