#!/usr/bin/env python
# encoding: utf-8



import yoyo
import subprocess
import logging
import re
import os
import time
from vilya.frontend import create_app
from docopt import docopt
from yoyo.connections import connect

app = create_app()

logging.basicConfig(level=logging.INFO)

def retab(docs):
       lines = docs.split('\n')
       while lines:
           l = lines[0]
           if not l.strip():
               lines = lines[1:]
           else:
               break
       if not lines: return docs
       fl = lines[0]
       space = re.compile('^\s+')
       flspace = space.match(fl)
       if flspace:
           start = flspace.end()
           lines = map(lambda l:l[start:], lines)
       return '\n'.join(lines)



class MigrationGenerator(object):
    
    def __init__(self, migrations_dir):
        self.migrations_dir = migrations_dir

    def gen_id(self, string):
        string = re.sub(r'[^a-zA-Z0-9]+', '_', string) 
        if string[0] == '_': string = string[1:]
        elif string[-1] == '_': string = string[:-1]
        string = string[:30]
        now = time.time()
        dates = time.strftime('%Y%m%d_%H%M')
        return "%x__%s__%s" % (now, dates, string)

    def filepath(self, mid):
        filename =  mid + '.py'
        return os.path.join(self.migrations_dir, filename)

    def edit_and_save(self, title, content):
        editor = os.environ.get('EDITOR','vim')
        migration_id = self.gen_id(title)
        fp = self.filepath(migration_id)
        content = content.format(
                migration_id=migration_id,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'))
        with open(fp, 'w') as tempfile:
            tempfile.write(content)
            tempfile.flush()
            ret = subprocess.call([editor, tempfile.name])
        if ret != 0:
            c = raw_input('Editor returned %d! Keep migration file? (Y/n)' % ret)
            if (c=='n' or c=='N'):
                os.remove(fp)
                raise Exception('Operation abort')
        print 'Migration generated'
        print ' -->', migration_id
        return migration_id

    def content(self, sql, rollback_sql, task="<task>", description = '<description>'):
        code = '''
        #!/usr/bin/env python
        # encoding: utf-8

        # 
        # ID: {{migration_id}}
        # timpstamp: {{timestamp}}
        # -------------------------------
        # {task}
        # 
        # {description}
        # -------------------------------
        #

        from yoyo import step

        step(
        # forward action
        """
        {sql}
        """,

        # rollback action
        """
        {rollback_sql}
        """
        )
        '''
        dlines = description.split('\n')
        ds = '\n# '.join(dlines)
        return retab(code).format(
                task=task,
                description=ds,
                sql=sql,
                rollback_sql=rollback_sql,
                )
    
    def snapshot(self, sql, db, tables):
        
        rollback = """
        DROP DATABASE {db};
        CREATE DATABASE {db};
        USE {db};

        CREATE TABLE `_yoyo_migration` (
          `id` varchar(255) NOT NULL,
          `ctime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;

        """.format(db=db)

        task = 'Snapshot: %s' % db
        description = 'tables:\n  ' + '\n  '.join(tables)
        content = self.content(sql, retab(rollback), task, description)
        mid = self.edit_and_save('snapshot', content)
        return mid

    def create_table(self, table, columns, pk, uk, keys):
        sql = """
        CREATE TABLE `{table}` (
          /* columns */
          {cs},

          /* primary key */
          {pk}
          /* Unique keys */
          {uk}
          /* Indexes */
          {ks}
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        """
        sql = retab(sql)
        column_sql = []
        column_pk = "`id` int NOT NULL AUTO_INCREMENT"
        des = []
        for n,t in sorted(columns):
            if n == pk:
                column_pk = "`%s` %s NOT NULL" % (n, t)
                if t.startswith('int'):
                    column_pk += ' AUTO_INCREMENT'
                des = [('%s: %s (primary key)' % (n, t))] + des
            else:
                l = "`%s` %s" % (n,t)
                if n in uk:
                    l += ' NOT NULL'
                    des.append(('%s: %s (unique key)' % (n, t)))
                elif n in keys:
                    des.append(('%s: %s (key)' % (n, t)))
                column_sql.append(l)
        cs = ',\n  '.join([column_pk] + column_sql) 
        uk = ',\n  '.join([('UNIQUE KEY `uk_%s` (`%s`)' % (n, n)) for n in sorted(uk)])
        ks = ',\n  '.join([('KEY `idx_%s` (`%s`)' % (n, n)) for n in sorted(keys)])
        pk = 'PRIMARY KEY (`%s`)' % pk
        if uk or ks:
            pk += ',\n'
        if uk and ks:
            uk += ',\n'
        if ks:
            ks += '\n'
        sql = sql.format(table=table, cs=cs, pk=pk, uk=uk, ks=ks)
        task = 'create table: `%s`' % table 
        description = 'columns:\n  ' + '\n  '.join(des)
        rollback = "DROP TABLE `%s`;" % table
        content = self.content(sql, rollback, task, description)
        mid = self.edit_and_save(task, content)
        return mid

    def drop_table(self, table, rollback):
        sql = "DROP TABLE `%s`;" % table
        task = "drop table: %s" % table
        content = self.content(sql, rollback, task)
        mid = self.edit_and_save(task, content)

    def _columns_sql(self, op, table, columns, schema, keys):
        sqls = []
        rollback = []
        for c in columns:
            sc = schema[c]
            if op == 'drop':
                t, null, key, default, ex = sc
                null = 'NULL' if null=='YES' else 'NOT NULL'
                default = 'DEFAULT %s' % default if default else ''
                ex = ex.upper()
                sqls.append('ALTER TABLE `{table}` DROP COLUMN `{c}`;'.format(table=table, c=c))
                r1 = 'ALTER TABLE `{table}` ADD `{c}` {t} {null} {default};'.format(
                        table=table, c=c, t=t, null=null, default=default)
                rollback.append(r1)

                key = keys.get(c)
                # TODO: suport multi columns index
                if key:
                    uni, idx = key
                    uni = 'UNIQUE ' if uni else ''
                    rollback.append('CREATE {}INDEX `{}` ON `{}`(`{}`);'.format(uni, idx, table, c))
            elif op == 'add':
                t = sc
                sqls.append('ALTER TABLE `{}` ADD `{}` {};'.format(table, c, t))
                rollback.append('ALTER TABLE `{}` DROP COLUMN `{}`;'.format(table, c))
        s = '\n'.join(sqls)
        r = '\n'.join(rollback)
        return s, r

    def add_columns(self, table, columns, schema, keys):
        s, r = self._columns_sql('add', table, columns, schema, keys)
        if len(columns) == 1:
            task = 'create column: %s' % columns[0]
            description = '<description>'
        else:
            task = 'create %d columns' % len(columns)
            description = 'columns:'+'  '.join(columns)
        content = self.content(s, r, task, description)
        return self.edit_and_save(task, content)

    def drop_columns(self, table, columns, schema, keys):
        s, r = self._columns_sql('drop', table, columns, schema, keys)
        if len(columns) == 1:
            task = 'drop column: %s' % columns.pop()
            description = '<description>'
        else:
            task = 'drop %d columns' % len(columns)
            description = 'columns:\n'+'  '.join(columns)
        content = self.content(s, r, task, description)
        return self.edit_and_save(task, content)

    def alter_column_type(self, table, column, ncolumn, schema, type_):
        ot, null, _, default, _  = schema
        nt = ' ' + type_ if type_ else ''
        null = ' NOT NULL' if null=='NO' else ' NULL'
        default = ' DEFAULT %s' % default if default else ''
        sql = 'ALTER TABLE `{}` CHANGE `{}` `{}`{};'.format(table, column, ncolumn, nt)
        rollback = 'ALTER TABLE `{}` CHANGE `{}` `{}` {}{}{};'.format(
                table, ncolumn, column, ot, null, default)
        if column == ncolumn:
            task = 'change column def: %s' % column
        else:
            task = 'change column %s to %s' % (column, ncolumn)
        content = self.content(sql, rollback, task)
        return self.edit_and_save(task, content)
        
    def rename_table(self, old, new):
        sql = 'RENAME TABLE `%s` TO `%s`;' % (old, new)
        rollback = 'RENAME TABLE `%s` TO `%s`;' % (new, old)
        task = 'rename table %s to %s' % (old, new)
        content = self.content(sql, rollback, task)
        return self.edit_and_save(task, content)

    def alter_index(self, drop, uni, key):
        sqls = []
        rollback = []
        sqls.append('\n/* droping indexes */')
        for t, c, i in sorted(drop):
            sqls.append('ALTER TABLE `%s` DROP INDEX `%s`;' % (t, i))
            rollback.append('CREATE INDEX `%s` ON `%s`(`%s`);' % (i, t, c))
        rollback.append('\n/* restore droped indexes */')
        sqls.append('\n/* creating unique indexes */')
        for t, c, i in sorted(uni):
            sqls.append('CREATE UNIQUE INDEX `%s` ON `%s`(`%s`);' % (i, t, c))
            rollback.append('ALTER TABLE `%s` DROP INDEX `%s`;' % (t, i))
        rollback.append('\n/* droping unique indexes */')
        sqls.append('\n/* creating indexes */')
        for t, c, i in sorted(key):
            sqls.append('CREATE INDEX `%s` ON `%s`(`%s`);' % (i, t, c))
            rollback.append('ALTER TABLE `%s` DROP INDEX `%s`;' % (t, i))
        rollback.append('\n/* droping indexes */')
        sql = '\n'.join(sqls)
        rob = '\n'.join(reversed(rollback))
        task = 'Alter %d indexes' % len(sqls)
        description = 'drop(%d)\nadd uniq:(%d)\nadd index:(%d)' % (len(drop), len(uni), len(key))
        content = self.content(sql, rob, task, description) 
        return self.edit_and_save(task, content)

    def scaffold(self, style, name):
        if not style:
            sql = '/* forward sql here */'
            rollback = '/* rollback sql here */'
            content = self.content(sql, rollback, name)
        else:
            content = """
            #!/usr/bin/env python
            # encoding: utf-8

            # 
            # ID: {{migration_id}}
            # timpstamp: {{timestamp}}
            # -------------------------------
            # {task}
            # 
            # <description>
            # -------------------------------
            #

            from yoyo import step

            def up(connection):
                # forward action here 
                pass

            def down(connection):
                # rollback action here 
                pass

            step(up, down)
            """.format(task=name)
        return self.edit_and_save(name, retab(content))


class Migrate(object):
    """
    usage: migrate [--version] [--config-file] <command> [<args>...]

    options:
       -h, --help       Show this

    The most commonly used commands are:
       snapshot         Snapshot current database schema

       create-table     Create table
       drop-table       Drop table
       alter-table      Alter table
       rename-table     Rename table
       alter-index      Operation on indexes

       migrate          Perform migration
       rollback         Rollback migration
       remove           Remove migrations
       new              Create a scaffold for migration

       status           Show status of migrations

    See 'migrate help <command>' for more information on a specific command.

    """

    def __init__(self):
        self()

    def __call__(self):
        self.main(docopt(
            doc=retab(self.__doc__),
            version=self.version_string,
            options_first=True))

    def read_config(self):
        db_config = {
                'host':'localhost',
                'port':'',
                'user':'root',
                'passwd':'',
                }
        db_config.update(app.config['DATABASE'])

        if db_config['passwd']:
            db_config['user'] += ':' + db_config['passwd'] 
        if db_config['port']:
            db_config['host'] += ':' + db_config['port'] 

        logging.debug(db_config)
        db_connection_url = "mysql://{user}@{host}/{name}".format(**db_config)
        self.db_config = db_config
        self.connection, self.paramstyle = connect(db_connection_url)
        self.migrations_dir = os.path.abspath(app.config['MIGRATIONS_DIR'])
        self.mg = MigrationGenerator(self.migrations_dir)

    @property
    def version(self):
        return (0, 0, 1)

    @property
    def version_string(self):
        return '.'.join(map(str, self.version))

    @property
    def tables(self):
        cursor = self.connection.cursor()
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()
        return [t[0] for t in tables]

    
    @property
    def migrations(self):
        migrations = yoyo.read_migrations(
                self.connection,
                self.paramstyle,
                self.migrations_dir)
        return migrations

    def snapshot(self, args):
        """
        usage: migrate snapshot [options]
            
            -h, --help
            --force      Force snapshot

        This command will clear all the migration history and generate
        a schema snapshot along with a migration. The snapshot will be
        applied immediately.
        
        You should use this command if you already have tables created
        in database and you want to persist them as a migration. You
        can also use this command to squash all migrations into one
        record.
        """
        if not os.path.isdir(self.migrations_dir):
            os.mkdir(self.migrations_dir)
        migrations = os.listdir(self.migrations_dir)

        if migrations and not args['--force']:
            raise Exception(
                    'Migration directory is not empty. \n'
                    'Use --force to clear all files there and force performing snapshot.')

        for migration in migrations:
            print "Removing:", migration
            os.remove(os.path.join(self.migrations_dir, migration))

        params = [
                'mysqldump',
                '-u {user}',
                '-h {host}',
                '--no-data',
                '--skip-comments',
                '--ignore-table={name}._yoyo_migration',
                '{name}'
                ]
        if self.db_config['password']: params.append('--password {password}')
        if self.db_config['port']: params.append('--port {port}')
        try:
            command = ' '.join(params).format(**self.db_config)
            logging.debug(command)
            output = subprocess.check_output([command], shell=True)
            mid = self.mg.snapshot(
                    output,
                    self.db_config['name'],
                    self.tables,
                    )
            print 'Applying snapshot'
            create_table = """
            CREATE TABLE IF NOT EXISTS `_yoyo_migration` (
              `id` varchar(255) NOT NULL,
              `ctime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
            """

            delete_yoyo = """
            DELETE FROM `_yoyo_migration`;
            """

            apply_mig = """
            INSERT INTO `_yoyo_migration` 
              VALUES (
                '{migration_id}',
                '{timestamp}'
              );
            """.format(
                    migration_id=mid,
                    timestamp=time.strftime('%Y-%m-%d %H:%M:%S'))
            cursor = self.connection.cursor()
            cursor.execute(create_table)
            self.connection.commit()
            cursor.execute(delete_yoyo)
            self.connection.commit()
            cursor.execute(apply_mig)
            self.connection.commit()
            cursor.close()
        except Exception as e:
            logging.critical("Error returned by mysqldump")
            logging.exception(e)
            exit(1)

    def create_table(self, args):
        """
        usage: migrate create-table <table> [<columns>...] 
                                   [--primary-key <primary_key>]
                                   [--unique-key <unique_keys>]...
                                   [--key <key>]...
            
            options:
                -p, --primary-key <primary_key>      Column to be used as primary key. 
                -u, --unique-key <unique_keys>...    Create unique index on columns.
                -k, --key <keys>...                  Create index on columns. 

            parameters:
                <table>       The name of table to be create
                <columns>...  Columns to be created.

            Examples:
                $ migrate create users id:int_11 name:varchar_20 description:text
                $ migrate create ex a:int b:int c:int -p a -k b -k c 

            You can use [:.#@] to seperate column name and type. Use underscore to
            specify type width, ex. varchar_20 will be translated to varchar(20). 
        """
        table = args['<table>'].strip()
        if table.isdigit() or not re.match('^[A-Za-z_0-9]+$', table):
            raise Exception("Invalid table name '%s'" % table)
        columns = {self._parse_colomn(c) for c in args['<columns>'] if c.strip()}
        pk = args['--primary-key'] or 'id'
        uk = set(args['--unique-key'])
        keys = set(args['--key'])

        if table in self.tables:
            raise Exception(
                    "Table '%s' already exists.\n"
                    "Forget to run `migrate migrate` ?" % table
                    )

        column_names = {c[0] for c in columns}
        if len(column_names) != len(columns):
            raise Exception('Duplicated column definition.')
        
        if pk not in column_names:
            if pk=='id':
                column_names.add('id')
                columns.add(('id', 'int'))
            else:
                raise Exception("Column '%s' not defined. (Primary Key)" % pk)

        if pk in uk or pk in keys:
            raise Exception("Primary key '%s' can not be unique key and key" % pk)

        sk = uk.intersection(keys)
        if len(sk) == 1:
            raise Exception("Column '%s' can not be both unique key and key" % sk.pop())
        if len(sk) > 1:
            raise Exception("Columns '%s' can not be both unique key and key" % "', '".join(sk))
        
        luk = uk - column_names
        if len(luk)==1:
            raise Exception("Column '%s' not defined. (Unique Key)" % luk.pop())
        elif len(luk)>1:
            raise Exception("Columns '%s' not defined. (Unique Key)" % "', '".join(luk))
        
        lkeys = keys - column_names
        if len(lkeys)==1:
            raise Exception("Column '%s' not defined. (Key)" % lkeys.pop())
        elif len(lkeys)>1:
            raise Exception("Columns '%s' not defined. (Key)" % "', '".join(lkeys))

        self.mg.create_table(table, columns, pk, uk, keys)
        
    def _parse_colomn(self, s):
        s = s.strip()
        if not s: return None
        part = re.split(r'[.#:@]', s)
        if len(part) == 1:
            return (part[0], 'int')
        elif len(part) == 2:
            n = part[0].strip()
            t = part[1].strip()
            m = re.match(r'^(\w+)_(\d+)$', t)
            if m:
                tn, tw = m.groups()
                t = "%s(%s)" % (tn, tw)
            return n.lower(), t.lower()
        else:
            raise Exception("Invalid column statement: " + s)


    def drop_table(self, args):
        """
        usage: migrate drop-table <table> 

        Drop the specifed table. This operation won't keep the
        data, thus, if you'd like to rollback this migration,
        only the table schema will be restored. 

        Be careful with this command.
        """
        table = args['<table>'].strip()
        if table.isdigit() or not re.match(r'^[A-Za-z_0-9]+$', table):
            raise Exception("Invalid table name '%s'" % table)
        if not table in self.tables:
            raise Exception(
                    "Table '%s' not exsits.\n"
                    "Forget to run `migrate migrate` ?" % table)
        params = [
                'mysqldump',
                '-u {user}',
                '-h {host}',
                '--no-data',
                '--skip-comments',
                '--ignore-table={name}._yoyo_migration',
                '{name}',
                table
                ]
        if self.db_config['password']: params.append('--password {password}')
        if self.db_config['port']: params.append('--port {port}')
        command = ' '.join(params).format(**self.db_config)
        rollback = subprocess.check_output([command], shell=True)
        mid = self.mg.drop_table(table, rollback)


    def alter_table(self, args):
        """
        usage: migrate alter-table <table> (-d | --drop) <columns>...
               migrate alter-table <table> (-a | --add) <columns>...
               migrate alter-table <table> (-c | --change) <column> <new-column>

            -d, --drop      Drop columns
            -a, --add       Add columns
            -c, --change    Change column datatype 
            -r, --rename    Rename table
        """
        table = args['<table>']
        schema = {c[0]:c[1:] for c in self._get_columns(table)}
        schema_keys = set(schema.keys())
        keys = {c[4]:c[1:3] for c in self._get_indexes(table)}
        if args['--drop']:
            columns = set(args['<columns>'])
            ic = columns - schema_keys
            if ic:
                raise Exception("Columns '%s' not exist" % "','".join(sorted(ic)))
            for k in ic:
                if schema[k][3] == 'PRI':
                    raise Exception("You can not drop primary key '%s'" % k)
            self.mg.drop_columns(table, columns, schema, keys)
        elif args['--add']:
            columns = set(args['<columns>'])
            ic = schema_keys.intersection(columns)
            if ic:
                raise Exception("Columns '%s' already exist" % "','".join(sorted(ic)))
            columns = {self._parse_colomn(c) for c in columns if c.strip()}
            schema = {c[0]:c[1] for c in columns}
            self.mg.add_columns(table, schema.keys(), schema, keys)
        elif args['--change']:
            column = args['<column>'].strip() 
            if not column in schema_keys:
                raise Exception("Column '%s' not exists" % column)
            ncolumn = args['<new-column>']
            if len(ncolumn.split(':'))>1:
                ncolumn, type_= self._parse_colomn(ncolumn)
            else:
                type_ = ''
            if ncolumn in schema_keys:
                raise Exception("Column '%s' already exists" % column)
            self.mg.alter_column_type(table, column, ncolumn, schema[column], type_)

    def rename_table(self, args):
        """
        usage: migrate rename-table <old-table> <new-table>
        """
        old = args['<old-table>']
        new = args['<new-table>']
        if not old in self.tables:
            raise Exception("Table '%s' not found" % old)
        if new in self.tables:
            raise Exception("Table '%s' already exist" % new)
        self.mg.rename_table(old, new)

    def _parse_index(self, string):
        s = string.strip().split(':')
        if len(s)==1:
            s = s[0]
            s = s.split('.')
            if len(s)==2:
                t, c = s
                return t, c, None
            else:
                return s[0], None, None
        elif len(s)==2:
            c, idx = s
            t, c, _ = self._parse_index(c)
            return t, c, idx
        raise Exception('Invalid key definition: %s' % string)

    def _get_columns(self, table):
        cursor = self.connection.cursor()
        cursor.execute('SHOW COLUMNS IN `%s`;' % table)
        return cursor.fetchall()

    def _get_indexes(self, table):
        cursor = self.connection.cursor()
        cursor.execute('SHOW INDEXES IN `%s`;' % table)
        return cursor.fetchall()

    def alter_index(self, args):
        """
        usage: migrate alter-index [-u | --add-unique-key <table.column:name>...]
                             [-k | --add-key  <table.column:name>...]
                             [-d | --drop-key <table.name>...]

            -u, --add-unique-key <n>   Add unique key on column
            -k, --add-key <n>          Add key key on column
            -d, --drop-key <n>         Drop key with table and name
        """
        uni = args['--add-unique-key']
        key = args['--add-key']
        drop = args['--drop-key']
        if not (uni or key or drop):
            docopt(retab(index.__doc__), args + ['--help'])
            return
        drop = set([self._parse_index(c) for c in drop if c.strip()])
        uni = set([self._parse_index(c) for c in uni if c.strip()])
        key = set([self._parse_index(c) for c in key if c.strip()])
        columns = {}
        indexes = {}
        drop_set = set()
        uni_set = set()
        key_set = set()
        for t, _, ii in drop:
            if not t in self.tables:
                raise Exception("Table '%s' not found" % t)
            idx = indexes.get(t)
            if not idx:
                inds = self._get_indexes(t)
                idx = {i[2] for i in inds}
                indexes[t] = idx 
                columns[t] = {i[2]:i[4] for i in inds}
            if not ii in idx:
                raise Exception("Can not drop index '%s:%s', index not found" % (t, ii))
            c = columns[t][ii]
            drop_set.add((t, c, ii))
         
        columns.clear()
        all_ind = set()
        for t, c, i in uni:
            if not i: i = 'uk_' + c
            if (t, i) in all_ind:
                raise Exception("Duplicated index '%s'" % i)
            all_ind.add((t, i))
            uni_set.add((t, c, i))

        for t, c, i in key:
            if not i: i = 'idx_' + c
            if (t, i) in all_ind:
                raise Exception("Duplicated index '%s.%s'" % (t, i))
            all_ind.add((t, i))
            key_set.add((t, c, i))
    
        for t, c, i in uni | key:
            if not t in self.tables:
                raise Exception("Table '%s' not found" % t)
            cols = columns.get(t)
            if not cols:
                colus = self._get_columns(t)
                cols = {c[0] for c in colus}
                columns[t] = cols
            if not c in cols:
                raise Exception("Can not add index on column '%s.%s', column not found" % (t, c))
            idx = indexes.get(t)
            if not idx:
                inds = self._get_indexes(t)
                idx = {i[2] for i in inds}
                indexes[t] = idx 
            if  i in idx:
                raise Exception("Can not add index '%s.%s', index already exist" % (t, i))
        self.mg.alter_index(drop_set, uni_set, key_set)

    def new(self, args):
        """
        usage: migrate new [-b | --alternative-style] <name>...

            -b, --alternative-style   Use alternative style
            
        This command generate a scaffold of an empty migration
        file with given name.
        """
        fstyle = args['--alternative-style']
        name = ' '.join(args['<name>'])
        self.mg.scaffold(fstyle, name)

    def apply(self, args):
        """
        usage: migrate apply
        """
        print 'Migrating database'
        self.migrations.to_apply().apply()
        self.connection.commit()

    def rollback(self, args):
        """
        usage: migrate rollback [-f|--force] (-n=<limit> | --number=<limit>)
               migrate rollback [-f|--force] (-t=<limit> | --tag=<prefix>)
               migrate rollback [-f|--force] (-a | -all)
               migrate rollback [-f|--force] (-i | --interactive)
           
            -f, --force            Force rollback, may case data loss
            -i, --interactive      Interactive rollback step by step
            -n, --number=<limit>   Number of migrations to rollback
            -t, --tag=<prefix>     Rollback to this tag
            -a, --all              Rollback all migrations

        """
        migrations = self.migrations
        to_rollback = migrations.to_rollback()
        if len(to_rollback) == 0: 
            raise Exception( "No migrations to rollback")
        force = args['--force']
        if args['--all']:
            to_rollback.rollback()
        elif args['--number']:
            number = args['--number']
            if not number.isdigit():
                raise Exception('--number must be an integer')
            to_rollback = to_rollback[:int(number)]
            to_rollback.rollback()
        elif args['--tag']:
            tag = args['--tag']
            for i, mig in enumerate(to_rollback, 1):
                if mig.id.startswith(tag):
                    break
            if i == len(to_rollback) and not to_rollback[-1].id.startswith(tag):
                raise Exception("Migration with tag '%s' not found" % tag)
            to_rollback = to_rollback[:i]
            to_rollback.rollback()
        elif args['--interactive']:
            for i, mig in enumerate(to_rollback):
                tr = to_rollback[i:i+1]
                print ""
                print "-> ", tr[0].id
                command = raw_input('rollback this migration (Y/n)?')
                print ""
                if command in ['', 'y', 'Y']:
                    tr.rollback()
                else:
                    break
    def status(self, args):
        """
        usage: migrate status
        """
        migrations = self.migrations
        if not migrations:
            print 'No migrations found'
            return
        print 'Migrations:'
        print ''
        to_apply = reversed(migrations.to_apply())
        to_rollback = migrations.to_rollback()
        for m in to_apply:
            print '   %-60s' % m.id

        if to_rollback:
            print '*  %-60s [current]' % to_rollback[0].id
            if len(to_rollback) > 1:
                for m in to_rollback[1:]:
                    print '-  %-60s' % m.id
            print ''
        else:
            print ''
            print 'No migrations have been applied.'
            print "Run 'migrate apply'."
            
    def remove(self, args):
        """
        usage: migrate remove [-y] (--top | --not-applied)
               migrate remove (-i | --interactive)
               migrate remove <tag>

            -y                 Do NOT confirm and delete directly
            --head             Remove the topest unapplied migrations
            --not-applied      Remove all migrations that haven't been applied
            -i, --interactive  Interactive remove

            <tag>              Remove all migrations to this tag 

        Remove unapplied migration files. To remove applied migrations,
        you have to rollback to it first.
        """
        to_apply = reversed(self.migrations.to_apply())
        to_remove = []
        top = args['--top']
        notapp = args['--not-applied']
        tag = args['<tag>']
        y = args['-y']
        inter = args['--interactive']
        
        if tag and len(tag) < 8:
            raise Exception('<tag> must be at least 8 chars')

        if inter:
            for m in to_apply:
                print ''
                print '-->', m.id
                inp = raw_input('Remove it(yes)?')
                print ''
                if inp.lower() in ['yes', 'y']:
                    to_remove.append(m)
                else:
                    break
        elif top:
            if not to_apply:
                raise Exception('No migrations not applied, rollback before remove')
            to_remove.append(to_apply.next()) 
        elif notapp:
            to_remove = list(to_apply)
        elif tag:
            find_tag = False
            for m in to_apply:
                if m.id.startswith(tag):
                    to_remove.append(m)
                    find_tag = True
                    break
                else:
                    to_remove.append(m)
            if not find_tag:
                raise Exception("Migrations with tag '%s' not found")
        if not to_remove:
            raise Exception('Nothing to remove. ')

        if not y:
            print "Migrations below will be deleted:"
            print ''
            for m in to_remove:
                print '  %s' % m.id
            print ''
            inp = raw_input('Are you sure? (yes)')
            if inp.strip().lower() in ['y', 'yes']:
                y = True
        if y:
            for m in to_remove:
                filepath = os.path.join(self.migrations_dir, m.id+'.py')
                print 'Removing:', os.path.basename(filepath)
                os.remove(filepath)
        else:
            print 'Abort'

    def main(self, argv):
        logging.debug(argv)
        command = argv['<command>']
        if command == 'snapshot':
            func = self.snapshot
        elif command == 'create-table':
            func = self.create_table
        elif command == 'drop-table':
            func = self.drop_table
        elif command == 'alter-table':
            func = self.alter_table
        elif command == 'rename-table':
            func = self.rename_table
        elif command == 'alter-index':
            func = self.alter_index
        elif command == 'apply':
            func = self.apply
        elif command == 'rollback':
            func = self.rollback
        elif command == 'new':
            func = self.new
        elif command == 'status':
            func = self.status
        elif command == 'remove':
            func = self.remove
        else:
            print 'Unrecognized command'
            print ""
            print "See 'migrate --help' for more information"
            return
        self.read_config()
        args = docopt(retab(func.__doc__), argv= [command] + argv['<args>'])
        try:
            func(args)
        except Exception as e:
            print e
            print ""
            print "See 'migrate %s --help' for more information" % command

if __name__ == '__main__':
    Migrate()
