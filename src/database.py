from datetime import datetime
from django.core.management import execute_from_command_line as django_command
from getpass import getuser
from psycopg2 import connect, OperationalError
from psycopg2.extras import DictCursor
from subprocess import DEVNULL, PIPE, Popen
from sys import argv
from sys import stdout as sys_stdout
from termcolor import colored
from threading import Lock
from traceback import format_exc, format_stack

from .log import initialize_django


class database(object):
    log_exception = '__LOG_EXCEPTION__'
    log_trace = '__LOG_TRACE__'

    def __init__(self, options, campaign={}, create_result=False,
                 initialize=False):
        if not campaign:
            campaign = {'id': options.campaign_id}
        self.campaign = campaign
        self.result = {}
        self.options = options
        self.lock = Lock()
        if create_result:
            with self as db:
                db.__create_result(supervisor=options.command == 'supervise')
        if not self.exists():
            if initialize:
                commands = (
                    ('CREATE USER '+self.options.db_user +
                        ' WITH PASSWORD \''+self.options.db_password+'\';'),
                    ('ALTER ROLE '+self.options.db_user +
                        ' SET client_encoding TO \'utf8\';'),
                    ('ALTER ROLE '+self.options.db_user +
                        ' SET default_transaction_isolation'
                        ' TO \'read committed\';'),
                    ('ALTER ROLE '+self.options.db_user +
                        ' SET timezone TO \'UTC\';'),
                    ('CREATE DATABASE '+self.options.db_name +
                        ' WITH OWNER '+self.options.db_user))
                self.psql(superuser=True, commands=commands)
                initialize_django(self.options)
                django_command([argv[0], 'makemigrations', 'log'])
                django_command([argv[0], 'migrate'])
            else:
                raise Exception('could not connect to database, '
                                'try creating a new campaign')

    def __enter__(self):
        self.lock.acquire()
        try:
            self.connection = connect(host=self.options.db_host,
                                      port=self.options.db_port,
                                      database=self.options.db_name,
                                      user=self.options.db_user,
                                      password=self.options.db_password,
                                      cursor_factory=DictCursor)
            self.cursor = self.connection.cursor()
        except KeyboardInterrupt:
            self.lock.release()
            raise KeyboardInterrupt
        return self

    def __exit__(self, type_, value, traceback):
        try:
            self.connection.commit()
            self.connection.close()
        finally:
            self.lock.release()
        if type_ is not None or value is not None or traceback is not None:
            return False  # reraise exception

    def psql(self, executable='psql', superuser=False, database=False,
             args=[], commands=[], stdin=None, stdout=None):
        if commands and stdin is not None:
            print('cannot simultaneously send commands and redirect stdin, '
                  'ignoring stdin redirect')
        popen_command = []
        if superuser and self.options.db_superuser != getuser() and \
                self.options.db_superuser_password is None:
            print('running "'+executable+'" with sudo, '
                  'password may be required')
            popen_command.extend(['sudo', '-u', self.options.db_superuser])
        popen_command.append(executable)
        if self.options.db_host != 'localhost' or \
                not (superuser and self.options.db_superuser_password is None):
            popen_command.extend(['-h', self.options.db_host, '-W'])
            password_prompt = True
        else:
            password_prompt = False
        popen_command.extend(['-p', str(self.options.db_port)])
        if not superuser:
            popen_command.extend(['-U', self.options.db_user])
        if database:
            popen_command.extend(['-d', self.options.db_name])
        if args:
            popen_command.extend(args)
        kwargs = {}
        if commands:
            kwargs.update({'stdin': PIPE, 'universal_newlines': True})
        elif stdin:
            kwargs['stdin'] = stdin
        if stdout:
            kwargs['stdout'] = stdout
        process = Popen(popen_command, **kwargs)
        if commands:
            for command in commands:
                print(executable+'>', command)
                process.stdin.write(command+'\n')
            process.stdin.close()
        if password_prompt:
            print('user', end=' ')
            if superuser:
                print(self.options.db_superuser, end=' ')
            else:
                print(self.options.db_user, end=' ')
            sys_stdout.flush()
        process.wait()
        if process.returncode:
            raise Exception(executable+' error')

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
            [('{'+','.join(map(str, value))+'}') if isinstance(value, list) or
             isinstance(value, tuple) else value
             for value in dictionary.values()])
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
            [('{'+','.join(map(str, value))+'}') if isinstance(value, list) or
             isinstance(value, tuple) else value
             for value in dictionary.values()])

    def __create_result(self, supervisor=False):
        self.result.update({'aux_output': '',
                            'campaign_id': self.campaign['id'],
                            'cycles': None,
                            'data_diff': None,
                            'debugger_output': '',
                            'detected_errors': None,
                            'dut_output': '',
                            'execution_time': None,
                            'num_injections': None,
                            'outcome_category': ('DrSEUs' if supervisor
                                                 else 'Incomplete'),
                            'outcome': ('Supervisor' if supervisor
                                        else 'In progress'),
                            'returned': None,
                            'timestamp': None})
        self.insert('result')

    def log_result(self, supervisor=False, exit=False):
        if self.result['outcome_category'] != 'DrSEUs':
            if 'dut_serial_port' in self.result:
                out = self.result['dut_serial_port']+', '
            else:
                out = ''
            out += (str(self.result['id'])+': ' +
                    self.result['outcome_category']+' - ' +
                    self.result['outcome'])
            if self.result['data_diff'] is not None and \
                    self.result['data_diff'] < 1.0:
                out += ' {0:.2f}%'.format(min(self.result['data_diff']*100,
                                              99.990))
            print(colored(out, 'blue'))
        self.update('result')
        if not exit:
            self.__create_result(supervisor)

    def log_event(self, level, source, type_, description=None,
                  success=None, campaign=False):
        if description == self.log_trace:
            description = ''.join(format_stack()[:-2])
            success = False
        elif description == self.log_exception:
            description = ''.join(format_exc())
            success = False
        event = {'description': description,
                 'type': type_,
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

    def log_event_success(self, event, success=True, update_timestamp=False):
        event['success'] = success
        if not update_timestamp:
            timestamp = event['timestamp']
            del event['timestamp']
        self.update('event', event)
        if not update_timestamp:
            event['timestamp'] = timestamp

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

    def delete_database(self, delete_user):
        commands = ['DROP DATABASE '+self.options.db_name+';']
        if delete_user:
            commands.append('DROP USER '+self.options.db_user+';')
        self.psql(superuser=delete_user or self.options.db_host == 'localhost',
                  commands=commands)

    def backup_database(self, backup_file):
        with open(backup_file, 'w') as backup:
            self.psql(superuser=self.options.db_host == 'localhost',
                      executable='pg_dump', database=True, args=['-c'],
                      stdout=backup)

    def restore_database(self, backup_file):
        with open(backup_file, 'r') as backup:
            self.psql(superuser=True, database=True,
                      args=['--single-transaction'], stdin=backup,
                      stdout=DEVNULL)
