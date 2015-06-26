import random
import os
import shutil
import sqlite3


def flip_bit(value_to_inject, num_bits_to_inject, bit_to_inject):
    """
    Flip the bit_to_inject of the binary representation of value_to_inject and
    return the new value.
    """
    if bit_to_inject >= num_bits_to_inject or bit_to_inject < 0:
        raise Exception('checkpoint_injection.py:flip_bit():' +
                        ' invalid bit_to_inject: '+str(bit_to_inject) +
                        ' for num_bits_to_inject: '+str(num_bits_to_inject))
    value_to_inject = int(value_to_inject, base=0)
    binary_list = list(str(bin(value_to_inject))[2:].zfill(num_bits_to_inject))
    binary_list[num_bits_to_inject-1-bit_to_inject] = (
        '1' if binary_list[num_bits_to_inject-1-bit_to_inject] == '0' else '0')
    injected_value = int(''.join(binary_list), 2)
    injected_value = hex(injected_value).rstrip('L')
    return injected_value


def choose_target(selected_targets, targets):
    """
    Given a list of targets, randomly choose one and return it.
    If no list of targets is given, choose from all available targets.
    Random selection takes into account the number of bits each target contains.
    """
    target_to_inject = None
    target_list = []
    total_bits = 0
    for target in targets:
        if selected_targets is None or target in selected_targets:
            bits = targets[target]['total_bits']
            target_list.append((target, bits))
            total_bits += bits
    random_bit = random.randrange(total_bits)
    bit_sum = 0
    for target in target_list:
        bit_sum += target[1]
        if random_bit < bit_sum:
            target_to_inject = target[0]
            break
    else:
        raise Exception('checkpoint_injection.py:choose_target(): ' +
                        'Error choosing injection target')
    if 'count' in targets[target_to_inject]:
        target_index = random.randrange(targets[target_to_inject]['count'])
        target_to_inject += ':'+str(target_index)
    return target_to_inject


def choose_register(target, targets):
    """
    Randomly choose a register from the target and return it.
    Random selection takes into account the number of bits each register
    contains.
    """
    if ':' in target:
        target = target.split(':')[0]
    registers = targets[target]['registers']
    register_to_inject = None
    register_list = []
    total_bits = 0
    for register in registers:
        bits = registers[register]['total_bits']
        register_list.append((register, bits))
        total_bits += bits
    random_bit = random.randrange(total_bits)
    bit_sum = 0
    for register in register_list:
        bit_sum += register[1]
        if random_bit < bit_sum:
            register_to_inject = register[0]
            break
    else:
        raise Exception('checkpoint_injection.py:choose_register(): ' +
                        'Error choosing register for target: '+target)
    return register_to_inject


