from datetime import datetime
from os.path import exists
from sqlite3 import connect
from traceback import format_exc, format_stack


class sql(object):
    log_trace = '__LOG_TRACE__'
    log_exception = '__LOG_EXCEPTION__'

    def __init__(self, database='campaign-data/db.sqlite3'):
        if not exists(database):
            raise Exception('could not find database file: '+database)
        self.database = database

    def __enter__(self):

        def dict_factory(cursor, row):
            dictionary = {}
            for idx, col in enumerate(cursor.description):
                dictionary[col[0]] = row[idx]
            return dictionary

    # def __enter__(self):
        self.connection = connect(self.database, timeout=60)
        self.connection.row_factory = dict_factory
        self.cursor = self.connection.cursor()
        return self

    def insert_dict(self, table, dictionary):
        if 'timestamp' in dictionary:
            dictionary['timestamp'] = datetime.now()
        self.cursor.execute(
            'INSERT INTO log_{} ({}) VALUES ({})'.format(
                table,
                ','.join(dictionary.keys()),
                ','.join('?'*len(dictionary))),
            list(dictionary.values()))
        if table == 'injection' and dictionary['injection_number'] == 1:
            self.cursor.execute('DELETE FROM log_injection '
                                'WHERE injection_number=0 AND result_id=?',
                                [dictionary['result_id']])

    def update_dict(self, table, dictionary, row_id=None):
        if row_id is None:
            if 'id' in dictionary:
                row_id = dictionary['id']
            else:
                raise Exception('Unknown sql row id to update')
        if 'timestamp' in dictionary:
            dictionary['timestamp'] = datetime.now()
        self.cursor.execute(
            'UPDATE log_{} SET {}=? WHERE id={}'.format(
                table,
                '=?,'.join(dictionary.keys()),
                str(row_id)),
            list(dictionary.values()))

    def log_event(self, id_, level, source, event_type, description, result):
        if description == self.log_trace:
            description = ''.join(format_stack()[:-2])
        elif description == self.log_exception:
            description = ''.join(format_exc())
        event_data = {'level': level,
                      'source': source,
                      'event_type': event_type,
                      'description': description,
                      'timestamp': None}
        event_data[('result' if result else 'campaign')+'_id'] = id_
        self.insert_dict('event', event_data)

    def get_campaign_data(self, campaign_id):
        if not campaign_id:
            self.cursor.execute('SELECT * FROM log_campaign '
                                'ORDER BY id DESC LIMIT 1')
            return self.cursor.fetchone()
        elif campaign_id == '*':
            self.cursor.execute('SELECT * FROM log_campaign ORDER BY id')
            return self.cursor.fetchall()
        else:
            self.cursor.execute('SELECT * FROM log_campaign WHERE id=?',
                                [campaign_id])
            return self.cursor.fetchone()

    def get_result_data(self, campaign_id):
        self.cursor.execute('SELECT * FROM log_result WHERE campaign_id=?',
                            [campaign_id])
        return self.cursor.fetchall()

    def get_result_item_data(self, result_id, item):
        self.cursor.execute('SELECT * FROM log_'+item+' WHERE result_id=? ',
                            [result_id])
        return self.cursor.fetchall()

    def get_result_item_count(self, result_id, item):
        self.cursor.execute('SELECT COUNT(*) FROM log_'+item+' '
                            'WHERE result_id=?', [result_id])
        return self.cursor.fetchone()['COUNT(*)']

    def delete_results(self, campaign_id):
        self.cursor.execute('DELETE FROM log_simics_memory_diff WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=?)', [campaign_id])
        self.cursor.execute('DELETE FROM log_simics_register_diff WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=?)', [campaign_id])
        self.cursor.execute('DELETE FROM log_injection WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=?)', [campaign_id])
        self.cursor.execute('DELETE FROM log_event WHERE '
                            'result_id IN (SELECT id FROM log_result '
                            'WHERE campaign_id=?)', [campaign_id])
        self.cursor.execute('DELETE FROM log_result WHERE campaign_id=?',
                            [campaign_id])

    def delete_campaign(self, campaign_id):
        self.delete_results(campaign_id)
        self.cursor.execute('DELETE FROM log_event WHERE campaign_id=?',
                            [campaign_id])
        self.cursor.execute('DELETE FROM log_campaign WHERE id=?',
                            [campaign_id])

    def __exit__(self, type_, value, traceback):
        self.connection.commit()
        self.connection.close()
        if type_ is not None or value is not None or traceback is not None:
            return False  # reraise exception
