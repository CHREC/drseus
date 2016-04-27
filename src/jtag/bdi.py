from time import sleep

from ..error import DrSEUsError
from . import jtag


class bdi(jtag):
    error_messages = ['syntax error in command',
                      'timeout while waiting for halt',
                      'wrong state for requested command', 'read access failed']

    def __init__(self, database, options):
        self.prompts = ['P2020>']
        self.port = 23
        super().__init__(database, options)
        self.set_targets()
        self.open()

    def __str__(self):
        string = 'BDI3000 at {} port {}'.format(
            self.options.debugger_ip_address, self.port)
        return string

    def set_targets(self):
        super().set_targets('p2020')

    def close(self):
        self.telnet.write(bytes('quit\r', encoding='utf-8'))
        super().close()

    def reset_bdi(self):
        event = self.db.log_event(
            'Warning', 'Debugger', 'Reset BDI',  success=False)
        self.telnet.write(bytes('boot\r\n', encoding='utf-8'))
        self.telnet.close()
        if self.db.result is None:
            self.db.campaign.debugger_output += 'boot\n'
        else:
            self.db.result.debugger_output += 'boot\n'
        sleep(1)
        self.connect_telnet()
        sleep(1)
        self.command(None, error_message='', log_event=False)
        event.success = True
        event.save()

    def reset_dut(self, attempts=5):
        expected_output = [
            '- TARGET: processing user reset request',
            '- BDI asserts HRESET',
            '- Reset JTAG controller passed',
            '- JTAG exists check passed',
            '- BDI removes HRESET',
            '- TARGET: resetting target passed',
            '- TARGET: processing target startup \.\.\.\.',
            '- TARGET: processing target startup passed']
        try:
            super().reset_dut(expected_output, 1)
        except DrSEUsError:
            self.reset_bdi()
            super().reset_dut(expected_output, max(attempts-1, 1))

    def halt_dut(self):
        super().halt_dut('halt 0 1', [
            '- TARGET: core #0 has entered debug mode',
            '- TARGET: core #1 has entered debug mode'])

    def continue_dut(self):
        super().continue_dut('go 0 1')

    def select_core(self, core):
        self.command('select {}'.format(core), ['Target CPU', 'Core state'],
                     'Error selecting core')

    def get_mode(self):
        msr = int(self.command(
            'rd msr', [':'], 'Error getting register value'
        ).split('\r')[0].split(':')[1].split()[0], base=16)
        supervisor = not bool(msr & (1 << 14))
        return 'supervisor' if supervisor else 'user'

    def set_mode(self, mode='supervisor'):
        msr = list(bin(int(self.command(
            'rd msr', [':'], 'Error getting register value'
        ).split('\r')[0].split(':')[1].split()[0], base=16)))
        if mode == 'supervisor':
            msr[-15] = '0'
        else:
            msr[-15] = '1'
        msr = hex(int(''.join(msr), base=2))
        self.command('rm msr {}'.format(msr),
                     error_message='Error setting register value')
        self.db.log_event(
            'Information', 'Debugger', 'Set processor mode', mode, success=True)

    def command(self, command, expected_output=[], error_message=None,
                log_event=True):
        return super().command(command, expected_output, error_message,
                               log_event, '\r\n', False)

    def get_register_value(self, register_info):
        target = self.targets[register_info.target]
        if register_info.target_index is None:
            target_index = 0
        else:
            target_index = register_info.target_index
        if register_info.register_alias is None:
            register_name = register_info.register
        else:
            register_name = register_info.register_alias
        register = target['registers'][register_info.register]
        if 'type' in target and target['type'] == 'memory_mapped':
            command = 'md'
            if 'bits' in register:
                bits = register['bits']
                if bits == 8:
                    command = 'mdb'
                elif bits == 16:
                    command = 'mdh'
                elif bits == 64:
                    command = 'mdd'
            address = target['base'][target_index] + register['offset']
            buff = self.command('{} {:#x} 1'.format(command, address),
                                [':'], 'Error getting register value')
        elif 'SPR' in register:
            buff = self.command('rdspr {}'.format(register['SPR']), [':'],
                                'Error getting register value')
        elif 'PMR' in register:
            buff = self.command('rdpmr {}'.format(register['PMR']), [':'],
                                'Error getting register value')
        else:
            buff = self.command('rd {}'.format(register_name), [':'],
                                'Error getting register value')
        return buff.split('\r')[0].split(':')[1].split()[0]

    def set_register_value(self, register_info):
        target = self.targets[register_info.target]
        if register_info.target_index is None:
            target_index = 0
        else:
            target_index = register_info.target_index
        if register_info.register_alias is None:
            register_name = register_info.register
        else:
            register_name = register_info.register_alias
        register = target['registers'][register_info.register]
        value = register_info.injected_value
        if 'type' in target and target['type'] == 'memory_mapped':
            command = 'mm'
            if 'bits' in register:
                bits = register['bits']
                if bits == 8:
                    command = 'mmb'
                elif bits == 16:
                    command = 'mmh'
                elif bits == 64:
                    command = 'mmd'
            address = target['base'][target_index] + register['offset']
            self.command('{} {:#x} {} 1'.format(command, address, value),
                         error_message='Error getting register value')
        elif 'SPR' in register:
            self.command('rmspr {} {}'.format(register['SPR'], value),
                         error_message='Error setting register value')
        elif 'PMR' in register:
            self.command('rmpmr {} {}'.format(register['PMR'], value),
                         error_message='Error setting register value')
        else:
            self.command('rm {} {}'.format(register_name, value),
                         error_message='Error setting register value')
