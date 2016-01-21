from pyudev import Context
from telnetlib import Telnet
from termcolor import colored
from threading import Thread
from time import sleep, time
from random import randrange, uniform
import socket
from subprocess import DEVNULL, Popen
from traceback import print_exc

from dut import dut
from error import DrSEUsError
from jtag_targets import devices
from sql import sql
from targets import choose_register, choose_target

# zedboards[uart_serial] = ftdi_serial
zedboards = {'844301CF3718': '210248585809',
             '8410A3D8431C': '210248657631',
             '036801551E13': '210248691084',
             '036801961420': '210248691092'}


def find_ftdi_serials():
    debuggers = Context().list_devices(ID_VENDOR_ID='0403', ID_MODEL_ID='6014')
    serials = []
    for debugger in debuggers:
        if 'DEVLINKS' not in debugger:
            serials.append(debugger['ID_SERIAL_SHORT'])
    return serials


def find_uart_serials():
    uarts = Context().list_devices(ID_VENDOR_ID='04b4', ID_MODEL_ID='0008')
    serials = {}
    for uart in uarts:
        if 'DEVLINKS' in uart:
            serials[uart['DEVNAME']] = uart['ID_SERIAL_SHORT']
    return serials


class jtag(object):
    def __init__(self, campaign_data, result_data, options, rsakey):
        self.campaign_data = campaign_data
        self.result_data = result_data
        self.options = options
        self.timeout = 30
        self.prompts = [bytes(prompt, encoding='utf-8')
                        for prompt in self.prompts]
        if options.command == 'inject' and options.selected_targets is not None:
            for target in options.selected_targets:
                if target not in self.targets:
                    raise Exception('invalid injection target: '+target)
        self.dut = dut(campaign_data, result_data, options, rsakey)
        if campaign_data['use_aux']:
            self.aux = dut(campaign_data, result_data, options, rsakey,
                           aux=True)

    def __str__(self):
        string = 'JTAG Debugger at '+self.options.debugger_ip_address
        try:
            string += ' port '+str(self.port)
        except AttributeError:
            pass
        return string

    def close(self):
        if self.telnet:
            self.telnet.close()
        self.dut.close()
        if self.campaign_data['use_aux']:
            self.aux.close()

    def reset_dut(self, expected_output):
        if self.telnet:
            self.command('reset', expected_output, 'Error resetting DUT')
        else:
            self.dut.serial.write('\x03')
        self.dut.do_login()

    def time_application(self):
        start = time()
        for i in range(self.options.iterations):
            if self.campaign_data['use_aux']:
                aux_process = Thread(
                    target=self.aux.command,
                    args=('./'+self.campaign_data['aux_command'], ))
                aux_process.start()
            self.dut.write('./'+self.campaign_data['command']+'\n')
            if self.campaign_data['use_aux']:
                aux_process.join()
            if self.campaign_data['kill_dut']:
                self.dut.serial.write('\x03')
            self.dut.read_until()
        end = time()
        self.campaign_data['exec_time'] = \
            (end - start) / self.options.iterations

    def inject_faults(self):
        injection_times = []
        for i in range(self.options.injections):
            injection_times.append(uniform(0, self.campaign_data['exec_time']))
        injection_times = sorted(injection_times)
        injection = 0
        for injection_time in injection_times:
            injection += 1
            if self.options.debug:
                print(colored('injection time: '+str(injection_time),
                              'magenta'))
            if injection == 1:
                self.dut.write('./'+self.campaign_data['command']+'\n')
            else:
                self.continue_dut()
            sleep(injection_time)
            self.halt_dut()
            target = choose_target(self.options.selected_targets, self.targets)
            register = choose_register(target, self.targets)
            injection_data = {'result_id': self.result_data['id'],
                              'injection_number': injection,
                              'target': target,
                              'register': register,
                              'time': injection_time,
                              'timestamp': None}
            if ':' in target:
                injection_data['target_index'] = target.split(':')[1]
                target = target.split(':')[0]
                injection_data['target'] = target
                self.select_core(injection_data['target_index'])
            injection_data['gold_value'] = self.get_register_value(
                injection_data['register'], injection_data['target'])
            if 'bits' in self.targets[target]['registers'][register]:
                num_bits_to_inject = (self.targets[target]['registers']
                                                  [register]['bits'])
            else:
                num_bits_to_inject = 32
            injection_data['bit'] = randrange(num_bits_to_inject)
            injection_data['injected_value'] = '0x%x' % \
                (int(injection_data['gold_value'], base=16) ^
                    (1 << injection_data['bit']))
            if self.options.debug:
                print(colored('target: '+injection_data['target'], 'magenta'))
                if 'target_index' in injection_data:
                    print(colored('target_index: ' +
                                  str(injection_data['target_index']),
                                  'magenta'))
                print(colored('register: '+injection_data['register'],
                              'magenta'))
                print(colored('bit: '+str(injection_data['bit']), 'magenta'))
                print(colored('gold value: '+injection_data['gold_value'],
                              'magenta'))
                print(colored('injected value: ' +
                              injection_data['injected_value'], 'magenta'))
            self.set_register_value(injection_data['register'],
                                    injection_data['target'],
                                    injection_data['injected_value'])
            if int(injection_data['injected_value'], base=16) == int(
                    self.get_register_value(injection_data['register'],
                                            injection_data['target']),
                    base=16):
                injection_data['success'] = True
            else:
                injection_data['success'] = False
            with sql() as db:
                db.insert_dict('injection', injection_data)
        return 0, False


