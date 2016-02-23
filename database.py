from datetime import datetime
from django.conf import settings as django_settings
from django.core.management import execute_from_command_line as django_command
from psycopg2 import connect, OperationalError
from psycopg2.extras import DictCursor
from subprocess import PIPE, Popen
from termcolor import colored
from threading import Lock
from traceback import format_exc, format_stack


class database(object):
    log_exception = '__LOG_EXCEPTION__'
    log_trace = '__LOG_TRACE__'

    def __init__(self, options, campaign={}, create_result=False,
                 log_settings=None):
        if not campaign:
            campaign = {'id': options.campaign_id}
        self.campaign = campaign
        self.result = {}
        self.host = options.db_host
        self.port = options.db_port
        self.database = options.db_name
        self.password = options.db_password
        self.lock = Lock()
        if create_result:
            with self as db:
                db.__create_result()
        if not self.exists():
            if log_settings is not None:
                print('adding drseus user and database to postgresql, '
                      'root privileges (sudo) required')
                psql = Popen(['sudo', '-u', 'postgres', 'psql'], bufsize=0,
                             universal_newlines=True, stdin=PIPE)
                for command in (
                    "CREATE DATABASE "+self.database+";",
                    "CREATE USER drseus WITH PASSWORD '"+self.password+"';",
                    "ALTER ROLE drseus SET client_encoding TO 'utf8';",
                    ("ALTER ROLE drseus SET default_transaction_isolation "
                        "TO 'read committed';"),
                    "ALTER ROLE drseus SET timezone TO 'UTC';",
                    ("GRANT ALL PRIVILEGES ON DATABASE "+self.database +
                        " TO drseus;")):
                    print('psql>', command)
                    psql.stdin.write(command+'\n')
                psql.stdin.close()
                psql.wait()
                django_settings.configure(**log_settings)
                django_command(['drseus', 'makemigrations', 'log'])
                django_command(['drseus', 'migrate'])
            else:
                raise Exception('could not connect to database')

    def __enter__(self):
        self.lock.acquire()
        self.connection = connect(host=self.host, port=self.port,
                                  database=self.database, user='drseus',
                                  password=self.password,
                                  cursor_factory=DictCursor)
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, type_, value, traceback):
        self.connection.commit()
        self.connection.close()
        self.lock.release()
        if type_ is not None or value is not None or traceback is not None:
            return False  # reraise exception

    def exists(self):
        try:
            self.__enter__()
        except OperationalError:
            self.lock.release()
            return False
        else:
            self.__exit__(None, None, None)
            return True

    def insert(self, table, dictionary=None):
        if dictionary is None:
            if table == 'campaign':
                dictionary = self.campaign
            elif table == 'result':
                dictionary = self.result
        if 'timestamp' in dictionary:
            dictionary['timestamp'] = datetime.now()
        if 'id' in dictionary:
            del dictionary['id']
        self.cursor.execute(
            'INSERT INTO log_{} ({}) VALUES ({}) RETURNING id'.format(
                table,
                ', '.join(dictionary.keys()),
                ', '.join(['%s']*len(dictionary))),
            list(dictionary.values()))
        dictionary['id'] = self.cursor.fetchone()[0]

    def update(self, table, dictionary=None):
        if table == 'campaign':
            dictionary = self.campaign
        elif table == 'result':
            dictionary = self.result
        if 'timestamp' in dictionary:
            dictionary['timestamp'] = datetime.now()
        self.cursor.execute(
            'UPDATE log_{} SET {}=%s WHERE id={}'.format(
                table,
                '=%s, '.join(dictionary.keys()),
                str(dictionary['id'])),
            list(dictionary.values()))

    def __create_result(self):
        self.result.update({'campaign_id': self.campaign['id'],
                            'aux_output': '',
                            'data_diff': None,
                            'debugger_output': '',
                            'detected_errors': None,
                            'dut_output': '',
                            'num_injections': None,
                            'outcome_category': 'Incomplete',
                            'outcome': 'In progress',
                            'timestamp': None})
        self.insert('result')

    def log_result(self, create_result=True):
        out = (self.result['dut_serial_port']+', '+str(self.result['id']) +
               ': '+self.result['outcome_category']+' - ' +
               self.result['outcome'])
        if self.result['data_diff'] is not None and \
                self.result['data_diff'] < 1.0:
            out += ' {0:.2f}%'.format(min(self.result['data_diff']*100,
                                          99.990))
        print(colored(out, 'blue'))
        self.update('result')
        if create_result:
            self.__create_result()

    def log_event(self, level, source, event_type, description=None,
                  success=None, campaign=False):
        if description == self.log_trace:
            description = ''.join(format_stack()[:-2])
            success = False
        elif description == self.log_exception:
            description = ''.join(format_exc())
            success = False
        event = {'description': description,
                 'event_type': event_type,
                 'level': level,
                 'source': source,
                 'success': success,
                 'timestamp': None}
        if self.result and not campaign:
            event['result_id'] = self.result['id']
        else:
            event['campaign_id'] = self.campaign['id']
        self.insert('event', event)
        return event

    def log_event_success(self, event, success=True):
        event['success'] = success
        self.update('event', event)

    def get_campaign(self):
        if not self.campaign['id']:
            self.cursor.execute('SELECT * FROM log_campaign '
                                'ORDER BY id DESC LIMIT 1')
            return self.cursor.fetchone()
        elif self.campaign['id'] == '*':
            self.cursor.execute('SELECT * FROM log_campaign ORDER BY id')
            return self.cursor.fetchall()
        else:
            self.cursor.execute('SELECT * FROM log_campaign WHERE id=%s',
                                [self.campaign['id']])
            return self.cursor.fetchone()

    def get_result(self):
        self.cursor.execute('SELECT * FROM log_result WHERE campaign_id=%s',
                            [self.campaign['id']])
        return self.cursor.fetchall()

    def get_item(self, item):
        self.cursor.execute('SELECT * FROM log_'+item+' WHERE result_id=%s ',
                            [self.result['id']])
        return self.cursor.fetchall()

    def get_count(self, item, item_from='result'):
        self.cursor.execute('SELECT COUNT(*) FROM log_'+item+' WHERE ' +
                            item_from+'_id=%s',
                            [getattr(self, item_from)['id']])
        return self.cursor.fetchone()[0]

    def delete_result(self):
        self.cursor.execute('DELETE FROM log_simics_memory_diff '
                            'WHERE result_id=%s', [self.result['id']])
        self.cursor.execute('DELETE FROM log_simics_register_diff '
                            'WHERE result_id=%s', [self.result['id']])
        self.cursor.execute('DELETE FROM log_injection WHERE result_id=%s',
                            [self.result['id']])
        self.cursor.execute('DELETE FROM log_event WHERE result_id=%s',
                            [self.result['id']])
        self.cursor.execute('DELETE FROM log_result WHERE id=%s',
                            [self.result['id']])

    def delete_results(self):
        self.cursor.execute('DELETE FROM log_simics_memory_diff WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=%s)', [self.campaign['id']])
        self.cursor.execute('DELETE FROM log_simics_register_diff WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=%s)', [self.campaign['id']])
        self.cursor.execute('DELETE FROM log_injection WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=%s)', [self.campaign['id']])
        self.cursor.execute('DELETE FROM log_event WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=%s)', [self.campaign['id']])
        self.cursor.execute('DELETE FROM log_result WHERE campaign_id=%s',
                            [self.campaign['id']])

    def delete_campaign(self):
        self.delete_results()
        self.cursor.execute('DELETE FROM log_event WHERE campaign_id=%s',
                            [self.campaign['id']])
        self.cursor.execute('DELETE FROM log_campaign WHERE id=%s',
                            [self.campaign['id']])

    def delete_database(self):
        print('deleting drseus user and database to postgresql, '
              'root privileges required')
        psql = Popen(['sudo', '-u', 'postgres', 'psql'], bufsize=0,
                     universal_newlines=True, stdin=PIPE)
        for command in (
                "DROP DATABASE "+self.database+";",
                "DROP USER drseus;"):
            print('psql>', command)
            psql.stdin.write(command+'\n')
        psql.stdin.close()
        psql.wait()
