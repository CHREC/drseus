from datetime import datetime
from io import StringIO
import os
import sqlite3
from traceback import print_exc


class sql(object):
    def __init__(self, database='campaign-data/db.sqlite3', row_factory=''):
        if not os.path.exists(database):
            raise Exception('could not find database file: '+database)
        self.database = database
        self.row_factory = row_factory

    def __enter__(self):

        def dict_factory(cursor, row):
            dictionary = {}
            for idx, col in enumerate(cursor.description):
                dictionary[col[0]] = row[idx]
            return dictionary

    # def __enter__(self):
        self.connection = sqlite3.connect(self.database, timeout=60)
        if self.row_factory == 'row':
            self.connection.row_factory = sqlite3.Row
        elif self.row_factory == 'dict':
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
        self.connection.commit()

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
        self.connection.commit()

    def log_event(self, result_id, source, event_type, description=None):
        event_data = {'result_id': result_id,
                      'source': source,
                      'event_type': event_type,
                      'description': description,
                      'timestamp': None}
        self.insert_dict('event', event_data)

    def log_event_exception(self, result_id, source, event_type):
        string_file = StringIO()
        print_exc(file=string_file)
        exception = string_file.getvalue()
        string_file.close()
        self.log_event(result_id, source, event_type, exception)

    def __exit__(self, type_, value, traceback):
        self.connection.close()
        if type_ is not None or value is not None or traceback is not None:
            return False  # reraise exception
