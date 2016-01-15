import os
import sqlite3


class sql():
    def dict_factory(cursor, row):
        dictionary = {}
        for idx, col in enumerate(cursor.description):
            dictionary[col[0]] = row[idx]
        return dictionary

    def __init__(self, database='campaign-data/db.sqlite3', row_factory=''):
        if not os.path.exists(database):
            raise Exception('could not find database file: '+database)
        self.database = database
        self.row_factory = row_factory

    def __enter__(self):
        self.connection = sqlite3.connect(self.database, timeout=60)
        if self.row_factory == 'row':
            self.connection.row_factory = sqlite3.Row
        elif self.row_factory == 'dict':
            self.connection.row_factory = self.dict_factory
        self.cursor = self.connection.cursor()
        return self

    def insert_dict(self, table, dictionary):
        self.cursor.execute(
            'INSERT INTO log_{} ({}) VALUES ({})'.format(
                table,
                ','.join(dictionary.keys()),
                ','.join('?'*len(dictionary))),
            dictionary.values())
        self.connection.commit()

    def update_dict(self, table, dictionary, row_id):
        self.cursor.execute(
            'UPDATE log_{} SET {}=? WHERE id={}'.format(
                table,
                '=?,'.join(dictionary.keys()),
                str(row_id)),
            dictionary.values())
        self.connection.commit()

    def __exit__(self, type_, value, traceback):
        self.connection.close()
        if type_ is not None or value is not None or traceback is not None:
            return False  # reraise exception
