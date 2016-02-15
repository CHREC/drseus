from datetime import datetime
from os.path import exists
from sqlite3 import connect
from termcolor import colored
from threading import Lock
from traceback import format_exc, format_stack


class database(object):
    log_exception = '__LOG_EXCEPTION__'
    log_trace = '__LOG_TRACE__'

    def __init__(self, campaign={}, create_result=False,
                 database_file='campaign-data/db.sqlite3'):
        if not exists(database_file):
            raise Exception('could not find database file: '+database_file)
        self.campaign = campaign
        self.result = {}
        self.file = database_file
        self.lock = Lock()
        if create_result:
            with self as db:
                db.__create_result()

    def __enter__(self):

        def dict_factory(cursor, row):
            dictionary = {}
            for id_, column in enumerate(cursor.description):
                dictionary[column[0]] = row[id_]
            return dictionary

    # def __enter__(self):
        self.lock.acquire()
        self.connection = connect(self.file, timeout=30)
        self.connection.row_factory = dict_factory
        self.cursor = self.connection.cursor()
        return self

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
            'INSERT INTO log_{} ({}) VALUES ({})'.format(
                table,
                ','.join(dictionary.keys()),
                ','.join('?'*len(dictionary))),
            list(dictionary.values()))
        dictionary['id'] = self.cursor.lastrowid

    def update(self, table, dictionary=None):
        if table == 'campaign':
            dictionary = self.campaign
        elif table == 'result':
            dictionary = self.result
        if 'timestamp' in dictionary:
            dictionary['timestamp'] = datetime.now()
        self.cursor.execute(
            'UPDATE log_{} SET {}=? WHERE id={}'.format(
                table,
                '=?,'.join(dictionary.keys()),
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
                            'outcome': 'Incomplete',
                            'timestamp': None})
        self.insert('result')

    def log_result(self, create_result=True):
        out = (self.result['dut_serial_port']+', '+str(self.result['id']) +
               ': '+self.result['outcome_category']+' - ' +
               self.result['outcome'])
        if self.result['data_diff'] is not None and \
                self.result['data_diff'] < 1.0:
            out += ' {0:.2f}%'.format(max(self.result['data_diff']*100,
                                          99.990))
        print(colored(out, 'blue'))
        self.update('result')
        if create_result:
            self.__create_result()

    def log_event(self, level, source, event_type, description=None,
                  campaign=False, success=None):
        if description == self.log_trace:
            description = ''.join(format_stack()[:-2])
        elif description == self.log_exception:
            description = ''.join(format_exc())
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
            self.cursor.execute('SELECT * FROM log_campaign WHERE id=?',
                                [self.campaign['id']])
            return self.cursor.fetchone()

    def get_result(self):
        self.cursor.execute('SELECT * FROM log_result WHERE campaign_id=?',
                            [self.campaign['id']])
        return self.cursor.fetchall()

    def get_item(self, item):
        self.cursor.execute('SELECT * FROM log_'+item+' WHERE result_id=? ',
                            [self.result['id']])
        return self.cursor.fetchall()

    def get_count(self, item, item_from='result'):
        self.cursor.execute('SELECT COUNT(*) FROM log_'+item+' WHERE ' +
                            item_from+'_id=?', [getattr(self, item_from)['id']])
        return self.cursor.fetchone()['COUNT(*)']

    def delete_result(self):
        self.cursor.execute('DELETE FROM log_simics_memory_diff '
                            'WHERE result_id=?', [self.result['id']])
        self.cursor.execute('DELETE FROM log_simics_register_diff '
                            'WHERE result_id=?', [self.result['id']])
        self.cursor.execute('DELETE FROM log_injection WHERE result_id=?',
                            [self.result['id']])
        self.cursor.execute('DELETE FROM log_event WHERE result_id=?',
                            [self.result['id']])
        self.cursor.execute('DELETE FROM log_result WHERE id=?',
                            [self.result['id']])

    def delete_results(self):
        self.cursor.execute('DELETE FROM log_simics_memory_diff WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=?)', [self.campaign['id']])
        self.cursor.execute('DELETE FROM log_simics_register_diff WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=?)', [self.campaign['id']])
        self.cursor.execute('DELETE FROM log_injection WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=?)', [self.campaign['id']])
        self.cursor.execute('DELETE FROM log_event WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=?)', [self.campaign['id']])
        self.cursor.execute('DELETE FROM log_result WHERE campaign_id=?',
                            [self.campaign['id']])

    def delete_campaign(self):
        self.delete_results()
        self.cursor.execute('DELETE FROM log_event WHERE campaign_id=?',
                            [self.campaign['id']])
        self.cursor.execute('DELETE FROM log_campaign WHERE id=?',
                            [self.campaign['id']])

    def __exit__(self, type_, value, traceback):
        self.connection.commit()
        self.connection.close()
        self.lock.release()
        if type_ is not None or value is not None or traceback is not None:
            return False  # reraise exception