def inject_register(gold_checkpoint, injected_checkpoint, register, target,
                    board, targets, previous_injection_data=None):
    """
    Creates config file for injected_checkpoint with an injected value for the
    register of the target in the gold_checkpoint and return the injection
    information.
    """
    if previous_injection_data is None:
        # create injection_data
        injection_data = {}
        injection_data['register'] = register
        if ':' in target:
            target_index = target.split(':')[1]
            target = target.split(':')[0]
            config_object = ('DUT_'+board+targets[target]['OBJECT'] +
                             '['+target_index+']')
        else:
            target_index = 'N/A'
            config_object = 'DUT_'+board+targets[target]['OBJECT']
        injection_data['target_index'] = target_index
        config_type = targets[target]['TYPE']
        injection_data['config_type'] = config_type
        injection_data['target'] = target
        injection_data['config_object'] = config_object
        if 'count' in targets[target]['registers'][register]:
            register_index = []
            for dimension in targets[target]['registers'][register]['count']:
                register_index.append(random.randrange(dimension))
            injection_data['register_index'] = register_index
        else:
            register_index = None
            injection_data['register_index'] = 'N/A'
        # choose bit_to_inject and TLB field_to_inject
        if ('is_tlb' in targets[target]['registers'][register] and
                targets[target]['registers'][register]['is_tlb']):
            fields = targets[target]['registers'][register]['fields']
            field_to_inject = 'N/A'
            fields_list = []
            total_bits = 0
            for field in fields:
                bits = fields[field]['bits']
                fields_list.append((field, bits))
                total_bits += bits
            random_bit = random.randrange(total_bits)
            bit_sum = 0
            for field in fields_list:
                bit_sum += field[1]
                if random_bit < bit_sum:
                    field_to_inject = field[0]
                    break
            else:
                raise Exception('checkpoint_injection.py:inject_register(): ' +
                                'Error choosing TLB field to inject')
            injection_data['field'] = field_to_inject
            if ('split' in fields[field_to_inject] and
                    fields[field_to_inject]['split']):
                total_bits = (fields[field_to_inject]['bits_h'] +
                              fields[field_to_inject]['bits_l'])
                random_bit = random.randrange(total_bits)
                if random_bit < fields[field_to_inject]['bits_l']:
                    register_index[-1] = fields[field_to_inject]['index_l']
                    start_bit_index = \
                        fields[field_to_inject]['bit_indicies_l'][0]
                    end_bit_index = fields[field_to_inject]['bit_indicies_l'][1]
                else:
                    register_index[-1] = fields[field_to_inject]['index_h']
                    start_bit_index = \
                        fields[field_to_inject]['bit_indicies_h'][0]
                    end_bit_index = fields[field_to_inject]['bit_indicies_h'][1]
            else:
                register_index[-1] = fields[field_to_inject]['index']
                start_bit_index = fields[field_to_inject]['bit_indicies'][0]
                end_bit_index = fields[field_to_inject]['bit_indicies'][1]
            num_bits_to_inject = 32
            bit_to_inject = random.randrange(start_bit_index, end_bit_index+1)
        else:
            if 'bits' in targets[target]['registers'][register]:
                num_bits_to_inject = \
                    targets[target]['registers'][register]['bits']
            else:
                num_bits_to_inject = 32
            bit_to_inject = random.randrange(num_bits_to_inject)
            if 'adjustBit' in targets[target]['registers'][register]:
                bit_to_inject = (
                    targets[target]['registers'][register]
                           ['adjustBit'][bit_to_inject]
                )
            if 'actualBits' in targets[target]['registers'][register]:
                num_bits_to_inject = \
                    targets[target]['registers'][register]['actualBits']
            if 'fields' in targets[target]['registers'][register]:
                for field_name, field_bounds in (targets[target]
                                                        ['registers'][register]
                                                        ['fields'].iteritems()):
                    if bit_to_inject in xrange(field_bounds[0],
                                               field_bounds[1]+1):
                        field_to_inject = field_name
                        break
                else:
                    raise Exception('checkpoint_injection.py:' +
                                    'inject_register(): ' +
                                    'Error finding register field name')
                injection_data['field'] = field_to_inject
            else:
                injection_data['field'] = 'N/A'
        injection_data['bit'] = bit_to_inject
    else:
        # use previous injection data
        config_object = previous_injection_data['config_object']
        config_type = previous_injection_data['config_type']
        register_index = previous_injection_data['register_index']
        if register_index == 'N/A':
            register_index = None
        else:
            register_index = [int(index) for index in register_index.split(':')]
        injection_data = {}
        injected_value = previous_injection_data['injected_value']
    # perform checkpoint injection
    with open(gold_checkpoint+'/config', 'r') as gold_config, \
            open(injected_checkpoint+'/config', 'w') as injected_config:
        current_line = gold_config.readline()
        injected_config.write(current_line)
        # write out configuration data until injection target found
        while ('OBJECT '+config_object+' TYPE '+config_type+' {'
               not in current_line):
            current_line = gold_config.readline()
            injected_config.write(current_line)
            if current_line == '':
                raise Exception('checkpoint_injection.py:inject_register(): ' +
                                'Could not find '+config_object +
                                ' in '+gold_checkpoint+'/config')
        # find target register
        while '\t'+register+': ' not in current_line:
            current_line = gold_config.readline()
            if 'OBJECT' in current_line:
                raise Exception('checkpoint_injection.py:inject_register(): ' +
                                'Could not find '+register +
                                ' in '+config_object +
                                ' in '+gold_checkpoint+'/config')
            elif '\t'+register+': ' not in current_line:
                injected_config.write(current_line)
        # inject register value
        if register_index is None:
            gold_value = current_line.split(':')[1].strip()
            if previous_injection_data is None:
                injected_value = flip_bit(gold_value, num_bits_to_inject,
                                          bit_to_inject)
            injected_config.write('\t'+register+': '+injected_value+'\n')
        # parse register list
        else:
            register_buffer = current_line.strip()
            if len(register_index) == 1:
                while ')' not in current_line:
                    current_line = gold_config.readline()
                    register_buffer += current_line.strip()
                register_buffer = register_buffer.replace(' ', '')
                register_list = (
                    register_buffer[
                        register_buffer.index('(')+1:register_buffer.index(')')
                    ].split(',')
                )
                gold_value = register_list[register_index[0]]
                if previous_injection_data is None:
                    injected_value = flip_bit(gold_value, num_bits_to_inject,
                                              bit_to_inject)
                register_list[register_index[0]] = injected_value
                injected_config.write('\t'+register+': (')
                line_to_write = ''
                for index in xrange(len(register_list)):
                    if index == len(register_list)-1:
                        if line_to_write == '':
                            injected_config.write(register_list[index]+')\n')
                        else:
                            injected_config.write(line_to_write+', ' +
                                                  register_list[index]+')\n')
                    else:
                        if len(line_to_write+register_list[index]+', ') > 80:
                            injected_config.write(line_to_write+',\n\t' +
                                                  '       ')
                            line_to_write = register_list[index]
                        elif line_to_write == '':
                            line_to_write += register_list[index]
                        else:
                            line_to_write += ', '+register_list[index]
            elif len(register_index) == 2:
                while '))' not in current_line:
                    current_line = gold_config.readline()
                    register_buffer += current_line.strip()
                register_buffer = register_buffer.replace(' ', '')
                register_list = (
                    register_buffer[
                        register_buffer.index('((')+2:
                        register_buffer.index('))')
                    ].split('),(')
                )
                for register_index1 in xrange(len(register_list)):
                    register_list[register_index1] = \
                        register_list[register_index1].split(',')
                gold_value = register_list[register_index[0]][register_index[1]]
                if previous_injection_data is None:
                    injected_value = flip_bit(gold_value, num_bits_to_inject,
                                              bit_to_inject)
                register_list[register_index[0]][register_index[1]] = \
                    injected_value
                injected_config.write('\t'+register+': ((')
                for index1 in xrange(len(register_list)):
                    for index2 in xrange(len(register_list[index1])):
                        if index2 != len(register_list[index1])-1:
                            injected_config.write(
                                register_list[index1][index2]+', '
                            )
                        elif index1 != len(register_list)-1:
                            injected_config.write(
                                register_list[index1][index2]+'),\n\t       ('
                            )
                        else:
                            injected_config.write(
                                register_list[index1][index2]+'))\n'
                            )
            elif len(register_index) == 3:
                while ')))' not in current_line:
                    current_line = gold_config.readline()
                    register_buffer += current_line.strip()
                register_buffer = register_buffer.replace(' ', '')
                register_list = (
                    register_buffer[
                        register_buffer.index('(((')+3:
                        register_buffer.index(')))')
                    ].split(')),((')
                )
                for index1 in xrange(len(register_list)):
                    register_list[index1] = register_list[index1].split('),(')
                    for index2 in xrange(len(register_list[index1])):
                        register_list[index1][index2] = \
                            register_list[index1][index2].split(',')
                gold_value = (
                    register_list[register_index[0]]
                                 [register_index[1]]
                                 [register_index[2]]
                )
                if previous_injection_data is None:
                    injected_value = flip_bit(gold_value, num_bits_to_inject,
                                              bit_to_inject)
                (
                    register_list[register_index[0]]
                                 [register_index[1]]
                                 [register_index[2]]
                ) = injected_value
                injected_config.write('\t'+register+': (((')
                for index1 in xrange(len(register_list)):
                    for index2 in xrange(len(register_list[index1])):
                        for index3 in \
                                xrange(len(register_list[index1][index2])):
                            if index3 != len(register_list[index1][index2])-1:
                                injected_config.write(
                                    register_list[index1][index2][index3]+', '
                                )
                            elif index2 != len(register_list[index1])-1:
                                injected_config.write(
                                    register_list[index1][index2][index3] +
                                    '),\n\t        ('
                                )
                            elif index1 != len(register_list)-1:
                                injected_config.write(
                                    register_list[index1][index2][index3] +
                                    ')),\n\t       (('
                                )
                            else:
                                injected_config.write(
                                    register_list[index1][index2][index3] +
                                    ')))\n'
                                )
            else:
                raise Exception('checkpoint_injection.py:inject_register(): ' +
                                'Too many dimensions for register '+register +
                                ' in target: '+target)
        injection_data['gold_value'] = gold_value
        injection_data['injected_value'] = injected_value
        # write out remaining configuration data
        while current_line != '':
            current_line = gold_config.readline()
            injected_config.write(current_line)
    return injection_data