class bdi(jtag):
    error_messages = ['timeout while waiting for halt',
                      'wrong state for requested command', 'read access failed']

    def __init__(self, campaign_data, result_data, options, rsakey):
        self.port = 23
        jtag.__init__(self, campaign_data, result_data, options, rsakey)
        try:
            self.telnet = Telnet(self.options.debugger_ip_address, self.port,
                                 timeout=self.timeout)
        except:
            self.telnet = None
            print_exc()
            print(colored('Could not connect to debugger, '
                          'running in supervisor-only mode', 'red'))
        else:
            self.command('', error_message='Debugger not ready')

    def __str__(self):
        string = ('BDI3000 at '+self.options.debugger_ip_address +
                  ' port '+str(self.port))
        return string

    def close(self):
        if self.telnet:
            self.telnet.write(bytes('quit\r', encoding='utf-8'))
        jtag.close(self)

    def command(self, command, expected_output=[], error_message=None):
        expected_output = [bytes(output, encoding='utf-8')
                           for output in expected_output]
        return_buffer = ''
        if error_message is None:
            error_message = command
        buff = self.telnet.read_very_eager().decode('utf-8', 'replace')
        if self.options.command == 'new':
            self.campaign_data['debugger_output'] += buff
        else:
            self.result_data['debugger_output'] += buff
        if self.options.debug:
            print(colored(buff, 'yellow'))
        if command:
            command = command+'\r'
            self.telnet.write(bytes(command, encoding='utf-8'))
            self.telnet.write(bytes('\r', encoding='utf-8'))
            if self.options.command == 'new':
                self.campaign_data['debugger_output'] += command
            else:
                self.result_data['debugger_output'] += command
            if self.options.debug:
                print(colored(command, 'yellow'))
        for i in range(len(expected_output)):
            index, match, buff = self.telnet.expect(expected_output,
                                                    timeout=self.timeout)
            buff = buff.decode('utf-8', 'replace')
            if self.options.command == 'new':
                self.campaign_data['debugger_output'] += buff
            else:
                self.result_data['debugger_output'] += buff
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
        if self.options.command == 'new':
            self.campaign_data['debugger_output'] += buff
        else:
            self.result_data['debugger_output'] += buff
        return_buffer += buff
        if self.options.debug:
            print(colored(buff, 'yellow'))
        if not self.options.command == 'supervise':
            with sql() as db:
                if self.options.command == 'new':
                    db.update_dict('campaign', self.campaign_data)
                else:
                    db.update_dict('result', self.result_data)
        if index < 0:
            raise DrSEUsError(error_message)
        for message in self.error_messages:
            if message in return_buffer:
                raise DrSEUsError(error_message)
        return return_buffer


