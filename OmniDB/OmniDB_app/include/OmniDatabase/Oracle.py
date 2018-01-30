'''
The MIT License (MIT)

Portions Copyright (c) 2015-2018, The OmniDB Team
Portions Copyright (c) 2017-2018, 2ndQuadrant Limited

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import os.path
import re
from collections import OrderedDict
from enum import Enum
import OmniDB_app.include.Spartacus as Spartacus
import OmniDB_app.include.Spartacus.Database as Database
import OmniDB_app.include.Spartacus.Utils as Utils

'''
------------------------------------------------------------------------
Template
------------------------------------------------------------------------
'''
class TemplateType(Enum):
    EXECUTE = 1
    SCRIPT = 2

class Template:
    def __init__(self, p_text, p_type=TemplateType.EXECUTE):
        self.v_text = p_text
        self.v_type = p_type

'''
------------------------------------------------------------------------
Oracle
------------------------------------------------------------------------
'''
class Oracle:
    def __init__(self, p_server, p_port, p_service, p_user, p_password, p_conn_id=0, p_alias=''):
        self.v_alias = p_alias
        self.v_db_type = 'oracle'
        self.v_conn_id = p_conn_id

        if p_port is None or p_port == '':
            self.v_port = '1521'
        else:
            self.v_port = p_port
        if p_service is None or p_service == '':
            self.v_service = 'XE'
        else:
            self.v_service = p_service.upper()

        self.v_server = p_server
        self.v_user = p_user.upper()
        self.v_schema = p_user.upper()
        self.v_connection = Spartacus.Database.Oracle(p_server, p_port, p_service, p_user, p_password)

        self.v_has_schema = True
        self.v_has_functions = True
        self.v_has_procedures = True
        self.v_has_sequences = True
        self.v_has_primary_keys = True
        self.v_has_foreign_keys = True
        self.v_has_uniques = True
        self.v_has_indexes = True
        self.v_has_checks = False
        self.v_has_excludes = False
        self.v_has_rules = False
        self.v_has_triggers = False
        self.v_has_partitions = False

        self.v_has_update_rule = False
        self.v_can_rename_table = True
        self.v_rename_table_command = "alter table #p_table_name# rename to #p_new_table_name#"
        self.v_create_pk_command = "constraint #p_constraint_name# primary key (#p_columns#)"
        self.v_create_fk_command = "constraint #p_constraint_name# foreign key (#p_columns#) references #p_r_table_name# (#p_r_columns#) #p_delete_update_rules#"
        self.v_create_unique_command = "constraint #p_constraint_name# unique (#p_columns#)"
        self.v_can_alter_type = True
        self.v_alter_type_command = "alter table #p_table_name# modify #p_column_name# #p_new_data_type#"
        self.v_can_alter_nullable = True
        self.v_set_nullable_command = "alter table #p_table_name# modify #p_column_name# null"
        self.v_drop_nullable_command = "alter table #p_table_name# modify #p_column_name# not null"
        self.v_can_rename_column = True
        self.v_rename_column_command = "alter table #p_table_name# rename column #p_column_name# to #p_new_column_name#"
        self.v_can_add_column = True
        self.v_add_column_command = "alter table #p_table_name# add #p_column_name# #p_data_type# #p_nullable#"
        self.v_can_drop_column = True
        self.v_drop_column_command = "alter table #p_table_name# drop column #p_column_name#"
        self.v_can_add_constraint = True
        self.v_add_pk_command = "alter table #p_table_name# add constraint #p_constraint_name# primary key (#p_columns#)"
        self.v_add_fk_command = "alter table #p_table_name# add constraint #p_constraint_name# foreign key (#p_columns#) references #p_r_table_name# (#p_r_columns#) #p_delete_update_rules#"
        self.v_add_unique_command = "alter table #p_table_name# add constraint #p_constraint_name# unique (#p_columns#)"
        self.v_can_drop_constraint = True
        self.v_drop_pk_command = "alter table #p_table_name# drop constraint #p_constraint_name#"
        self.v_drop_fk_command = "alter table #p_table_name# drop constraint #p_constraint_name#"
        self.v_drop_unique_command = "alter table #p_table_name# drop constraint #p_constraint_name#"
        self.v_create_index_command = "create index #p_index_name# on #p_table_name# (#p_columns#)";
        self.v_create_unique_index_command = "create unique index #p_index_name# on #p_table_name# (#p_columns#)"
        self.v_drop_index_command = "drop index #p_schema_name#.#p_index_name#"
        self.v_update_rules = [
            "NO ACTION"
        ]
        self.v_delete_rules = [
            "NO ACTION",
			"SET NULL",
			"CASCADE"
        ]

    def GetName(self):
        return self.v_service

    def GetVersion(self):
        return self.v_connection.ExecuteScalar('''
            select (case when product like '%Express%'
                         then 'Oracle XE '
                         else 'Oracle '
                    end) || version
            from product_component_version
            where product like 'Oracle%'
        ''')

    def GetUserName(self):
        return self.v_user

    def GetUserSuper(self):
        try:
            v_sessions = self.v_connection.Query('select * from v$session where rownum <= 1')
            return True
        except Exception as exc:
            return False

    def GetExpress(self):
        v_express = self.v_connection.Query("select * from product_component_version where product like '%Express%'")
        return (len(v_express.Rows) > 0)

    def PrintDatabaseInfo(self):
        return self.v_user + '@' + self.v_service

    def PrintDatabaseDetails(self):
        return self.v_server + ':' + self.v_port

    def HandleUpdateDeleteRules(self, p_update_rule, p_delete_rule):
        v_rules = ''
        if p_delete_rule.strip() != '':
            v_rules += ' on delete ' + p_delete_rule + ' '
        return v_rules

    def TestConnection(self):
        v_return = ''
        try:
            self.v_connection.Open()
            self.v_connection.Close()
            v_return = 'Connection successful.'
        except Exception as exc:
            v_return = str(exc)
        return v_return

    def GetErrorPosition(self, p_error_message):
        vector = str(p_error_message).split('\n')
        v_return = None
        if len(vector) > 1 and vector[1][0:4]=='LINE':
            v_return = {
                'row': vector[1].split(':')[0].split(' ')[1],
                'col': vector[2].index('^') - len(vector[1].split(':')[0])-2
            }
        return v_return

    def QueryRoles(self):
        return self.v_connection.Query('''
            select username as "role_name"
            from all_users
            order by 1
        ''', True)

    def QueryTablespaces(self):
        return self.v_connection.Query('''
            select tablespace_name as "tablespace_name"
            from dba_tablespaces
            order by 1
        ''', True)

    def QueryDatabases(self):
        return self.v_connection.Query('''
            select name as "database_name"
            from v$database
            order by 1
        ''', True)

    def QueryTables(self, p_all_schemas=False, p_schema=None):
        v_filter = ''
        if not p_all_schemas:
            if p_schema:
                v_filter = "and owner = '{0}' ".format(p_schema)
            else:
                v_filter = "and owner = '{0}' ".format(self.v_schema)
        return self.v_connection.Query('''
            select table_name as "table_name",
                   owner as "table_schema"
            from all_tables
            where 1 = 1
            {0}
            order by 2, 1
        '''.format(v_filter), True)

    def QueryTablesFields(self, p_table=None, p_all_schemas=False, p_schema=None):
        v_filter = ''
        if not p_all_schemas:
            if p_table and p_schema:
                v_filter = "and owner = '{0}' and table_name = '{1}' ".format(p_schema, p_table)
            elif p_table:
                v_filter = "and owner = '{0}' and table_name = '{1}' ".format(self.v_schema, p_table)
            elif p_schema:
                v_filter = "and owner = '{0}' ".format(p_schema)
            else:
                v_filter = "and owner = '{0}' ".format(self.v_schema)
        else:
            if p_table:
                v_filter = "and table_name = '{0}' ".format(p_table)
        return self.v_connection.Query('''
            select table_name as "table_name",
                   column_name as "column_name",
                   case when data_type = 'NUMBER' and data_scale = '0' then 'INTEGER' else data_type end as "data_type",
                   case nullable when 'Y' then 'YES' else 'NO' end as "nullable",
                   data_length as "data_length",
                   data_precision as "data_precision",
                   data_scale as "data_scale"
            from all_tab_columns
            where 1 = 1
            {0}
            order by table_name, column_id
        '''.format(v_filter), True)

    def QueryTablesForeignKeys(self, p_table=None, p_all_schemas=False, p_schema=None):
        v_filter = ''
        if not p_all_schemas:
            if p_table and p_schema:
                v_filter = "and constraint_info.owner = '{0}' and detail_table.table_name = '{1}' ".format(p_schema, p_table)
            elif p_table:
                v_filter = "and constraint_info.owner = '{0}' and detail_table.table_name = '{1}' ".format(self.v_schema, p_table)
            elif p_schema:
                v_filter = "and constraint_info.owner = '{0}' ".format(p_schema)
            else:
                v_filter = "and constraint_info.owner = '{0}' ".format(self.v_schema)
        else:
            if p_table:
                v_filter = "and detail_table.table_name = '{0}' ".format(p_table)
        return self.v_connection.Query('''
            select master_table.table_name as "r_table_name",
                   master_table.owner as "r_table_schema",
                   master_table.column_name as "r_column_name",
                   detail_table.table_name as "table_name",
                   detail_table.column_name as "column_name",
                   detail_table.owner as "table_schema",
                   constraint_info.constraint_name as "constraint_name",
                   constraint_info.delete_rule as "delete_rule",
                   'NO ACTION' as "update_rule",
                   constraint_info.r_constraint_name as "r_constraint_name",
                   detail_table.position as "ordinal_position"
            from user_constraints constraint_info,
                 user_cons_columns detail_table,
                 user_cons_columns master_table
            where constraint_info.constraint_name = detail_table.constraint_name
              and constraint_info.r_constraint_name = master_table.constraint_name
              and detail_table.position = master_table.position
              and constraint_info.constraint_type = 'R'
            {0}
            order by constraint_info.constraint_name,
                     detail_table.table_name,
                     detail_table.position
        '''.format(v_filter), True)

    def QueryTablesPrimaryKeys(self, p_table=None, p_all_schemas=False, p_schema=None):
        v_filter = ''
        if not p_all_schemas:
            if p_table and p_schema:
                v_filter = "and \"table_schema\" = '{0}' and \"table_name\" = '{1}' ".format(p_schema, p_table)
            elif p_table:
                v_filter = "and \"table_schema\" = '{0}' and \"table_name\" = '{1}' ".format(self.v_schema, p_table)
            elif p_schema:
                v_filter = "and \"table_schema\" = '{0}' ".format(p_schema)
            else:
                v_filter = "and \"table_schema\" = '{0}' ".format(self.v_schema)
        else:
            if p_table:
                v_filter = "and \"table_name\" = '{0}' ".format(p_table)
        return self.v_connection.Query('''
            select distinct *
            from (
                select cons.constraint_name as "constraint_name",
                       cols.column_name as "column_name",
                       cols.table_name as "table_name",
                       cons.owner as "table_schema"
                from all_constraints cons,
                     all_cons_columns cols,
                     all_tables t
                where cons.constraint_type = 'P'
                  and t.table_name = cols.table_name
                  and cons.constraint_name = cols.constraint_name
                  and cons.owner = cols.owner
                order by cons.owner,
                         cols.table_name,
                         cons.constraint_name,
                         cols.position
            )
            where 1 = 1
            {0}
        '''.format(v_filter), True)

    def QueryTablesUniques(self, p_table=None, p_all_schemas=False, p_schema=None):
        v_filter = ''
        if not p_all_schemas:
            if p_table and p_schema:
                v_filter = "and \"table_schema\" = '{0}' and \"table_name\" = '{1}' ".format(p_schema, p_table)
            elif p_table:
                v_filter = "and \"table_schema\" = '{0}' and \"table_name\" = '{1}' ".format(self.v_schema, p_table)
            elif p_schema:
                v_filter = "and \"table_schema\" = '{0}' ".format(p_schema)
            else:
                v_filter = "and \"table_schema\" = '{0}' ".format(self.v_schema)
        else:
            if p_table:
                v_filter = "and \"table_name\" = '{0}' ".format(p_table)
        return self.v_connection.Query('''
            select distinct *
            from (
                select cons.constraint_name as "constraint_name",
                       cols.column_name as "column_name",
                       cols.table_name as "table_name",
                       cons.owner as "table_schema"
                from all_constraints cons,
                     all_cons_columns cols,
                     all_tables t
                where cons.constraint_type = 'U'
                  and t.table_name = cols.table_name
                  and cons.constraint_name = cols.constraint_name
                  and cons.owner = cols.owner
                order by cons.owner,
                         cols.table_name,
                         cons.constraint_name,
                         cols.position
            )
            where 1 = 1
            {0}
        '''.format(v_filter), True)

    def QueryTablesIndexes(self, p_table=None, p_all_schemas=False, p_schema=None):
        v_filter = ''
        if not p_all_schemas:
            if p_table and p_schema:
                v_filter = "and t.owner = '{0}' and t.table_name = '{1}' ".format(p_schema, p_table)
            elif p_table:
                v_filter = "and t.owner = '{0}' and t.table_name = '{1}' ".format(self.v_schema, p_table)
            elif p_schema:
                v_filter = "and t.owner = '{0}' ".format(p_schema)
            else:
                v_filter = "and t.owner = '{0}' ".format(self.v_schema)
        else:
            if p_table:
                v_filter = "and t.table_name = '{0}' ".format(p_table)
        return self.v_connection.Query('''
            select t.owner as "schema_name",
                   t.table_name as "table_name",
                   t.index_name as "index_name",
                   c.column_name as "column_name",
                   case when t.uniqueness = 'UNIQUE' then 'Unique' else 'Non Unique' end as "uniqueness"
            from all_indexes t,
                 all_ind_columns c
            where t.table_name = c.table_name
              and t.index_name = c.index_name
              and t.owner = c.index_owner
            {0}
            order by t.owner,
                     t.table_name,
                     t.index_name
        '''.format(v_filter), True)

    def QueryDataLimited(self, p_query, p_count=-1):
        if p_count != -1:
            try:
                self.v_connection.Open()
                v_data = self.v_connection.QueryBlock('select * from ( {0} ) t where rownum <= {1}'.format(p_query, p_count), p_count, True, True)
                self.v_connection.Close()
                return v_data
            except Spartacus.Database.Exception as exc:
                try:
                    self.v_connection.Cancel()
                except:
                    pass
                raise exc
        else:
            return self.v_connection.Query(p_query, True)

    def QueryTableRecords(self, p_column_list, p_table, p_filter, p_count=-1):
        v_limit = ''
        if p_count != -1:
            v_limit = ' where rownum <= ' + p_count
        return self.v_connection.Query('''
            select *
            from (
            select {0}
            from {1} t
            {2}
            )
            {3}
        '''.format(
                p_column_list,
                p_table,
                p_filter,
                v_limit
            ), True, True
        )

    def QueryFunctions(self, p_all_schemas=False, p_schema=None):
        v_filter = ''
        if not p_all_schemas:
            if p_schema:
                v_filter = "and t.owner = '{0}' ".format(p_schema)
            else:
                v_filter = "and t.owner = '{0}' ".format(self.v_schema)
        return self.v_connection.Query('''
            select t.owner as "schema_name",
                   t.object_name as "id",
                   t.object_name as "name"
            from all_procedures t
            where t.object_type = 'FUNCTION'
            {0}
            order by 2
        '''.format(v_filter), True)

    def QueryFunctionFields(self, p_function, p_schema):
        if p_schema:
            return self.v_connection.Query('''
                select (case t.in_out
                          when 'IN' then 'I'
                          when 'OUT' then 'O'
                          else 'R'
                        end) as "type",
                       (case when t.position = 0
                             then 'return ' || t.data_type
                             else t.argument_name || ' ' || t.data_type
                        end) as "name",
                       t.position+1 as "seq"
                from all_arguments t
                where t.owner = '{0}'
                  and t.object_name = '{1}'
                order by 3
            '''.format(p_schema, p_function), True)
        else:
            return self.v_connection.Query('''
                select (case t.in_out
                          when 'IN' then 'I'
                          when 'OUT' then 'O'
                          else 'R'
                        end) as "type",
                       (case when t.position = 0
                             then 'return ' || t.data_type
                             else t.argument_name || ' ' || t.data_type
                        end) as "name",
                       t.position+1 as "seq"
                from all_arguments t
                where t.owner = '{0}'
                  and t.object_name = '{1}'
                order by 3
            '''.format(self.v_schema, p_function), True)

    def GetFunctionDefinition(self, p_function):
        v_body = '-- DROP FUNCTION {0};\n'.format(p_function)
        v_body = v_body + self.v_connection.ExecuteScalar("select dbms_metadata.get_ddl('FUNCTION', '{0}') from dual".format(p_function))
        return v_body

    def QueryProcedures(self, p_all_schemas=False, p_schema=None):
        v_filter = ''
        if not p_all_schemas:
            if p_schema:
                v_filter = "and t.owner = '{0}' ".format(p_schema)
            else:
                v_filter = "and t.owner = '{0}' ".format(self.v_schema)
        return self.v_connection.Query('''
            select t.owner as "schema_name",
                   t.object_name as "id",
                   t.object_name as "name"
            from all_procedures t
            where t.object_type = 'PROCEDURE'
            {0}
            order by 2
        '''.format(v_filter), True)

    def QueryProcedureFields(self, p_procedure, p_schema):
        if p_schema:
            return self.v_connection.Query('''
                select (case t.in_out
                          when 'IN' then 'I'
                          when 'OUT' then 'O'
                          else 'R'
                        end) as "type",
                       t.argument_name || ' ' || t.data_type as "name",
                       t.position+1 as "seq"
                from all_arguments t
                where t.owner = '{0}'
                  and t.object_name = '{1}'
                order by 3
            '''.format(p_schema, p_procedure), True)
        else:
            return self.v_connection.Query('''
                select (case t.in_out
                          when 'IN' then 'I'
                          when 'OUT' then 'O'
                          else 'R'
                        end) as "type",
                       t.argument_name || ' ' || t.data_type as "name",
                       t.position+1 as "seq"
                from all_arguments t
                where t.owner = '{0}'
                  and t.object_name = '{1}'
                order by 3
            '''.format(self.v_schema, p_procedure), True)

    def GetProcedureDefinition(self, p_procedure):
        v_body = '-- DROP PROCEDURE {0};\n'.format(p_procedure)
        v_body = v_body + self.v_connection.ExecuteScalar("select dbms_metadata.get_ddl('PROCEDURE', '{0}') from dual".format(p_procedure))
        return v_body

    def QuerySequences(self, p_all_schemas=False, p_schema=None):
        v_filter = ''
        if not p_all_schemas:
            if p_schema:
                v_filter = "and sequence_owner = '{0}' ".format(p_schema)
            else:
                v_filter = "and sequence_owner = '{0}' ".format(self.v_schema)
        v_table = self.v_connection.Query('''
            select sequence_owner as "sequence_schema",
                   sequence_name as "sequence_name"
            from all_sequences
            where 1 = 1
            {0}
            order by 1, 2
        '''.format(v_filter), True)
        return v_table

    def QueryViews(self, p_all_schemas=False, p_schema=None):
        v_filter = ''
        if not p_all_schemas:
            if p_schema:
                v_filter = "and owner = '{0}' ".format(p_schema)
            else:
                v_filter = "and owner = '{0}' ".format(self.v_schema)
        return self.v_connection.Query('''
            select view_name as "table_name",
                   owner as "table_schema"
            from all_views
            where 1 = 1
            {0}
            order by 2, 1
        '''.format(v_filter), True)

    def QueryViewFields(self, p_table=None, p_all_schemas=False, p_schema=None):
        v_filter = ''
        if not p_all_schemas:
            if p_table and p_schema:
                v_filter = "and owner = '{0}' and table_name = '{1}' ".format(p_schema, p_table)
            elif p_table:
                v_filter = "and owner = '{0}' and table_name = '{1}' ".format(self.v_schema, p_table)
            elif p_schema:
                v_filter = "and owner = '{0}' ".format(p_schema)
            else:
                v_filter = "and owner = '{0}' ".format(self.v_schema)
        else:
            if p_table:
                v_filter = "and table_name = '{0}' ".format(p_table)
        return self.v_connection.Query('''
            select table_name as "table_name",
                   column_name as "column_name",
                   case when data_type = 'NUMBER' and data_scale = '0' then 'INTEGER' else data_type end as "data_type",
                   case nullable when 'Y' then 'YES' else 'NO' end as "nullable",
                   data_length as "data_length",
                   data_precision as "data_precision",
                   data_scale as "data_scale"
            from all_tab_columns
            where 1 = 1
            {0}
            order by table_name, column_id
        '''.format(v_filter), True)

    def GetViewDefinition(self, p_view, p_schema):
        if p_schema:
            v_schema = p_schema
        else:
            v_schema = self.v_schema
        return '''CREATE OR REPLACE VIEW {0}.{1} AS
{2}
'''.format(p_schema, p_view,
        self.v_connection.ExecuteScalar('''
                select text
                from all_views
                where owner = '{0}'
                  and view_name = '{1}'
            '''.format(v_schema, p_view)
    ))

    def TemplateCreateRole(self):
        return Template('''CREATE { ROLE | USER } name
