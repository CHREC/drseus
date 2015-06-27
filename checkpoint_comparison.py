import sqlite3

from simics_targets import devices

# TODO: consider saving pickle of parsed registers from gold checkpoints


def parse_registers(config_file, board, targets):
    """
    Retrieves all the register values of the targets specified in
    simics_targets.py for the specified checkpoint config_file and returns a
    dictionary with all the values.
    """
    registers = {}
    for target in targets:
        if target != 'TLB':
            if 'count' in targets[target]:
                count = targets[target]['count']
            else:
                count = 1
            for target_index in xrange(count):
                config_object = 'DUT_'+board+targets[target]['OBJECT']
                config_type = targets[target]['TYPE']
                if count > 1:
                    config_object += '['+str(target_index)+']'
                if target == 'GPR':
                    target_key = config_object + ':gprs'
                else:
                    target_key = config_object
                registers[target_key] = {}
                with open(config_file, 'r') as config:
                    current_line = config.readline()
                    while ('OBJECT '+config_object+' TYPE '+config_type+' {'
                           not in current_line):
                        current_line = config.readline()
                        if current_line == '':
                            raise Exception('checkpoint_comparison.py:'
                                            'parse_registers(): '
                                            'could not find '+config_object +
                                            ' in '+config_file)
                    current_line = config.readline()
                    while 'OBJECT' not in current_line and current_line != '':
                        if ':' in current_line:
                            current_item = current_line.split(':')[0].strip()
                            if current_item in targets[target]['registers']:
                                if 'count' in (targets[target]['registers']
                                                      [current_item]):
                                    dimensions = len(targets[target]
                                                            ['registers']
                                                            [current_item]
                                                            ['count'])
                                    register_buffer = current_line.strip()
                                    if dimensions == 1:
                                        while ')' not in current_line:
                                            current_line = config.readline()
                                            register_buffer += \
                                                current_line.strip()
                                        register_buffer = \
                                            register_buffer.replace(' ', '')
                                        register_list = register_buffer[
                                            register_buffer.index('(')+1:
                                            register_buffer.index(')')
                                        ].split(',')
                                    elif dimensions == 2:
                                        while '))' not in current_line:
                                            current_line = config.readline()
                                            register_buffer += \
                                                current_line.strip()
                                        register_buffer = \
                                            register_buffer.replace(' ', '')
                                        register_list = register_buffer[
                                            register_buffer.index('((')+2:
                                            register_buffer.index('))')
                                        ].split('),(')
                                        for index in xrange(len(register_list)):
                                            register_list[index] = \
                                                register_list[index].split(',')
                                    else:
                                        raise Exception(
                                            'checkpoint_comparison.py:'
                                            'parse_registers(): '
                                            'Too many dimensions for register'
                                            ' in target: '+target)
                                    registers[target_key][current_item] = \
                                        register_list
                                else:
                                    current_value = \
                                        current_line.split(':')[1].strip()
                                    registers[target_key][current_item] = \
                                        current_value
                        current_line = config.readline()
                if (len(registers[target_key]) !=
                        len(targets[target]['registers'])):
                    print registers[target_key]
                    print targets[target]['registers']
                    missing_registers = []
                    for register in targets[target]['registers']:
                        if register not in registers[target_key]:
                            missing_registers.append(register)
                    raise Exception('checkpoint_comparison.py:'
                                    'parse_registers(): '
                                    'Could not find the following registers '
                                    'for '+config_object+': ' +
                                    str(missing_registers))
    return registers


def compare_registers(injection_number, monitored_checkpoint_number,
                      gold_checkpoint, monitored_checkpoint, board):
    """
    Compares the register values of the monitored_checkpoint to the
    gold_checkpoint and adds the differences to the database.
    """
    if board == 'p2020rdb':
        targets = devices['P2020']
    elif board == 'a9x4':
        targets = devices['A9']
    gold_registers = parse_registers(gold_checkpoint+'/config', board, targets)
    monitored_registers = parse_registers(monitored_checkpoint+'/config', board,
                                          targets)
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
    sql = sql_db.cursor()
    for target in targets:
        if target != 'TLB':
            if 'count' in targets[target]:
                target_count = targets[target]['count']
            else:
                target_count = 1
            for target_index in xrange(target_count):
                config_object = 'DUT_'+board+targets[target]['OBJECT']
                if target_count > 1:
                    config_object += '['+str(target_index)+']'
                if target == 'GPR':
                    target_key = config_object + ':gprs'
                else:
                    target_key = config_object
                for register in targets[target]['registers']:
                    if 'count' in targets[target]['registers'][register]:
                        register_count = (targets[target]['registers']
                                                 [register]['count'])
                    else:
                        register_count = ()
                    if len(register_count) == 0:
                        if (monitored_registers[target_key][register] !=
                                gold_registers[target_key][register]):
                            sql.execute(
                                'INSERT INTO ' +
                                'drseus_logging_simics_register_diff '
                                '(injection_id,monitored_checkpoint_number,'
                                'config_object,register,gold_value,'
                                'monitored_value) VALUES (?,?,?,?,?,?)', (
                                    injection_number,
                                    monitored_checkpoint_number, target_key,
                                    register,
                                    gold_registers[target_key][register],
                                    monitored_registers[target_key][register]
                                )
                            )
                    elif len(register_count) == 1:
                        for index1 in xrange(register_count[0]):
                            if (monitored_registers[target_key]
                                                   [register][index1] !=
                                gold_registers[target_key]
                                              [register][index1]):
                                sql.execute(
                                    'INSERT INTO '
                                    'drseus_logging_simics_register_diff '
                                    '(injection_id,monitored_checkpoint_number,'
                                    'config_object,register,gold_value,'
                                    'monitored_value) VALUES (?,?,?,?,?,?)', (
                                        injection_number,
                                        monitored_checkpoint_number, target_key,
                                        register+':'+str(index1),
                                        gold_registers[target_key]
                                                      [register][index1],
                                        monitored_registers[target_key]
                                                           [register][index1]
                                    )
                                )
                    elif len(register_count) == 2:
                        for index1 in xrange(register_count[0]):
                            for index2 in xrange(register_count[1]):
                                if (monitored_registers[target_key][register]
                                                       [index1][index2] !=
                                    gold_registers[target_key][register]
                                                  [index1][index2]):
                                    sql.execute(
                                        'INSERT INTO '
                                        'drseus_logging_simics_register_diff '
                                        '(injection_id,'
                                        'monitored_checkpoint_number,'
                                        'config_object,register,gold_value,'
                                        'monitored_value) VALUES (?,?,?,?,?,?)',
                                        (
                                            injection_number,
                                            monitored_checkpoint_number,
                                            target_key, register+':' +
                                            str(index1)+':'+str(index2),
                                            gold_registers[target_key][register]
                                                          [index1][index2],
                                            monitored_registers[target_key]
                                                               [register]
                                                               [index1][index2]
                                        )
                                    )
                    else:
                        raise Exception('checkpoint_comparison.py:'
                                        'compare_registers(): '
                                        'Too many dimensions for register ' +
                                        register+' in target: '+target)
    sql_db.commit()
    sql_db.close()
