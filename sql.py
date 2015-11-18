def dict_factory(cursor, row):
        dictionary = {}
        for idx, col in enumerate(cursor.description):
            dictionary[col[0]] = row[idx]
        return dictionary


def insert_dict(cursor, table, dictionary):
    cursor.execute('INSERT INTO drseus_logging_'+table +
                   ' ({}) VALUES ({})'.format(','.join(dictionary.keys()),
                                              ','.join('?'*len(dictionary))),
                   dictionary.values())


def update_dict(cursor, table, dictionary, row_id):
    cursor.execute('UPDATE drseus_logging_'+table+' SET'
                   ' {}=?'.format('=?,'.join(dictionary.keys())) +
                   ' WHERE id='+str(row_id), dictionary.values())