--NOT IDENTIFIED
--IDENTIFIED BY password
--DEFAULT TABLESPACE tablespace
--TEMPORARY TABLESPACE tablespace
--QUOTA { size | UNLIMITED } ON tablespace
--PASSWORD EXPIRE
--ACCOUNT { LOCK | UNLOCK }
''')

    def TemplateAlterRole(self):
        return Template('''ALTER { ROLE | USER } #role_name#
--NOT IDENTIFIED
--IDENTIFIED BY password
--DEFAULT TABLESPACE tablespace
--TEMPORARY TABLESPACE tablespace
--QUOTA { size | UNLIMITED } ON tablespace
--DEFAULT ROLE { role [, role ] ... | ALL [ EXCEPT role [, role ] ... ] | NONE }
--PASSWORD EXPIRE
--ACCOUNT { LOCK | UNLOCK }
''')

    def TemplateDropRole(self):
        return Template('''DROP { ROLE | USER } #role_name#
--CASCADE
''')

    def TemplateCreateTablespace(self):
        return Template('''CREATE { SMALLFILE | BIGFILE }
[ TEMPORARY | UNDO ] TABLESPACE name
[ DATAFILE | TEMPFILE ] 'filename' [ SIZE size ] [ REUSE ]
--AUTOEXTEND OFF | AUTOEXTEND ON [ NEXT size ]
--MAXSIZE [ size | UNLIMITED ]
--MINIMUM EXTENT size
--BLOCKSIZE size
--LOGGING | NOLOGGING | FORCE LOGGING
--ENCRYPTION [ USING 'algorithm' ]
--ONLINE | OFFLINE
--EXTENT MANAGEMENT LOCAL { AUTOALLOCATE | UNIFORM [ SIZE size ] }
--SEGMENT SPACE MANAGEMENT { AUTO | MANUAL }
--FLASHBACK { ON | OFF }
--RETENTION { GUARANTEE | NOGUARANTEE }
''')

    def TemplateAlterTablespace(self):
        return Template('''ALTER TABLESPACE #tablespace_name#