def inject_checkpoint(injection_number, board, selected_targets,
                      num_checkpoints):
    """
    Create a new injected checkpoint (only performing injection on the
    selected_targets if provided) and return the path of the injected
    checkpoint.
    """
    if board == 'p2020rdb':
        from simics_targets import P2020 as targets
    elif board == 'a9x4':
        from simics_targets import A9 as targets
    # verify selected targets exist
    if selected_targets is not None:
        for target in selected_targets:
            if target not in targets:
                raise Exception('checkpoint_injection.py:inject_checkpoint():' +
                                ' invalid injection target: '+target)
    # choose a checkpoint for injection
    checkpoint_list = os.listdir('simics-workspace/gold-checkpoints')
    for checkpoint in checkpoint_list:
        if '.ckpt' not in checkpoint:
            checkpoint_list.remove(checkpoint)
    checkpoint_list.remove('checkpoint-'+str(num_checkpoints-1)+'.ckpt')
    gold_checkpoint = ('simics-workspace/gold-checkpoints/' +
                       checkpoint_list[random.randrange(len(checkpoint_list))])
    # create injected checkpoint directory
    if not(os.path.exists('simics-workspace/injected-checkpoints')):
        os.mkdir('simics-workspace/injected-checkpoints')
    checkpoint_number = int(
        gold_checkpoint.split('/')[-1][
            gold_checkpoint.split('/')[-1].index('-')+1:
            gold_checkpoint.split('/')[-1].index('.ckpt')
        ]
    )
    injected_checkpoint = ('simics-workspace/injected-checkpoints/' +
                           str(injection_number)+'_'+'checkpoint-' +
                           str(checkpoint_number)+'.ckpt')
    os.mkdir(injected_checkpoint)
    # copy gold checkpoint files
    checkpoint_files = os.listdir(gold_checkpoint)
    checkpoint_files.remove('config')
    # checkpoint_files.remove('DebugInfo.txt')
    for checkpointFile in checkpoint_files:
        shutil.copyfile(gold_checkpoint+'/'+checkpointFile,
                        injected_checkpoint+'/'+checkpointFile)
    # choose injection target
    target = choose_target(selected_targets, targets)
    register = choose_register(target, targets)
    # perform fault injection
    injection_data = inject_register(gold_checkpoint, injected_checkpoint,
                                     register, target, board, targets)
    # log injection data
    injection_data['injection_number'] = injection_number
    injection_data['checkpoint_number'] = checkpoint_number
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
    sql = sql_db.cursor()
    register_index = ''
    for index in injection_data['register_index']:
        register_index += str(index).zfill(2)+':'
    register_index = register_index[:-1]
    sql.execute(
        'INSERT INTO drseus_logging_simics_injection ' +
        '(injection_number,register,bit,gold_value,injected_value,' +
        'checkpoint_number,target_index,target,config_object,config_type,' +
        'register_index,field) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
        (
            injection_data['injection_number'], injection_data['register'],
            injection_data['bit'], injection_data['gold_value'],
            injection_data['injected_value'],
            injection_data['checkpoint_number'], injection_data['target_index'],
            injection_data['target'], injection_data['config_object'],
            injection_data['config_type'], register_index,
            injection_data['field']
        )
    )
    sql_db.commit()
    sql_db.close()
    return injected_checkpoint.replace('simics-workspace/', '')


