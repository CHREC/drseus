#!python/bin/python3

# TODO: add key verification

from collections import defaultdict
from copy import deepcopy
from importlib import import_module
from os.path import abspath, dirname
from sys import path

path.append(dirname(dirname(abspath(__file__))))
targets = import_module('src.targets')
load_targets = targets.load_targets
save_targets = targets.save_targets


def tree():
    return defaultdict(tree)


missing_total = 0
for device in ['a9', 'p2020']:
    jtag_targets = load_targets(device, 'jtag')
    simics_targets = load_targets(device, 'simics')

    merged_targets = tree()

    for old_type in ['simics', 'jtag']:  # do simics first because of preprocess
        print('\nerrors for', device, old_type)

        if old_type == 'jtag':
            old_targets = jtag_targets
            other_type = 'simics'
            other_targets = simics_targets
        elif old_type == 'simics':
            old_targets = simics_targets
            other_type = 'jtag'
            other_targets = jtag_targets
        else:
            raise Exception('unrecognized old_type')
        for target in sorted(old_targets.keys()):
            if 'unused_targets' not in merged_targets[other_type]:
                merged_targets[other_type]['unused_targets'] = []
            old_target = old_targets[target]
            merged_target = merged_targets['targets'][target]

            if target == 'TLB':
                merged_target['type'] = 'tlb'

            if target not in other_targets:
                other_target = None
                merged_targets[other_type]['unused_targets'].append(target)
                # print('target in '+old_type+' but not '+other_type+':',
                #       target)
            else:
                other_target = other_targets[target]

            for key in [key for key in old_target.keys()
                        if key not in ['registers', 'unused_registers']]:
                if key == 'base':
                    merged_target[key] = old_target[key]
                elif key == 'count':
                    if old_target[key] != 1:
                        merged_target[key] = old_target[key]
                elif key in ['CP', 'memory_mapped']:
                    if not old_target[key]:
                        print('unexpected value for :', target+'['+key+']:',
                              old_target[key])
                    merged_target['type'] = key
                elif key == 'OBJECT':
                    merged_targets[old_type]['targets'][target]['object'] = \
                        old_target['OBJECT']
                elif key == 'limitations':
                    merged_targets[old_type]['targets'][target][key] = \
                        old_target[key]
                else:
                    print('* key:', key, 'in target:', target)

            if old_type == 'simics':
                registers = list(old_target['registers'].keys())
                if 'unused_registers' in old_target:
                    unused_registers = list(
                        old_target['unused_registers'].keys())
                else:
                    unused_registers = []
                for register in registers + unused_registers:
                    unused_register = register in unused_registers
                    if unused_register:
                        old_register = old_target['unused_registers'][register]
                    else:
                        old_register = old_target['registers'][register]

                    if 'count' in old_register:
                        count = old_register['count']
                    else:
                        count = []

                    if register == 'fpgprs':
                        for i in range(old_register['count'][0]):
                            old_target['registers']['fpr'+str(i)] = {'alias': {
                                'register': register, 'register_index': [i]}}
                        del old_target['registers'][register]
                        continue

                    if other_target is not None and \
                            register not in other_target['registers']:
                        matches = []
                        for other_register in other_target['registers']:
                            if count:
                                if other_register.startswith(register):
                                    try:
                                        try:
                                            index = int(
                                                other_register.replace(
                                                    register+'_', ''))
                                        except:
                                            index = int(
                                                other_register.replace(
                                                    register, ''))
                                        if register == 'SRDSCR' and \
                                                index > 3:
                                            index -= 1
                                        elif register == 'DDR_SDRAM_RCW':
                                            index -= 1
                                        match = (other_register, [index])
                                        matches.append(match)
                                        # print(register, count, match)
                                        continue
                                    except:
                                        pass
                                if register == 'MSI_MSISR' and \
                                        other_register == 'MSISR':
                                    match = ('MSISR', [0])
                                    matches.append(match)
                                    # print(register, count, match)
                                if register == 'usb_regs_prtsc' and \
                                        other_register == 'PORTSC':
                                    match = ('PORTSC', [0])
                                    matches.append(match)
                                    # print(register, count, match)
                                if register == 'PM_MR' and \
                                        'MR' in other_register:
                                    try:
                                        index1 = int(other_register[2])
                                        index2 = int(other_register[5])
                                        match = (other_register,
                                                 [index1, index2])
                                        matches.append(match)
                                        # print(register, count, match)
                                        continue
                                    except:
                                        pass
                                if register == 'IADDR' and \
                                        other_register.startswith('IGADDR'):
                                    index = int(other_register.replace(
                                        'IGADDR', ''))
                                    match = (other_register, [index])
                                    matches.append(match)
                                    # print(register, count, match)
                                    continue
                                if register.startswith('MAC_ADD') and \
                                        'MAC' in other_register and \
                                        'ADDR' in other_register and \
                                        register[-1] == other_register[-1]:
                                    try:
                                        index = int(other_register[3:5])-1
                                        match = (other_register, [index])
                                        matches.append(match)
                                        # print(register, count, match)
                                        continue
                                    except:
                                        pass
                                if register == 'PEX_outbound_OTWBAR' and \
                                        other_register.startswith('PEXOWBAR'):
                                    try:
                                        index = int(
                                            other_register.replace(
                                                'PEXOWBAR', ''))
                                        match = (other_register, [index])
                                        matches.append(match)
                                        # print(register, count, match)
                                        continue
                                    except:
                                        pass
                                if len(register.split('_')) > 1:
                                    reg = register.split('_')
                                    if reg[-1][-1] == 'n':
                                        reg[-1] = reg[-1][:-1]
                                    if reg[0] == 'CS' and '_'.join(reg[1:]) == \
                                            '_'.join(
                                                other_register.split('_')[1:]):
                                        try:
                                            index = int(
                                                other_register.split(
                                                    '_')[0].replace('CS', ''))
                                            match = (other_register, [index])
                                            matches.append(match)
                                            # print(register, count, match)
                                            continue
                                        except:
                                            pass
                                    if reg[0] == 'PEX' and \
                                            other_register.startswith(
                                                'PEX'+reg[-1]):
                                        try:
                                            index = int(
                                                other_register.replace(
                                                    'PEX'+reg[-1], ''))
                                            if reg[-1] in ['IWAR', 'IWBAR',
                                                           'ITAR', 'IWBEAR']:
                                                index -= 1
                                            match = (other_register, [index])
                                            matches.append(match)
                                            # print(register, count, match)
                                            continue
                                        except:
                                            pass
                                    if reg[0] == 'MSG' and \
                                            reg[1] in ['MER', 'MSR']:
                                        if other_register.startswith(reg[1]):
                                            if other_register[-1] == 'a':
                                                index = 1
                                            else:
                                                index = 0
                                            match = (other_register, [index])
                                            matches.append(match)
                                            # print(register, count, match)
                                            continue
                                    if reg[0] == 'GT' and \
                                            reg[1] in ['TFRR', 'TCR']:
                                        if other_register.startswith(reg[1]):
                                            if other_register[-1] == 'A':
                                                index = 0
                                            elif other_register[-1] == 'B':
                                                index = 1
                                            match = (other_register, [index])
                                            matches.append(match)
                                            # print(register, count, match)
                                            continue
                                    if register == 'regs_port_' \
                                                   'port_error_and_status':
                                        reg[2] = 'ESCSR'
                                    if register == 'regs_port_port_control':
                                        reg[2] = 'CCSR'
                                    if register == 'regs_port_port_error_rate':
                                        reg[2] = 'ERCSR'
                                    if register == 'regs_port_' \
                                                   'capture_attributes':
                                        reg[2] = 'ECACSR'
                                    if register == 'regs_port_' \
                                                   'port_error_detect':
                                        reg[2] = 'EDCSR'
                                    if register == 'regs_port_' \
                                                   'port_error_rate_enable':
                                        reg[2] = 'ERECSR'
                                    if register == 'regs_port_' \
                                                   'port_error_rate_threshold':
                                        reg[2] = 'ERTCSR'
                                    if register == 'regs_port_capture_symbol':
                                        reg[2] = 'PCSECCSR0'
                                    if register == 'regs_port_' \
                                                   'port_local_ackid_status':
                                        reg[2] = 'LASCSR'
                                    if register == 'regs_port_' \
                                                   'capture_packet_1':
                                        reg[2] = 'PECCSR1'
                                    if register == 'regs_port_' \
                                                   'capture_packet_2':
                                        reg[2] = 'PECCSR2'
                                    if register == 'regs_port_' \
                                                   'capture_packet_3':
                                        reg[2] = 'PECCSR3'
                                    if register == 'regs_port_' \
                                                   'link_maintenance_request':
                                        reg[2] = 'LMREQCSR'
                                    if register == 'regs_port_' \
                                                   'link_maintenance_response':
                                        reg[2] = 'LMRESPCSR'
                                    if reg[1] == 'port' and \
                                            reg[2] in other_register and \
                                            other_register[0] == 'P':
                                        if len(count) == 1:
                                            try:
                                                index = int(other_register[1])
                                                if other_register == \
                                                        'P'+str(index)+reg[2]:
                                                    index -= 1
                                                    match = (other_register,
                                                             [index])
                                                    matches.append(match)
                                                    # print(register, count,
                                                    #       match)
                                                    continue
                                            except:
                                                pass
                                        elif len(count) == 2:
                                            try:
                                                index1 = int(other_register[1])
                                                index1 -= 1
                                                index2 = int(other_register[-1])
                                                if reg[2] in ['RIWTAR',
                                                              'ROWTAR',
                                                              'ROWTEAR',
                                                              'RIWAR',
                                                              'ROWAR',
                                                              'ROWBAR',
                                                              'RIWBAR',
                                                              'ROWS1R',
                                                              'ROWS2R',
                                                              'ROWS3R']:
                                                    if index2 == 0:
                                                        continue
                                                        print('unexpected 0 '
                                                              'index')
                                                    else:
                                                        index2 -= 1
                                                match = (other_register,
                                                         [index1, index2])
                                                matches.append(match)
                                                # print(register, count, match)
                                                continue
                                            except:
                                                pass
                                    if reg[1] == 'M':
                                        r = None
                                        if reg[2].startswith('EI'):
                                            s = 'EIM'
                                            r = reg[2][2:]
                                            i = 3
                                        elif reg[2].startswith('EO'):
                                            s = 'EOM'
                                            r = reg[2][2:]
                                            i = 3
                                        elif reg[2].startswith('I'):
                                            s = 'IM'
                                            r = reg[2][1:]
                                            i = 2
                                        elif reg[2].startswith('O'):
                                            s = 'OM'
                                            r = reg[2][1:]
                                            i = 2
                                        if r is not None and \
                                                other_register.endswith(r) and \
                                                other_register.startswith(s):
                                            try:
                                                index = int(other_register[i])
                                                match = (other_register,
                                                         [index])
                                                matches.append(match)
                                                # print(register, count, match)
                                                continue
                                            except:
                                                pass
                                    if other_register.startswith(reg[-1]):
                                        index = None
                                        try:
                                            index = int(other_register[-2:])
                                        except:
                                            try:
                                                index = int(other_register[-1])
                                            except:
                                                pass
                                        if index is not None:
                                            if len(count) == 1:
                                                if register == 'regs_SNOOP':
                                                    index -= 1
                                                match = (other_register,
                                                         [index])
                                            elif len(count) == 2:
                                                if count[0] == 1:
                                                    match = (other_register,
                                                             [0, index])
                                                elif other_register[-2] == 'a':
                                                    match = (other_register,
                                                             [1,
                                                              index % count[1]])
                                                elif other_register[-2] == 'A':
                                                    match = (other_register,
                                                             [0, index])
                                                elif other_register[-2] == 'B':
                                                    match = (other_register,
                                                             [1, index])
                                                elif register == \
                                                    'P_IPIDR' and \
                                                    other_register.endswith(
                                                        'CPU' +
                                                        str(index).zfill(2)):
                                                    if index >= 10:
                                                        index1 = 2
                                                    else:
                                                        index1 = 1
                                                    match = (
                                                        other_register,
                                                        [index1,
                                                         index % 10])
                                                else:
                                                    match = (other_register,
                                                             [int(index /
                                                                  count[1]),
                                                              index % count[1]])
                                            matches.append(match)
                                            # print(register, count, match)
                                            continue
                            else:
                                if other_register == register.upper():
                                    match = (register.upper(), None)
                                    matches.append(match)
                                    # print(register, count, match)
                                    break
                                if len(register.split('_')) > 1:
                                    reg = register.split('_')
                                    if register == 'regs_layer_error_detect':
                                        reg[-1] = 'LTLEDCSR'
                                    if register == 'regs_layer_error_enable':
                                        reg[-1] = 'LTLEECSR'
                                    if register == 'regs_src_operations':
                                        reg[-1] = 'SOCAR'
                                    if register == 'regs_pe_ll_status':
                                        reg[-1] = 'PELLCCSR'
                                    if register == 'regs_pe_features':
                                        reg[-1] = 'PEFCAR'
                                    if register == 'regs_DMIRIR':
                                        reg[-1] = 'IDMIRIR'
                                    if register == 'regs_error_block_header':
                                        reg[-1] = 'ERBH'
                                    if register == 'regs_dst_operations':
                                        reg[-1] = 'DOCAR'
                                    if register == 'regs_assembly_id':
                                        reg[-1] = 'AIDCAR'
                                    if register == 'regs_assembly_info':
                                        reg[-1] = 'AICAR'
                                    if register == 'regs_port_link_timeout':
                                        reg[-1] = 'PLTOCCSR'
                                    if register == 'regs_base_device_id':
                                        reg[-1] = 'BDIDCSR'
                                    if register == 'regs_component_tag':
                                        reg[-1] = 'CTCSR'
                                    if register == 'regs_device_info':
                                        reg[-1] = 'DICAR'
                                    if register == 'regs_device_id':
                                        reg[-1] = 'DIDCAR'
                                    if register == 'regs_port_block_header':
                                        reg[-1] = 'PMBH0'
                                    if register == 'regs_host_base_device_id':
                                        reg[-1] = 'HBDIDLCSR'
                                    if register == 'regs_port_general_control':
                                        reg[-1] = 'PGCCSR'
                                    if register == 'regs_ODRS':
                                        reg[-1] = 'ODSR'
                                    if register == 'regs_base1_status':
                                        reg[-1] = 'LCSBA1CSR'
                                    if register == 'regs_write_port_status':
                                        reg[-1] = 'PWDCSR'
                                    if register == 'regs_layer_capture_address':
                                        reg[-1] = 'LTLACCSR'
                                    if register == 'regs_layer_capture_control':
                                        reg[-1] = 'LTLCCCSR'
                                    if register == \
                                            'regs_layer_capture_device_id':
                                        reg[-1] = 'LTLDIDCCSR'
                                    if register == '':
                                        reg[-1] = ''
                                    if register == '':
                                        reg[-1] = ''
                                    if other_register == reg[-1]:
                                        match = (reg[-1], None)
                                        matches.append(match)
                                        # print(register, count, match)
                                        break
                                    if reg[0] == 'regs' and other_register == \
                                            '_'.join(reg[1:]):
                                        match = (other_register, None)
                                        matches.append(match)
                                        # print(register, count, match)
                                        break
                                    if other_register == reg[-1].upper():
                                        match = (reg[-1].upper(), None)
                                        matches.append(match)
                                        # print(register, count, match)
                                        break
                                    if other_register == 'I'+reg[-1]:
                                        match = ('I'+reg[-1], None)
                                        matches.append(match)
                                        # print(register, count, match)
                                        break
                                    if reg[-1].startswith('E') and \
                                            other_register.startswith('E') and \
                                            other_register == 'EI'+reg[-1][1:]:
                                        match = ('EI'+reg[-1][1:], None)
                                        matches.append(match)
                                        # print(register, count, match)
                                        break
                                    if reg[-1] == 'ADDRESS' and \
                                        other_register == \
                                            register.replace('ADDRESS',
                                                             'ADDR'):
                                        match = (register.replace('ADDRESS',
                                                                  'ADDR'),
                                                 None)
                                        matches.append(match)
                                        # print(register, count, match)
                                        break
                                if register == 'DDR_SDRAM_INIT':
                                    match = ('DDR_DATA_INIT', None)
                                    matches.append(match)
                                    # print(register, count, match)
                                    break
                                if register == 'ECMIP_REV1':
                                    match = ('EIPBRR1', None)
                                    matches.append(match)
                                    # print(register, count, match)
                                    break
                                if register == 'ECMIP_REV2':
                                    match = ('EIPBRR2', None)
                                    matches.append(match)
                                    # print(register, count, match)
                                    break
                                if register == 'IOVSELCR':
                                    match = ('IOVSELSR', None)
                                    matches.append(match)
                                    # print(register, count, match)
                                    break

                        if matches:
                            matches.sort(key=lambda x: x[0])
                            correct = True
                            if len(count) > 0:
                                counts0 = [match[1][0] for match in matches
                                           if len(match[1]) == 1 or
                                           (len(match[1]) == 2 and
                                            match[1][1] == 0)]
                                missing = []
                                extra = []
                                for i in range(count[0]):
                                    if i not in counts0:
                                        correct = False
                                        missing.append([i])
                                    else:
                                        counts0.remove(i)
                                    if len(count) == 2:
                                        counts1 = [match[1][1]
                                                   for match in matches
                                                   if match[1][0] == i]
                                        for j in range(count[1]):
                                            if j not in counts1:
                                                correct = False
                                                missing.append([i, j])
                                            else:
                                                counts1.remove(j)
                                        if counts1:
                                            extra.append([i, counts1])
                                            correct = False
                                if counts0:
                                    extra.extend(counts0)
                                    correct = False
                            elif len(matches) > 1:
                                correct = False
                            if correct or register in [
                                    'PEX_inbound_IWBEAR',
                                    'PEX_outbound_OTWBAR',
                                    'P_CTPR',
                                    'regs_ENDPTCTRL',
                                    'P_IPIDR']:
                                # print('matches:', register, count,
                                #       matches)
                                if 'count' in old_register:
                                    del old_register['count']
                                if len(list(old_register.keys())) > 0:
                                    new_register = deepcopy(old_register)
                                else:
                                    new_register = tree()
                                if unused_register:
                                    del (old_target['unused_registers']
                                                   [register])
                                else:
                                    del old_target['registers'][register]
                                for match in matches:
                                    temp_register = deepcopy(new_register)
                                    temp_register['alias'] = {
                                        'register': register}
                                    if match[1] is not None:
                                        (temp_register['alias']
                                                      ['register_index']) = \
                                            match[1]
                                    if unused_register:
                                        (old_target['unused_registers']
                                                   [match[0]]) = \
                                            temp_register
                                    else:
                                        (old_target['registers']
                                                   [match[0]]) = \
                                            temp_register
                            else:
                                print('\n\nincorrect match for',
                                      register, count)
                                print(matches)
                                if missing:
                                    print('missing', missing)
                                if extra:
                                    print('extra', extra)
                                print('\n\n')
            else:
                if target in ['CPU', 'TLB', 'GPR'] or \
                        ('CP' in old_target and old_target['CP']):
                    merged_targets['targets'][target]['core'] = True

            missing = []
            registers = list(old_target['registers'].keys())
            if 'unused_registers' in old_target:
                unused_registers = list(old_target['unused_registers'].keys())
            else:
                unused_registers = []
            for register in registers + unused_registers:
                unused_register = register in unused_registers
                if unused_register:
                    old_register = old_target['unused_registers'][register]
                else:
                    old_register = old_target['registers'][register]

                other_register = None
                if other_target is not None:
                    if register in other_target['registers']:
                        other_register = other_target['registers'][register]
                    elif 'unused_registers' in other_target and \
                            register in other_target['unused_registers']:
                        other_register = \
                            other_target['unused_registers'][register]

                merged_register = merged_target['registers'][register]
                if unused_register:
                    (merged_targets[old_type]
                                   ['targets'][target]
                                   ['unused_registers'][register])
                    if other_target is not None and other_register is None:
                        (merged_targets[other_type]
                                       ['targets'][target]
                                       ['unused_registers'][register])
                        missing.append(register)
                        missing_total += 1
                elif other_target is not None and other_register is None:
                    (merged_targets[other_type]
                                   ['targets'][target]
                                   ['unused_registers'][register])
                    missing.append(register)
                    missing_total += 1

                for key in [key for key in old_register.keys()
                            if key not in ['fields', 'unused_fields']]:
                    if key in ['access', 'CP', 'CRm', 'CRn', 'Op1', 'Op2',
                               'PMR', 'SPR', 'offset', 'limitations']:
                        merged_register[key] = old_register[key]
                    elif key == 'alias':
                        if unused_register:
                            (merged_targets[old_type]
                                           ['targets'][target]
                                           ['unused_registers'][register]
                                           [key]) = old_register[key]
                        else:
                            (merged_targets[old_type]
                                           ['targets'][target]
                                           ['registers'][register]
                                           [key]) = old_register[key]
                    elif key == 'actual_bits':
                        if old_register[key] != 32:
                            merged_register['bits'] = old_register[key]
                    elif key == 'bits':
                        if 'actual_bits' not in old_register:
                            merged_register[key] = old_register[key]
                    elif key == 'partial':
                        if 'unused_fields' not in old_register:
                            print('* partial register:', register,
                                  'in target:', target)
                    elif key == 'count' and old_type == 'simics' and \
                            other_register is None:
                        merged_register[key] = old_register[key]
                    elif key == 'is_tlb':
                        pass
                    else:
                        print('* key:', key, 'value:', old_register[key],
                              'in register:', register, 'in target:', target)

                if 'fields' in old_register:
                    if old_type == 'jtag' or target == 'TLB' or \
                            other_register is None:
                        merged_register['fields'] = old_register['fields']
                        if 'unused_fields' in old_register:
                            merged_register['fields'].extend(
                                old_register['unused_fields'])
                    elif other_register is not None and \
                            'fields' in other_register:
                        other_fields = other_register['fields']
                        other_fields.sort(key=lambda x: x[1][1],
                                          reverse=True)
                        fields = old_register['fields']
                        if 'unused_fields' in old_register:
                            fields.extend(old_register['unused_fields'])
                        fields.sort(key=lambda x: x[1][1], reverse=True)
                        for i in range(len(fields)):
                            if fields[i][0] != other_fields[i][0]:
                                print('field name mismatch',
                                      target, register,
                                      fields[i][0], other_fields[i][0])
                            elif fields[i][1][0] != \
                                    other_fields[i][1][0] or \
                                    fields[i][1][1] != \
                                    other_fields[i][1][1]:
                                print('field range mismatch',
                                      target, register, fields[i][0])

                if 'unused_fields' in old_register:
                    if 'actual_bits' not in old_register:
                        print('* unused_fields found, but missing actual_bits',
                              register)
                    if 'partial' not in old_register:
                        print('* unused_fields found, but missing partial',
                              register)
                    if 'unused_fields' not in (
                            merged_targets[old_type]
                                          ['targets'][target]
                                          ['registers'][register]):
                        (merged_targets[old_type]
                                       ['targets'][target]
                                       ['registers'][register]
                                       ['unused_fields']) = []
                    unused_fields = (merged_targets[old_type]
                                                   ['targets'][target]
                                                   ['registers'][register]
                                                   ['unused_fields'])
                    for field in old_register['unused_fields']:
                        if field[0] in unused_fields:
                            print('* duplicate field', register, field[0])
                        unused_fields.append(field[0])
                    unused_fields.sort()

                if 'fields' in merged_register and target != 'TLB':
                    merged_register['fields'].sort(key=lambda x: x[1][0],
                                                   reverse=True)
                    if 'bits' in merged_register:
                        bits = merged_register['bits']
                    else:
                        bits = 32
                    for field in merged_register['fields']:
                        bits -= (field[1][1] - field[1][0]) + 1
                    if bits != 0:
                        print('* bit count error:', register,
                              merged_register['fields'])

            if missing:
                print('*', target, 'registers in', old_type,
                      'but not', other_type+':', ', '.join(sorted(missing)))

        if 'unused_targets' in merged_targets[other_type]:
            if merged_targets[other_type]['unused_targets']:
                merged_targets[other_type]['unused_targets'].sort()
            else:
                del merged_targets[other_type]['unused_targets']

    save_targets('', device, merged_targets)

print('\ntotal missing registers:', missing_total)

for device in ['a9', 'p2020']:
    merged_targets = load_targets('', device)
    for type_ in 'jtag', 'simics':
        for target in list(merged_targets[type_]['targets'].keys()):
            if not merged_targets[type_]['targets'][target]:
                del merged_targets[type_]['targets'][target]
            else:
                if 'unused_registers' in \
                        merged_targets[type_]['targets'][target] and \
                        not (merged_targets[type_]
                                           ['targets'][target]
                                           ['unused_registers']):
                    del (merged_targets[type_]
                                       ['targets'][target]
                                       ['unused_registers'])
    if device == 'p2020':
        merged_targets['jtag']['unused_targets'].append('RAPIDIO')
        merged_targets['jtag']['unused_targets'].sort()
    reg_count = 0
    for target in list(merged_targets['targets'].keys()):
        reg_count += len(list(
            merged_targets['targets'][target]['registers'].keys()))
    print(device, 'register count:', reg_count)
    save_targets('', device, merged_targets)
