from __future__ import print_function
from datetime import datetime
import pyudev
from telnetlib import Telnet
from termcolor import colored
from threading import Thread
import time
import random
from signal import SIGINT
import socket
import sqlite3
import subprocess

from dut import dut
from error import DrSEUsError
from hardware_targets import devices
from sql import insert_dict
from targets import choose_register, choose_target

# zedboards[uart_serial] = ftdi_serial
zedboards = {'844301CF3718': '210248585809',
             '8410A3D8431C': '210248657631',
             '036801551E13': '210248691084',
             '036801961420': '210248691092'}


def find_ftdi_serials():
    context = pyudev.Context()
    debuggers = context.list_devices(ID_VENDOR_ID='0403', ID_MODEL_ID='6014')
    serials = []
    for debugger in debuggers:
        if 'DEVLINKS' not in debugger:
            serials.append(debugger['ID_SERIAL_SHORT'])
    return serials


def find_uart_serials():
    context = pyudev.Context()
    uarts = context.list_devices(ID_VENDOR_ID='04b4', ID_MODEL_ID='0008')
    serials = {}
    for uart in uarts:
        if 'DEVLINKS' in uart:
            serials[uart['DEVNAME']] = uart['ID_SERIAL_SHORT']
    return serials


def find_open_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class jtag:
    def __init__(self, ip_address, port, rsakey, dut_serial_port,
                 aux_serial_port, use_aux, dut_prompt, aux_prompt, debug,
                 timeout, campaign_number):
        self.ip_address = ip_address
        self.port = port
        self.timeout = 30
        self.debug = debug
        self.use_aux = use_aux
        self.output = ''
        self.dut = dut(rsakey, dut_serial_port, dut_prompt, debug, timeout,
                       campaign_number)
        if self.use_aux:
            self.aux = dut(rsakey, aux_serial_port, aux_prompt, debug, timeout,
                           campaign_number, color='cyan')

    def __str__(self):
        string = ('JTAG Debugger at '+self.ip_address+' port '+str(self.port))
        return string

    def close(self):
        if self.telnet:
            self.telnet.close()
        self.dut.close()
        if self.use_aux:
            self.aux.close()

    def reset_dut(self, expected_output):
        if self.telnet:
            self.command('reset', expected_output, 'Error resetting DUT')
        else:
            self.dut.serial.write('\x03')
        self.dut.do_login()

    def time_application(self, command, aux_command, timing_iterations,
                         kill_dut):
        start = time.time()
        for i in xrange(timing_iterations):
            if self.use_aux:
                aux_process = Thread(target=self.aux.command,
                                     args=('./'+aux_command, ))
                aux_process.start()
            self.dut.serial.write(str('./'+command+'\n'))
            if self.use_aux:
                aux_process.join()
            if kill_dut:
                self.dut.serial.write('\x03')
            self.dut.read_until()
        end = time.time()
        return (end - start) / timing_iterations, None

    def inject_fault(self, result_id, injection_times, command,
                     selected_targets):
        if selected_targets is not None:
            for target in selected_targets:
                if target not in self.targets:
                    raise Exception('jtag.py:inject_fault(): '
                                    'invalid injection target: '+target)
        injection = 0
        for injection_time in injection_times:
            injection += 1
            if self.debug:
                print(colored('injection time: '+str(injection_time),
                              'magenta'))
            if injection == 1:
                self.dut.serial.write(str('./'+command+'\n'))
            else:
                self.continue_dut()
            time.sleep(injection_time)
            self.halt_dut()
            target = choose_target(selected_targets, self.targets)
            register = choose_register(target, self.targets)
            injection_data = {'result_id': result_id,
                              'injection_number': injection,
                              'target': target,
                              'register': register,
                              'time': injection_time,
                              'timestamp': datetime.now()}
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
            injection_data['bit'] = random.randrange(num_bits_to_inject)
            injection_data['injected_value'] = '0x%x' % (
                int(injection_data['gold_value'], base=16)
                ^ (1 << injection_data['bit']))
            if self.debug:
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
            sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
            sql = sql_db.cursor()
            insert_dict(sql, 'injection', injection_data)
            sql.execute('DELETE FROM log_injection WHERE '
                        'result_id=? AND injection_number=0', (result_id,))
            sql_db.commit()
            sql_db.close()
            if int(injection_data['injected_value'], base=16) != int(
                    self.get_register_value(injection_data['register'],
                                            injection_data['target']),
                    base=16):
                raise DrSEUsError('Error injecting fault')


