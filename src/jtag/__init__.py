from pyudev import Context
from random import uniform
from socket import AF_INET, SOCK_STREAM, socket
from telnetlib import Telnet
from termcolor import colored
from time import sleep

from ..dut import dut
from ..error import DrSEUsError
from ..targets import choose_injection, get_targets


def find_devices():
    devices = {'jtag': {}, 'uart': {}}
    for dev in Context().list_devices():
        if 'ID_VENDOR_ID' not in dev or 'ID_MODEL_ID' not in dev:
            continue
        if 'DEVLINKS' in dev:
            if dev['ID_VENDOR_ID'] == '067b' and dev['ID_MODEL_ID'] == '2303':
                devices['uart'][dev['DEVNAME']] = {'type': 'p2020'}
            elif dev['ID_VENDOR_ID'] == '04b4' and dev['ID_MODEL_ID'] == '0008':
                devices['uart'][dev['DEVNAME']] = {
                    'type': 'zedboard', 'serial': dev['ID_SERIAL_SHORT']}
            elif dev['ID_VENDOR_ID'] == '0403' and dev['ID_MODEL_ID'] == '6010':
                if dev['ID_USB_INTERFACE_NUM'] == '01':
                    devices['uart'][dev['DEVNAME']] = {
                        'type': 'pynq', 'serial': dev['ID_SERIAL_SHORT']}
            elif dev['ID_VENDOR_ID'] == '0403' and dev['ID_MODEL_ID'] == '6001':
                devices['uart'][dev['DEVNAME']] = {
                    'type': 'pmod', 'serial': dev['ID_SERIAL_SHORT']}
            elif dev['SUBSYSTEM'] == 'tty':
                devices['uart'][dev['DEVNAME']] = {'type': 'other'}
                if 'ID_SERIAL_SHORT' in dev:
                    devices['uart'][dev['DEVNAME']]['serial'] = \
                        dev['ID_SERIAL_SHORT']
        else:
            if dev['ID_VENDOR_ID'] == '0403' and dev['ID_MODEL_ID'] == '6014':
                devices['jtag'][dev['ID_SERIAL_SHORT']] = {'type': 'zedboard'}
            elif dev['ID_VENDOR_ID'] == '0403' and dev['ID_MODEL_ID'] == '6010':
                devices['jtag'][dev['ID_SERIAL_SHORT']] = {'type': 'pynq'}
    return devices


def find_open_port():
            sock = socket(AF_INET, SOCK_STREAM)
            sock.bind(('', 0))
            port = sock.getsockname()[1]
            sock.close()
            return port