class bdi_arm(bdi):
    # BDI3000 with ZedBoard requires Linux kernel <= 3.6.0 (Xilinx TRD14-4)
    def __init__(self, campaign_data, result_data, options, rsakey):
        self.prompts = ['A9#0>', 'A9#1>']
        self.targets = devices['a9_bdi']
        bdi.__init__(self, campaign_data, result_data, options, rsakey)

    def reset_dut(self):
        jtag.reset_dut(self, ['- TARGET: processing reset request',
                              '- TARGET: BDI removes TRST',
                              '- TARGET: Bypass check',
                              '- TARGET: JTAG exists check passed',
                              '- Core#0: ID code', '- Core#0: DP-CSW',
                              '- Core#0: DBG-AP', '- Core#0: DIDR',
                              '- Core#1: ID code', '- Core#1: DP-CSW',
                              '- Core#1: DBG-AP', '- Core#1: DIDR',
                              '- TARGET: BDI removes RESET',
                              '- TARGET: BDI waits for RESET inactive',
                              '- TARGET: Reset sequence passed',
                              '- TARGET: resetting target passed',
                              '- TARGET: processing target startup',
                              '- TARGET: processing target startup passed'])

    def halt_dut(self):
        self.command('halt 3', ['- TARGET: core #0 has entered debug mode',
                                '- TARGET: core #1 has entered debug mode'],
                     'Error halting DUT')

    def continue_dut(self):
        self.command('cont 3', error_message='Error continuing DUT')

    def select_core(self, core):
        # TODO: check if cores are running (not in debug mode)
        self.command('select '+str(core), ['Core number', 'Core state',
                                           'Debug entry cause', 'Current PC',
                                           'Current CPSR'],
                     'Error selecting core')

    def get_register_value(self, register, target):
        buff = self.command('rd '+register, [':'],
                            error_message='Error getting register value')
        return buff.split('\r')[0].split(':')[1].strip().split(' ')[0].strip()

    def set_register_value(self, register, target, value):
        self.command('rm '+register+' '+value, error_message='Error setting '
                                                             'register value')


class bdi_p2020(bdi):
    def __init__(self, campaign_data, result_data, options, rsakey):
        self.prompts = ['P2020>']
        self.targets = devices['p2020']
        bdi.__init__(self, campaign_data, result_data, options, rsakey)

    def reset_dut(self):
        jtag.reset_dut(self, ['- TARGET: processing user reset request',
                              '- BDI asserts HRESET',
                              '- Reset JTAG controller passed',
                              '- JTAG exists check passed',
                              '- IDCODE',
                              '- SVR',
                              '- PVR',
                              '- CCSRBAR',
                              '- BDI removes HRESET',
                              '- TARGET: resetting target passed',
                              # '- TARGET: processing target startup',
                              '- TARGET: processing target startup passed'])

    def halt_dut(self):
        self.command('halt 0; halt 1', ['Target CPU', 'Core state',
                                        'Debug entry cause', 'Current PC',
                                        'Current CR', 'Current MSR',
                                        'Current LR']*2, 'Error halting DUT')

    def continue_dut(self):
        self.command('go 0 1', error_message='Error continuing DUT')

    def select_core(self, core):
        self.command('select '+str(core), ['Target CPU', 'Core state',
                                           'Debug entry cause', 'Current PC',
                                           'Current CR', 'Current MSR',
                                           'Current LR', 'Current CCSRBAR'],
                     'Error selecting core')

    def get_register_value(self, register, target):
        buff = self.command('rd '+register, error_message='Error getting '
                                                          'register value')
        return buff.split('\r')[0].split(':')[1].strip().split(' ')[0].strip()

    def set_register_value(self, register, target, value):
        self.command('rm '+register+' '+value, error_message='Error setting '
                                                             'register value')