class bdi(jtag):
    error_messages = ['timeout while waiting for halt',
                      'wrong state for requested command', 'read access failed']

    def __init__(self, ip_address, rsakey, dut_serial_port, aux_serial_port,
                 use_aux, dut_prompt, aux_prompt, debug, timeout,
                 campaign_number):
        jtag.__init__(self, ip_address, 23, rsakey, dut_serial_port,
                      aux_serial_port, use_aux, dut_prompt, aux_prompt, debug,
                      timeout, campaign_number)
        try:
            self.telnet = Telnet(self.ip_address, self.port,
                                 timeout=self.timeout)
        except:
            self.telnet = None
            print('Could not connect to debugger, '
                  'running in supervisor-only mode')
        else:
            self.command('', error_message='Debugger not ready')

    def __str__(self):
        string = 'BDI3000 at '+self.ip_address+' port '+str(self.port)
        return string

    def close(self):
        if self.telnet:
            self.telnet.write('quit\r')
        jtag.close(self)

    def command(self, command, expected_output=[], error_message=None):
        return_buffer = ''
        if error_message is None:
            error_message = command
        buff = self.telnet.read_very_eager()
        self.output += buff
        if self.debug:
            print(colored(buff, 'yellow'))
        if command:
            command = command+'\r'
            self.telnet.write(command)
            self.telnet.write('\r')
            self.output += command
            if self.debug:
                print(colored(command, 'yellow'))
        for i in xrange(len(expected_output)):
            index, match, buff = self.telnet.expect(expected_output,
                                                    timeout=self.timeout)
            self.output += buff
            return_buffer += buff
            if self.debug:
                print(colored(buff, 'yellow'), end='')
            if index < 0:
                raise DrSEUsError(error_message)
        else:
            if self.debug:
                print()
        index, match, buff = self.telnet.expect(self.prompts,
                                                timeout=self.timeout)
        self.output += buff
        return_buffer += buff
        if self.debug:
            print(colored(buff, 'yellow'))
        if index < 0:
            raise DrSEUsError(error_message)
        for message in self.error_messages:
            if message in return_buffer:
                raise DrSEUsError(error_message)
        return return_buffer


class bdi_arm(bdi):
    # BDI3000 with ZedBoard requires Linux kernel <= 3.6.0 (Xilinx TRD14-4)
    def __init__(self, ip_address, rsakey, dut_serial_port, aux_serial_port,
                 use_aux, dut_prompt, aux_prompt, debug, timeout,
                 campaign_number):
        self.prompts = ['A9#0>', 'A9#1>']
        self.targets = devices['a9_bdi']
        bdi.__init__(self, ip_address, rsakey, dut_serial_port, aux_serial_port,
                     use_aux, dut_prompt, aux_prompt, debug, timeout,
                     campaign_number)

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
    def __init__(self, ip_address, rsakey, dut_serial_port, aux_serial_port,
                 use_aux, dut_prompt, aux_prompt, debug, timeout,
                 campaign_number):
        self.prompts = ['P2020>']
        self.targets = devices['p2020']
        bdi.__init__(self, ip_address, rsakey, dut_serial_port, aux_serial_port,
                     use_aux, dut_prompt, aux_prompt, debug, timeout,
                     campaign_number)

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

    def __init__(self, ip_address, rsakey, dut_serial_port, aux_serial_port,
                 use_aux, dut_prompt, aux_prompt, debug, timeout,
                 campaign_number, standalone=False):
        self.prompts = ['>']
        self.targets = devices['a9']
        serial = zedboards[find_uart_serials()[dut_serial_port]]
        port = find_open_port()
        if not standalone:
            self.dev_null = open('/dev/null', 'w')
        self.openocd = subprocess.Popen(['openocd', '-c',
                                         'gdb_port 0; tcl_port 0; '
                                         'telnet_port '+str(port)+'; '
                                         'interface ftdi; '
                                         'ftdi_serial '+serial+';',
                                         '-f', 'openocd_zedboard.cfg'],
                                        stderr=(self.dev_null if not standalone
                                                else None))
        if not standalone:
            jtag.__init__(self, '127.0.0.1', port, rsakey, dut_serial_port,
                          aux_serial_port, use_aux, dut_prompt, aux_prompt,
                          debug, timeout, campaign_number)
            time.sleep(1)
            self.telnet = Telnet(self.ip_address, self.port,
                                 timeout=self.timeout)
        else:
            self.port = port

    def __str__(self):
        string = 'OpenOCD at localhost port '+str(self.port)
        return string

    def close(self):
        if self.telnet:
            self.telnet.write('shutdown\n')
        jtag.close(self)
        self.openocd.send_signal(SIGINT)
        self.openocd.wait()
        self.dev_null.close()

    def command(self, command, expected_output=[], error_message=None):
        return_buffer = ''
        if error_message is None:
            error_message = command
        buff = self.telnet.read_very_eager()
        self.output += buff
        if self.debug:
            print(colored(buff, 'yellow'))
        if command:
            self.telnet.write(command+'\n')
            index, match, buff = self.telnet.expect([command],
                                                    timeout=self.timeout)
            self.output += buff
            return_buffer += buff
            if self.debug:
                print(colored(buff, 'yellow'))
            if index < 0:
                raise DrSEUsError(error_message)
        for i in xrange(len(expected_output)):
            index, match, buff = self.telnet.expect(expected_output,
                                                    timeout=self.timeout)
            self.output += buff
            return_buffer += buff
            if self.debug:
                print(colored(buff, 'yellow'), end='')
            if index < 0:
                raise DrSEUsError(error_message)
        else:
            if self.debug:
                print()
        index, match, buff = self.telnet.expect(self.prompts,
                                                timeout=self.timeout)
        self.output += buff
        return_buffer += buff
        if self.debug:
            print(colored(buff, 'yellow'))
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