--MINIMUM EXTENT size
--RESIZE size
--COALESCE
--SHRINK SPACE [ KEEP size ]
--RENAME TO new_name
--[ BEGIN | END ] BACKUP
--ADD [ DATAFILE | TEMPFILE ] 'filename' [ SIZE size ] [ REUSE AUTOEXTEND OFF | AUTOEXTEND ON [ NEXT size ] ] [ MAXSIZE [ size | UNLIMITED ] ]
--DROP [ DATAFILE | TEMPFILE ] 'filename'
--SHRINK TEMPFILE 'filename' [ KEEP size ]
--RENAME DATAFILE 'filename' TO 'new_filename'
--[ DATAFILE | TEMPFILE ] [ ONLINE | OFFLINE ]
--[ NO ] FORCE LOGGING
--ONLINE
--OFFLINE [ NORMAL | TEMPORARY | IMMEDIATE ]
--READ [ ONLY | WRITE ]
--PERMANENT | TEMPORARY
--AUTOEXTEND OFF | AUTOEXTEND ON [ NEXT size ]
--MAXSIZE [ size | UNLIMITED ]
--FLASHBACK { ON | OFF }
--RETENTION { GUARANTEE | NOGUARANTEE }
''')

    def TemplateDropTablespace(self):
        return Template('''DROP TABLESPACE #tablespace_name#