class jtag(object):
    def __init__(self, database, options):
        self.db = database
        self.options = options
        self.timeout = 30
        self.prompts = [bytes(prompt, encoding='utf-8')
                        for prompt in self.prompts]

    def __str__(self):
        string = 'JTAG Debugger at {}'.format(self.options.debugger_ip_address)
        try:
            string += ' port {}'.format(self.port)
        except AttributeError:
            pass
        return string

    def connect_telnet(self):
        self.telnet = Telnet(self.options.debugger_ip_address, self.port,
                             timeout=self.timeout)
        self.db.log_event(
            'Information', 'Debugger', 'Connected to telnet',
            '{}:{}'.format(self.options.debugger_ip_address, self.port))

    def open(self):
        self.dut = dut(self.db, self.options)
        if self.db.campaign.aux:
            self.aux = dut(self.db, self.options, aux=True)
        self.connect_telnet()

    def close(self):
        self.telnet.close()
        self.db.log_event(
            'Information', 'Debugger', 'Closed telnet')
        self.dut.close()
        if self.db.campaign.aux:
            self.aux.close()

    def set_targets(self, architecture):
        if hasattr(self.options, 'selected_targets'):
            selected_targets = self.options.selected_targets
        else:
            selected_targets = None
        if hasattr(self.options, 'selected_registers'):
            selected_registers = self.options.selected_registers
        else:
            selected_registers = None
        self.targets = get_targets(architecture, 'jtag', selected_targets,
                                   selected_registers)

    def reset_dut(self, expected_output, attempts):

        def attempt_exception(attempt, attempts, error, event_type):
            self.db.log_event(
                'Warning' if attempt < attempts-1 else 'Error', 'Debugger',
                event_type, self.db.log_exception)
            print(colored('{}: Error resetting DUT (attempt {}/{}): {}'.format(
                self.dut.serial.port, attempt+1, attempts, error), 'red'))
            if attempt < attempts-1:
                sleep(30)
            else:
                raise DrSEUsError(error.type)

    # def reset_dut(self, expected_output, attempts):
        self.dut.flush()
        self.dut.reset_ip()
        for attempt in range(attempts):
            try:
                self.command('reset', expected_output,
                             'Error resetting DUT', True)
            except DrSEUsError as error:
                attempt_exception(attempt, attempts, error,
                                  'Error resetting DUT')
            else:
                try:
                    self.dut.do_login()
                except DrSEUsError as error:
                    attempt_exception(attempt, attempts, error,
                                      'Error booting DUT')
                else:
                    break

    def halt_dut(self, halt_command, expected_output):
        event = self.db.log_event(
            'Information', 'Debugger', 'Halt DUT', success=False)
        self.command(halt_command, expected_output, 'Error halting DUT', False)
        self.dut.stop_timer()
        event.success = True
        event.save()

    def continue_dut(self, continue_command):
        event = self.db.log_event(
            'Information', 'Debugger', 'Continue DUT', success=False)
        self.command(continue_command, error_message='Error continuing DUT',
                     log_event=False)
        self.dut.start_timer()
        event.success = True
        event.save()

    def inject_faults(self):
        injection_times = []
        for i in range(self.options.injections):
            injection_times.append(uniform(0,
                                           self.db.campaign.execution_time))
        injections = []
        if hasattr(self, 'targets') and self.targets:
            for injection_time in sorted(injection_times):
                injection = choose_injection(
                    self.targets, self.options.selected_target_indices)
                injection = self.db.result.injection_set.create(
                    success=False, time=injection_time, **injection)
                injections.append(injection)
        if self.db.campaign.command:
            self.dut.write('{}\n'.format(self.db.campaign.command))
        previous_injection_time = 0
        for injection in injections:
            if injection.target in ('CPU', 'GPR', 'TLB') or \
                ('CP' in self.targets[injection.target] and
                    self.targets[injection.target]['CP']):
                self.select_core(injection.target_index)
            sleep(injection.time-previous_injection_time)
            self.halt_dut()
            previous_injection_time = injection.time
            injection.processor_mode = self.get_mode()
            if 'access' in (self.targets[injection.target]
                                        ['registers'][injection.register]):
                injection.register_access = \
                    (self.targets[injection.target]
                                 ['registers'][injection.register]['access'])
            injection.gold_value = \
                self.get_register_value(injection)
            injection.injected_value = hex(
                int(injection.gold_value, base=16) ^ (1 << injection.bit))
            injection.save()
            if self.options.debug:
                print(colored(
                    'result id: {}\ninjection time: {}\ntarget: {}\n'
                    'register: {}\nbit: {}\ngold value: {}\ninjected value: {}'
                    ''.format(
                        self.db.result.id, injection.time,
                        injection.target_name, injection.register,
                        injection.bit, injection.gold_value,
                        injection.injected_value), 'magenta'))
            self.set_register_value(injection)
            if int(injection.injected_value, base=16) == \
                    int(self.get_register_value(injection), base=16):
                injection.success = True
                injection.save()
                self.db.log_event(
                    'Information', 'Debugger', 'Fault injected')
            else:
                self.set_mode()
                self.set_register_value(injection)
                if int(injection.injected_value, base=16) == \
                        int(self.get_register_value(injection), base=16):
                    injection.success = True
                    injection.save()
                    self.db.log_event(
                        'Information', 'Debugger',
                        'Fault injected as supervisor')
                else:
                    self.db.log_event(
                        'Error', 'Debugger', 'Injection failed')
                self.set_mode(injection.processor_mode)
            self.continue_dut()
        return None, None, False

    def command(self, command, expected_output, error_message,
                log_event, line_ending, echo):
        if log_event:
            event = self.db.log_event(
                'Information', 'Debugger', 'Command', command, success=False)
        expected_output = [bytes(output, encoding='utf-8')
                           for output in expected_output]
        return_buffer = ''
        if error_message is None:
            error_message = command
        buff = self.telnet.read_very_eager().decode('utf-8', 'replace')
        if self.db.result is None:
            self.db.campaign.debugger_output += buff
        else:
            self.db.result.debugger_output += buff
        if self.options.debug:
            print(colored(buff, 'yellow'))
        if command:
            self.telnet.write(bytes('{}{}'.format(command, line_ending),
                                    encoding='utf-8'))
            if echo:
                index, match, buff = self.telnet.expect(
                    [bytes(command, encoding='utf-8')], timeout=self.timeout)
                buff = buff.decode('utf-8', 'replace')
            else:
                buff = '{}\n'.format(command)
            if self.db.result is None:
                self.db.campaign.debugger_output += buff
            else:
                self.db.result.debugger_output += buff
            if self.options.debug:
                print(colored(buff, 'yellow'))
            if echo and index < 0:
                raise DrSEUsError(error_message)
        for i in range(len(expected_output)):
            index, match, buff = self.telnet.expect(expected_output,
                                                    timeout=self.timeout)
            buff = buff.decode('utf-8', 'replace')
            if self.db.result is None:
                self.db.campaign.debugger_output += buff
            else:
                self.db.result.debugger_output += buff
            return_buffer += buff
            if self.options.debug:
                print(colored(buff, 'yellow'), end='')
            if index < 0:
                raise DrSEUsError(error_message)
        else:
            if self.options.debug:
                print()
        index, match, buff = self.telnet.expect(self.prompts,
                                                timeout=self.timeout)
        buff = buff.decode('utf-8', 'replace')
        if self.db.result is None:
            self.db.campaign.debugger_output += buff
        else:
            self.db.result.debugger_output += buff
        return_buffer += buff
        if self.options.debug:
            print(colored(buff, 'yellow'))
        self.db.save()
        if index < 0:
            raise DrSEUsError(error_message)
        for message in self.error_messages:
            if message in return_buffer:
                raise DrSEUsError(error_message)
        if log_event:
            event.success = True
            event.save()
        return return_buffer

    def select_core(self, core):
        pass

    def get_mode(self):
        pass

    def set_mode(self, mode):
        pass

    def get_register_value(self, register_info):
        pass

    def set_register_value(self, register_info, value):
        pass
