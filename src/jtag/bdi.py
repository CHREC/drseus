from time import sleep

from ..error import DrSEUsError
from ..targets import get_targets
from . import jtag


class bdi(jtag):
    error_messages = ['syntax error in command',
                      'timeout while waiting for halt',
                      'wrong state for requested command', 'read access failed']

    def __init__(self, database, options):
        self.prompts = ['P2020>']
        if options.command == 'inject':
            self.targets = get_targets('p2020', 'jtag',
                                       options.selected_targets,
                                       options.selected_registers)
        self.port = 23
        super().__init__(database, options)
        self.open()

    def __str__(self):
        string = ('BDI3000 at '+self.options.debugger_ip_address +
                  ' port '+str(self.port))
        return string

    def close(self):
        self.telnet.write(bytes('quit\r', encoding='utf-8'))
        super().close()

    def reset_bdi(self):
        with self.db as db:
            event = db.log_event('Warning', 'Debugger', 'Reset BDI',
                                 success=False)
        self.telnet.write(bytes('boot\r\n', encoding='utf-8'))
        self.telnet.close()
        if self.db.result:
            self.db.result['debugger_output'] += 'boot\n'
        else:
            self.db.campaign['debugger_output'] += 'boot\n'
        sleep(1)
        self.connect_telnet()
        sleep(1)
        self.command(None, error_message='', log_event=False)
        with self.db as db:
            db.log_event_success(event)

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
        self.command('select '+str(core), ['Target CPU', 'Core state'],
                     'Error selecting core')

    def get_mode(self):
        msr = int(self.get_register_value({'register': 'MSR',
                                           'target': 'CPU',
                                           'target_index': None}), base=16)
        supervisor = not bool(msr & (1 << 14))
        return 'supervisor' if supervisor else 'user'

    def set_mode(self, mode='supervisor'):
        msr = {'register': 'MSR', 'target': 'CPU', 'target_index': None}
        value = list(bin(int(self.get_register_value(msr), base=16)))
        if mode == 'supervisor':
            value[-15] = '0'
        else:
            value[-15] = '1'
        value = hex(int(''.join(value), base=2))
        self.set_register_value(msr, value)
        with self.db as db:
            db.log_event('Information', 'Debugger', 'Set processor mode',
                         mode, success=True)

    def command(self, command, expected_output=[], error_message=None,
                log_event=True):
        return super().command(command, expected_output, error_message,
                               log_event, '\r\n', False)

    def get_register_value(self, register_info):
        target = register_info['target']
        if 'target_index' in register_info:
            target_index = register_info['target_index']
        else:
            target_index = 0
        if 'register_alias' in register_info:
            register = register_info['register_alias']
        else:
            register = register_info['register']
        if 'type' in self.targets[target] and \
                self.targets[target]['type'] == 'memory_mapped':
            command = 'md'
            if 'bits' in self.targets[target]['registers'][register]:
                bits = self.targets[target]['registers'][register]['bits']
                if bits == 8:
                    command += 'b'
                elif bits == 16:
                    command += 'h'
                elif bits == 64:
                    command += 'd'
            address = self.targets[target]['base'][target_index] + \
                self.targets[target]['registers'][register]['offset']
            buff = self.command(command+' '+hex(address)+' 1', [':'],
                                'Error getting register value')
        elif 'SPR' in self.targets[target]['registers'][register]:
            buff = self.command(
                'rdspr ' +
                str(self.targets[target]['registers'][register]['SPR']),
                [':'], 'Error getting register value')
        elif 'PMR' in self.targets[target]['registers'][register]:
            buff = self.command(
                'rdpmr ' +
                str(self.targets[target]['registers'][register]['PMR']),
                [':'], 'Error getting register value')
        else:
            buff = self.command('rd '+register, [':'],
                                'Error getting register value')
        return buff.split('\r')[0].split(':')[1].split()[0]

    def set_register_value(self, register_info, value=None):
        target = register_info['target']
        if 'target_index' in register_info:
            target_index = register_info['target_index']
        else:
            target_index = 0
        if 'register_alias' in register_info:
            register = register_info['register_alias']
        else:
            register = register_info['register']
        if value is None:
            value = register_info['injected_value']
        if 'type' in self.targets[target] and \
                self.targets[target]['type'] == 'memory_mapped':
            command = 'mm'
            if 'bits' in self.targets[target]['registers'][register]:
                bits = self.targets[target]['registers'][register]['bits']
                if bits == 8:
                    command += 'b'
                elif bits == 16:
                    command += 'h'
                elif bits == 64:
                    command += 'd'
            address = self.targets[target]['base'][target_index] + \
                self.targets[target]['registers'][register]['offset']
            self.command(command+' '+hex(address)+' '+value+' 1',
                         error_message='Error getting register value')
        elif 'SPR' in self.targets[target]['registers'][register]:
            self.command(
                'rmspr ' +
                str(self.targets[target]['registers'][register]['SPR']) +
                ' '+value,
                error_message='Error setting register value')
        elif 'PMR' in self.targets[target]['registers'][register]:
            self.command(
                'rmpmr ' +
                str(self.targets[target]['registers'][register]['PMR']) +
                ' '+value,
                error_message='Error setting register value')
        else:
            self.command('rm '+register+' '+value,
                         error_message='Error setting register value')