--INCLUDING CONTENTS
--[ AND | KEEP ] DATAFILES
--CASCADE CONSTRAINTS
''')

    def TemplateCreateDatabase(self):
        return Template('''CREATE DATABASE name
--USER SYS IDENTIFIED BY password
--USER SYSTEM IDENTIFIED BY password
--CONTROLFILE REUSE
--MAXDATAFILES integer
--MAXINSTANCES integer
--CHARACTER SET charset
--NATIONAL CHARACTER SET charset
--SET DEFAULT [ SMALLFILE | BIGFILE ] TABLESPACE
--EXTENT MANAGEMENT LOCAL
--DEFAULT TABLESPACE tablespace
--[ BIGFILE | SMALLFILE ] DEFAULT TEMPORARY TABLESPACE tablespace
--[ BIGFILE | SMALLFILE ] UNDO TABLESPACE tablespace
''')

    def TemplateAlterDatabase(self):
        return Template('''ALTER DATABASE #database_name#
--OPEN READ ONLY
--OPEN READ WRITE [ RESETLOGS | NORESETLOGS ] [ UPGRADE | DOWNGRADE ]
--[ BEGIN | END ] BACKUP
--SET DEFAULT [ SMALLFILE | BIGFILE ] TABLESPACE
--DEFAULT TABLESPACE tablespace
--[ BIGFILE | SMALLFILE ] DEFAULT TEMPORARY TABLESPACE tablespace
--RENAME GLOBAL_NAME TO new_name
--{ ENABLE | DISABLE } BLOCK CHANGING TRACKING
--FLASHBACK { ON | OFF }
''')

    def TemplateDropDatabase(self):
        return Template('DROP DATABASE')

    def TemplateCreateFunction(self):
        return Template('''CREATE OR REPLACE FUNCTION #schema_name#.name
