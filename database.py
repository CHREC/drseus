from datetime import datetime
from os.path import exists
from sqlite3 import connect
from threading import Lock
from traceback import format_exc, format_stack


class database(object):
    log_trace = '__LOG_TRACE__'
    log_exception = '__LOG_EXCEPTION__'

    def __init__(self, campaign_data={}, result_data={},
                 database_file='campaign-data/db.sqlite3'):
        if not exists(database_file):
            raise Exception('could not find database file: '+database_file)
        self.campaign_data = campaign_data
        self.result_data = result_data
        self.database_file = database_file
        self.lock = Lock()

    def __enter__(self):

        def dict_factory(cursor, row):
            dictionary = {}
            for idx, col in enumerate(cursor.description):
                dictionary[col[0]] = row[idx]
            return dictionary

    # def __enter__(self):
        self.lock.acquire()
        self.connection = connect(self.database_file, timeout=60)
        self.connection.row_factory = dict_factory
        self.cursor = self.connection.cursor()
        return self

    def insert_dict(self, table, dictionary=None):
        if dictionary is None:
            if table == 'campaign':
                dictionary = self.campaign_data
            elif table == 'result':
                dictionary = self.result_data
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

    def update_dict(self, table, dictionary=None):
        if table == 'campaign':
            dictionary = self.campaign_data
        elif table == 'result':
            dictionary = self.result_data
        if 'timestamp' in dictionary:
            dictionary['timestamp'] = datetime.now()
        self.cursor.execute(
            'UPDATE log_{} SET {}=? WHERE id={}'.format(
                table,
                '=?,'.join(dictionary.keys()),
                str(dictionary['id'])),
            list(dictionary.values()))

    def log_event(self, level, source, event_type, description=None,
                  campaign=False):
        if description == self.log_trace:
            description = ''.join(format_stack()[:-2])
        elif description == self.log_exception:
            description = ''.join(format_exc())
        event_data = {'level': level,
                      'source': source,
                      'event_type': event_type,
                      'description': description,
                      'timestamp': None}
        if self.result_data and not campaign:
            event_data['result_id'] = self.result_data['id']
        else:
            event_data['campaign_id'] = self.campaign_data['id']
        self.insert_dict('event', event_data)

    def get_campaign_data(self):
        if not self.campaign_data['id']:
            self.cursor.execute('SELECT * FROM log_campaign '
                                'ORDER BY id DESC LIMIT 1')
            return self.cursor.fetchone()
        elif self.campaign_data['id'] == '*':
            self.cursor.execute('SELECT * FROM log_campaign ORDER BY id')
            return self.cursor.fetchall()
        else:
            self.cursor.execute('SELECT * FROM log_campaign WHERE id=?',
                                [self.campaign_data['id']])
            return self.cursor.fetchone()

    def get_result_data(self):
        self.cursor.execute('SELECT * FROM log_result WHERE campaign_id=?',
                            [self.campaign_data['id']])
        return self.cursor.fetchall()

    def get_result_item_data(self, item):
        self.cursor.execute('SELECT * FROM log_'+item+' WHERE result_id=? ',
                            [self.result_data['id']])
        return self.cursor.fetchall()

    def get_result_item_count(self, item):
        self.cursor.execute('SELECT COUNT(*) FROM log_'+item+' '
                            'WHERE result_id=?', [self.result_data['id']])
        return self.cursor.fetchone()['COUNT(*)']

    def delete_result(self):
        self.cursor.execute('DELETE FROM log_simics_memory_diff '
                            'WHERE result_id=?', [self.result_data['id']])
        self.cursor.execute('DELETE FROM log_simics_register_diff '
                            'WHERE result_id=?', [self.result_data['id']])
        self.cursor.execute('DELETE FROM log_injection WHERE result_id=?',
                            [self.result_data['id']])
        self.cursor.execute('DELETE FROM log_event WHERE result_id=?',
                            [self.result_data['id']])
        self.cursor.execute('DELETE FROM log_result WHERE id=?',
                            [self.result_data['id']])

    def delete_results(self):
        self.cursor.execute('DELETE FROM log_simics_memory_diff WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=?)', [self.campaign_data['id']])
        self.cursor.execute('DELETE FROM log_simics_register_diff WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=?)', [self.campaign_data['id']])
        self.cursor.execute('DELETE FROM log_injection WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=?)', [self.campaign_data['id']])
        self.cursor.execute('DELETE FROM log_event WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=?)', [self.campaign_data['id']])
        self.cursor.execute('DELETE FROM log_result WHERE campaign_id=?',
                            [self.campaign_data['id']])

    def delete_campaign(self):
        self.delete_results()
        self.cursor.execute('DELETE FROM log_event WHERE campaign_id=?',
                            [self.campaign_data['id']])
        self.cursor.execute('DELETE FROM log_campaign WHERE id=?',
                            [self.campaign_data['id']])

    def __exit__(self, type_, value, traceback):
        self.connection.commit()
        self.connection.close()
        self.lock.release()
        if type_ is not None or value is not None or traceback is not None:
            return False  # reraise exception