def regenerate_injected_checkpoint(board, injection_data):
    """
    Regenerate a previously created injected checkpoint using injection_data.
    """
    gold_checkpoint = ('simics-workspace/gold-checkpoints/checkpoint-' +
                       str(injection_data['checkpoint_number'])+'.ckpt')
    # create temporary directory
    if not(os.path.exists('simics-workspace/temp')):
        os.mkdir('simics-workspace/temp')
    injected_checkpoint = ('simics-workspace/temp/' +
                           str(injection_data['injection_number'])+'_' +
                           'checkpoint-' +
                           str(injection_data['checkpoint_number'])+'.ckpt')
    os.mkdir(injected_checkpoint)
    # copy gold checkpoint files
    checkpoint_files = os.listdir(gold_checkpoint)
    checkpoint_files.remove('config')
    for checkpointFile in checkpoint_files:
        shutil.copyfile(gold_checkpoint+'/'+checkpointFile,
                        injected_checkpoint+'/'+checkpointFile)
    # perform fault injection
    if board == 'p2020rdb':
        from simics_targets import P2020 as targets
    elif board == 'a9x4':
        from simics_targets import A9 as targets
    inject_register(gold_checkpoint, injected_checkpoint,
                    injection_data['register'], injection_data['target'],
                    board, targets, injection_data)
    return injected_checkpoint.replace('simics-workspace/', '')