--(
--    [ argmode ] [ argname ] argtype [ { DEFAULT | = } default_expr ]
--)
--RETURN rettype
--PIPELINED
AS
-- variables
-- pragmas
BEGIN
-- definition
END;
''')

    def TemplateDropFunction(self):
        return Template('DROP FUNCTION #function_name#')

    def TemplateCreateProcedure(self):
        return Template('''CREATE OR REPLACE PROCEDURE #schema_name#.name
--(
--    [ argmode ] [ argname ] argtype [ { DEFAULT | = } default_expr ]
--)
AS
-- variables
-- pragmas
BEGIN
-- definition
END;
''')

    def TemplateDropProcedure(self):
        return Template('DROP PROCEDURE #function_name#')

    def TemplateCreateTable(self):
        pass

    def TemplateAlterTable(self):
        pass

    def TemplateDropTable(self):
        return Template('''DROP TABLE #table_name#
--CASCADE CONSTRAINTS
--PURGE
''')

    def TemplateCreateColumn(self):
        return Template('''ALTER TABLE #table_name#
ADD name data_type
--SORT
--DEFAULT expr
--NOT NULL
''')

    def TemplateAlterColumn(self):
        return Template('''ALTER TABLE #table_name#
--MODIFY #column_name# { datatype | DEFAULT expr | [ NULL | NOT NULL ]}
--RENAME COLUMN #column_name# TO new_name
'''
)

    def TemplateDropColumn(self):
        return Template('''ALTER TABLE #table_name#
