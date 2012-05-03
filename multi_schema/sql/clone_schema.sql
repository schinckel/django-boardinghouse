# http://wiki.postgresql.org/wiki/Clone_schema

CREATE OR REPLACE FUNCTION clone_schema(source_schema text, dest_schema text) RETURNS void AS
$BODY$
DECLARE
  object text;
  buffer text;
BEGIN
    EXECUTE 'CREATE SCHEMA ' || dest_schema ;

    FOR object IN
        SELECT table_name::text FROM information_schema.TABLES WHERE table_schema = source_schema
    LOOP
        buffer := dest_schema || '.' || object;
        EXECUTE 'CREATE TABLE ' || buffer || ' (LIKE ' || source_schema || '.' || object || ' INCLUDING CONSTRAINTS INCLUDING INDEXES INCLUDING DEFAULTS)';
    END LOOP;

END;
$BODY$
LANGUAGE plpgsql VOLATILE;