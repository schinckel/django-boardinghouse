-- http://wiki.postgresql.org/wiki/Clone_schema

CREATE OR REPLACE FUNCTION clone_schema(source_schema text, dest_schema text) RETURNS void AS
$$

DECLARE
BEGIN
  RAISE EXCEPTION 'This function is no longer supported. Please upgrade.';
END;

$$ LANGUAGE plpgsql VOLATILE;