DROP COLUMN #column_name#
--CASCADE CONSTRAINTS
--INVALIDATE
''')

    def TemplateCreatePrimaryKey(self):
        return Template('''ALTER TABLE #table_name#
ADD CONSTRAINT name
PRIMARY KEY ( column_name [, ... ] )
--[ NOT ] DEFERRABLE
--INITIALLY { IMMEDIATE | DEFERRED }
--RELY | NORELY
--USING INDEX index_name
--ENABLE
--DISABLE
--VALIDATE
--NOVALIDATE
--EXCEPTIONS INTO table_name
''')

    def TemplateDropPrimaryKey(self):
        return Template('''ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''')

    def TemplateCreateUnique(self):
        return Template('''ALTER TABLE #table_name#
ADD CONSTRAINT name
UNIQUE ( column_name [, ... ] )
--[ NOT ] DEFERRABLE
--INITIALLY { IMMEDIATE | DEFERRED }
--RELY | NORELY
--USING INDEX index_name
--ENABLE
--DISABLE
--VALIDATE
--NOVALIDATE
--EXCEPTIONS INTO table_name
''')

    def TemplateDropUnique(self):
        return Template('''ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''')

    def TemplateCreateForeignKey(self):
        return Template('''ALTER TABLE #table_name#
ADD CONSTRAINT name
FOREIGN KEY ( column_name [, ... ] )
REFERENCES reftable [ ( refcolumn [, ... ] ) ]
--[ NOT ] DEFERRABLE
--INITIALLY { IMMEDIATE | DEFERRED }
--RELY | NORELY
--USING INDEX index_name
--ENABLE
--DISABLE
--VALIDATE
--NOVALIDATE
--EXCEPTIONS INTO table_name
''')

    def TemplateDropForeignKey(self):
        return Template('''ALTER TABLE #table_name#
