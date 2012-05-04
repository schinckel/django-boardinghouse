from django.db.backends.postgresql_psycopg2.creation import *


class DatabaseCreation(DatabaseCreation):   
    def sql_indexes_for_field(self, model, f, style):
        if f.db_index and not f.unique:
            qn = self.connection.ops.quote_name
            db_table = model._meta.db_table
            tablespace = f.db_tablespace or model._meta.db_tablespace
            if tablespace:
                tablespace_sql = self.connection.ops.tablespace_sql(tablespace)
                if tablespace_sql:
                    tablespace_sql = ' ' + tablespace_sql
            else:
                tablespace_sql = ''

            def get_index_sql(index_name, opclass=''):
                index_name = index_name.replace('__template__"."', '')
                return (style.SQL_KEYWORD('CREATE INDEX') + ' ' +
                        style.SQL_TABLE(qn(truncate_name(index_name,self.connection.ops.max_name_length()))) + ' ' +
                        style.SQL_KEYWORD('ON') + ' ' +
                        style.SQL_TABLE(qn(db_table)) + ' ' +
                        "(%s%s)" % (style.SQL_FIELD(qn(f.column)), opclass) +
                        "%s;" % tablespace_sql)

            output = [get_index_sql('%s_%s' % (db_table, f.column))]

            # Fields with database column types of `varchar` and `text` need
            # a second index that specifies their operator class, which is
            # needed when performing correct LIKE queries outside the
            # C locale. See #12234.
            db_type = f.db_type(connection=self.connection)
            if db_type.startswith('varchar'):
                output.append(get_index_sql('%s_%s_like' % (db_table, f.column),
                                            ' varchar_pattern_ops'))
            elif db_type.startswith('text'):
                output.append(get_index_sql('%s_%s_like' % (db_table, f.column),
                                            ' text_pattern_ops'))
        else:
            output = []
        return output