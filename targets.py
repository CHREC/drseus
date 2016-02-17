from random import randrange


def calculate_target_bits(devices):
    for device in devices:
        for target in devices[device]:
            # count bits for each target
            total_bits = 0
            for register in devices[device][target]['registers']:
                if 'bits' in devices[device][target]['registers'][register]:
                    bits = (devices[device][target]['registers'][register]
                                   ['bits'])
                else:
                    bits = 32
                if 'count' in devices[device][target]['registers'][register]:
                    count = 1
                    if 'is_tlb' in \
                        devices[device][target]['registers'][register] \
                        and (devices[device][target]['registers'][register]
                                    ['is_tlb']):
                        dimensions = (devices[device][target]['registers']
                                             [register]['count'][:-1])
                    else:
                        dimensions = (devices[device][target]['registers']
                                             [register]['count'])
                    for dimension in dimensions:
                        count *= dimension
                else:
                    count = 1
                (devices[device][target]['registers']
                        [register]['total_bits']) = count * bits
                total_bits += count * bits
                # if a register is partially implemented generate an adjust_bit
                # mapping list to ensure an unimplemented field is not injected
                if 'partial' in devices[device][target]['registers'][register] \
                    and (devices[device][target]['registers'][register]
                                ['partial']):
                    adjust_bit = []
                    for field, field_range in (devices[device][target]
                                                      ['registers'][register]
                                                      ['fields'].items()):
                        adjust_bit.extend(range(field_range[0],
                                                field_range[1]+1))
                    if len(adjust_bit) != bits:
                        raise Exception('Bits mismatch for register: ' +
                                        register+' in target: '+target +
                                        ' in device: '+device)
                    else:
                        (devices[device][target]['registers'][register]
                                ['adjust_bit']) = sorted(adjust_bit)
            devices[device][target]['total_bits'] = total_bits


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
    random_bit = randrange(total_bits)
    bit_sum = 0
    for target in target_list:
        bit_sum += target[1]
        if random_bit < bit_sum:
            target_to_inject = target[0]
            break
    else:
        raise Exception('Error choosing injection target')
    if 'count' in targets[target_to_inject]:
        target_index = randrange(targets[target_to_inject]['count'])
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
    random_bit = randrange(total_bits)
    bit_sum = 0
    for register in register_list:
        bit_sum += register[1]
        if random_bit < bit_sum:
            register_to_inject = register[0]
            break
    else:
        raise Exception('Error choosing register for target: '+target)
    return register_to_inject