DROP CONSTRAINT #constraint_name#
--CASCADE
''')

    def TemplateCreateIndex(self):
        return Template('''CREATE [ UNIQUE ] INDEX name
ON #table_name#
( { column_name | ( expression ) } [ ASC | DESC ] )
--ONLINE
--TABLESPACE tablespace
--[ SORT | NOSORT ]
--REVERSE
--[ VISIBLE | INVISIBLE ]
--[ NOPARALLEL | PARALLEL integer ]
''')

    def TemplateAlterIndex(self):
        return Template('''ALTER INDEX #index_name#
--COMPILE
--[ ENABLE | DISABLE ]
--UNUSABLE
--[ VISIBLE | INVISIBLE ]
--RENAME TO new_name
--COALESCE
--[ MONITORING | NOMONITORING ] USAGE
--UPDATE BLOCK REFERENCES
''')

    def TemplateDropIndex(self):
        return Template('''DROP INDEX #index_name#
--FORCE
''')

    def TemplateCreateSequence(self):
        return Template('''CREATE SEQUENCE #schema_name#.name
--INCREMENT BY increment
--MINVALUE minvalue | NOMINVALUE
--MAXVALUE maxvalue | NOMAXVALUE
--START WITH start
--CACHE cache | NOCACHE
--CYCLE | NOCYCLE
--ORDER | NOORDER
''')

    def TemplateAlterSequence(self):
        return Template('''ALTER SEQUENCE #sequence_name#