class openocd(jtag):
    error_messages = ['Timeout', 'Target not examined yet']

    def __init__(self, campaign_data, result_data, options, rsakey):

        def find_open_port():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 0))
            port = sock.getsockname()[1]
            sock.close()
            return port

    # def __init__(self, campaign_data, result_data, options, rsakey):
        options.debugger_ip_address = '127.0.0.1'
        self.prompts = ['>']
        self.targets = devices['a9']
        serial = zedboards[find_uart_serials()[options.dut_serial_port]]
        self.port = find_open_port()
        self.openocd = Popen(['openocd', '-c',
                              'gdb_port 0; tcl_port 0; telnet_port ' +
                              str(self.port)+'; interface ftdi; ftdi_serial ' +
                              serial+';', '-f', 'openocd_zedboard.cfg'],
                             stderr=(DEVNULL if options.command != 'openocd'
                                     else None))
        if options.command != 'openocd':
            jtag.__init__(self, campaign_data, result_data, options, rsakey)
            sleep(1)
            self.telnet = Telnet(self.options.debugger_ip_address, self.port,
                                 timeout=self.timeout)

    def __str__(self):
        string = 'OpenOCD at localhost port '+str(self.port)
        return string

    def close(self):
        self.telnet.write(bytes('shutdown\n', encoding='utf-8'))
        jtag.close(self)
        self.openocd.wait()

    def command(self, command, expected_output=[], error_message=None):
        expected_output = [bytes(output, encoding='utf-8')
                           for output in expected_output]
        return_buffer = ''
        if error_message is None:
            error_message = command
        buff = self.telnet.read_very_eager().decode('utf-8', 'replace')
        if self.options.command == 'new':
            self.campaign_data['debugger_output'] += buff
        else:
            self.result_data['debugger_output'] += buff
        if self.options.debug:
            print(colored(buff, 'yellow'))
        if command:
            self.telnet.write(bytes(command+'\n', encoding='utf-8'))
            index, match, buff = self.telnet.expect(
                [bytes(command, encoding='utf-8')], timeout=self.timeout)
            buff = buff.decode('utf-8', 'replace')
            if self.options.command == 'new':
                self.campaign_data['debugger_output'] += buff
            else:
                self.result_data['debugger_output'] += buff
            return_buffer += buff
            if self.options.debug:
                print(colored(buff, 'yellow'))
            if index < 0:
                raise DrSEUsError(error_message)
        for i in range(len(expected_output)):
            index, match, buff = self.telnet.expect(expected_output,
                                                    timeout=self.timeout)
            buff = buff.decode('utf-8', 'replace')
            if self.options.command == 'new':
                self.campaign_data['debugger_output'] += buff
            else:
                self.result_data['debugger_output'] += buff
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
        if self.options.command == 'new':
            self.campaign_data['debugger_output'] += buff
        else:
            self.result_data['debugger_output'] += buff
        return_buffer += buff
        if self.options.debug:
            print(colored(buff, 'yellow'))
        if not self.options.command == 'supervise':
            with sql() as db:
                if self.options.command == 'new':
                    db.update_dict('campaign', self.campaign_data)
                else:
                    db.update_dict('result', self.result_data)
        if index < 0:
            raise DrSEUsError(error_message)
        for message in self.error_messages:
            if message in return_buffer:
                raise DrSEUsError(error_message)
        return return_buffer

    def reset_dut(self):
        jtag.reset_dut(self,
                       ['JTAG tap: zynq.dap tap/device found: 0x4ba00477'])

    def halt_dut(self):
        self.command('halt',
                     ['target state: halted',
                      'target halted in ARM state due to debug-request, '
                      'current mode:', 'cpsr:', 'MMU:']*2,
                     'Error halting DUT')

    def continue_dut(self):
        self.command('resume', error_message='Error continuing DUT')

    def select_core(self, core):
        self.command('targets zynq.cpu'+str(core),
                     error_message='Error selecting core')

    def get_register_value(self, register, target):
        if target == 'CP':
            buff = self.command(
                ' '.join([
                    'arm', 'mrc',
                    str(self.targets[target]['registers'][register]['CP']),
                    str(self.targets[target]['registers'][register]['Op1']),
                    str(self.targets[target]['registers'][register]['CRn']),
                    str(self.targets[target]['registers'][register]['CRm']),
                    str(self.targets[target]['registers'][register]['Op2'])]),
                error_message='Error getting register value')
            return hex(int(buff.split('\n')[1].strip()))
        else:
            buff = self.command('reg '+register, [':'],
                                error_message='Error getting register value')
            return \
                buff.split('\n')[1].split(':')[1].strip().split(' ')[0].strip()

    def set_register_value(self, register, target, value):
        if target == 'CP':
            self.command(
                ' '.join([
                    'arm', 'mrc',
                    str(self.targets[target]['registers'][register]['CP']),
                    str(self.targets[target]['registers'][register]['Op1']),
                    str(self.targets[target]['registers'][register]['CRn']),
                    str(self.targets[target]['registers'][register]['CRm']),
                    str(self.targets[target]['registers'][register]['Op2']),
                    value]),
                error_message='Error setting register value')
        else:
            self.command('reg '+register+' '+value,
                         error_message='Error setting register value')