--INCREMENT BY increment
--MINVALUE minvalue | NOMINVALUE
--MAXVALUE maxvalue | NOMAXVALUE
--CACHE cache | NOCACHE
--CYCLE | NOCYCLE
--ORDER | NOORDER
''')

    def TemplateDropSequence(self):
        return Template('DROP SEQUENCE #sequence_name#')

    def TemplateCreateView(self):
        return Template('''CREATE OR REPLACE VIEW #schema_name#.name AS
SELECT ...
''')

    def TemplateDropView(self):
        return Template('''DROP VIEW #view_name#
--CASCADE CONSTRAINTS
''')

    def GetProperties(self, p_schema, p_object, p_type):
        v_table1 = self.v_connection.Query('''
            select owner as "Owner",
                   object_name as "Object Name",
                   object_id as "Object ID",
                   object_type as "Object Type",
                   created as "Created",
                   last_ddl_time as "Last DDL Time",
                   timestamp as "Timestamp",
                   status as "Status",
                   temporary as "Temporary",
                   generated as "Generated",
                   secondary as "Secondary"
            from all_objects
            where owner = '{0}'
              and object_name = '{1}'
        '''.format(self.v_schema, p_object)).Transpose('Property', 'Value')
        if p_type == 'sequence':
            v_table2 = self.v_connection.Query('''
                select last_number as "Last Value",
                       min_value as "Min Value",
                       max_value as "Max Value",
                       increment_by as "Increment By",
                       cycle_flag as "Is Cached",
                       order_flag as "Is Ordered",
                       cache_size as "Cache Size"
                from all_sequences
                where sequence_owner = '{0}'
                  and sequence_name = '{1}'
            '''.format(self.v_schema, p_object)).Transpose('Property', 'Value')
            v_table1.Merge(v_table2)
        return v_table1

    def GetDDL(self, p_schema, p_object, p_type):
        return self.v_connection.ExecuteScalar('''
            select dbms_metadata.get_ddl(object_type, object_name) as ddl,
            from user_objects
            where object_name = '{0}'
        '''.format(p_object))
