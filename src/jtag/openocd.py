from json import load
from os.path import exists
from pyudev import Context
from socket import AF_INET, SOCK_STREAM, socket
from subprocess import DEVNULL, Popen
from termcolor import colored
from time import sleep

from ..error import DrSEUsError
from ..targets import get_targets
from . import jtag


def find_ftdi_serials():
    debuggers = Context().list_devices(ID_VENDOR_ID='0403',
                                       ID_MODEL_ID='6014')
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


class openocd(jtag):
    error_messages = ['Timeout', 'Target not examined yet']
    modes = {'10000': 'usr',
             '10001': 'fiq',
             '10010': 'irq',
             '10011': 'svc',
             '10110': 'mon',
             '10111': 'abt',
             '11010': 'hyp',
             '11011': 'und',
             '11111': 'sys'}

    def __init__(self, database, options, power_switch=None):

        def find_open_port():
            sock = socket(AF_INET, SOCK_STREAM)
            sock.bind(('', 0))
            port = sock.getsockname()[1]
            sock.close()
            return port

    # def __init__(self, database, options, power_switch=None):
        self.power_switch = power_switch
        if exists('devices.json'):
            with open('devices.json', 'r') as device_file:
                device_info = load(device_file)
            for device in device_info:
                if device['uart'] == \
                        find_uart_serials()[options.dut_serial_port]:
                    self.device_info = device
                    break
            else:
                raise Exception('could not find entry in "devices.json" for '
                                'device at '+options.dut_serial_port)
        else:
            ftdis = find_ftdi_serials()
            if len(ftdis) == 1:
                self.device_info = {
                    'ftdi': ftdis[0],
                    'uart': find_uart_serials()[options.dut_serial_port]
                }
            else:
                raise Exception('multiple ZedBoards connected and could not '
                                'find device information file "devices.json", '
                                'try running command "power detect" or '
                                'disconnecting extra zedboards')

        options.debugger_ip_address = '127.0.0.1'
        self.prompts = ['>']
        self.targets = get_targets('a9', 'jtag')
        self.port = find_open_port()
        super().__init__(database, options)
        if self.options.command == 'openocd' and self.options.gdb:
            self.gdb_port = find_open_port()
        else:
            self.gdb_port = 0
        self.open()

    def __str__(self):
        string = 'OpenOCD at localhost port '+str(self.port)
        if hasattr(self, 'gdb_port') and self.gdb_port:
            string += ' (GDB port '+str(self.gdb_port)+')'
        return string

    def open(self):
        self.openocd = Popen(['openocd', '-c',
                              'gdb_port '+str(self.gdb_port)+'; '
                              'tcl_port 0; '
                              'telnet_port '+str(self.port)+'; '
                              'interface ftdi; '
                              'ftdi_serial '+self.device_info['ftdi']+';',
                              '-f', 'openocd_zedboard.cfg'],
                             stderr=(DEVNULL
                                     if self.options.command != 'openocd'
                                     else None))
        if self.options.command != 'openocd':
            with self.db as db:
                db.log_event('Information', 'Debugger', 'Launched openocd',
                             success=True)
            sleep(1)
        if self.options.command != 'openocd':
            super().open()

    def close(self):
        self.telnet.write(bytes('shutdown\n', encoding='utf-8'))
        self.openocd.wait()
        with self.db as db:
            db.log_event('Information', 'Debugger', 'Closed openocd',
                         success=True)
        super().close()

    def command(self, command, expected_output=[], error_message=None,
                log_event=True):
        return super().command(command, expected_output, error_message,
                               log_event, '\n', True)

    def reset_dut(self, attempts=10):
        if self.power_switch:
            try:
                super().reset_dut(
                    ['JTAG tap: zynq.dap tap/device found: 0x4ba00477'], 1)
            except DrSEUsError:
                self.power_cycle_dut()
                super().reset_dut(
                    ['JTAG tap: zynq.dap tap/device found: 0x4ba00477'],
                    max(attempts-1, 1))
        else:
            super().reset_dut(
                ['JTAG tap: zynq.dap tap/device found: 0x4ba00477'], attempts)

    def power_cycle_dut(self):
        with self.db as db:
            event = db.log_event('Information', 'Debugger',
                                 'Power cycled DUT', success=False)
        self.close()
        with self.power_switch as ps:
            ps.set_outlet(self.device_info['outlet'], 'off')
            ps.set_outlet(self.device_info['outlet'], 'on')
        for serial_port, uart_serial in find_uart_serials().items():
            if uart_serial == self.device_info['uart']:
                self.options.dut_serial_port = serial_port
                self.db.result['dut_serial_port'] = serial_port
                break
        else:
            raise Exception('Error finding uart device after power cycle')
        self.open()
        print(colored('Power cycled device: '+self.dut.serial.port, 'red'))
        with self.db as db:
            db.log_event_success(event)

    def halt_dut(self):
        super().halt_dut('halt', ['target state: halted']*2)

    def continue_dut(self):
        super().continue_dut('resume')

    def select_core(self, core):
        self.command('targets zynq.cpu'+str(core),
                     error_message='Error selecting core')

    def get_mode(self):
        cpsr = int(self.get_register_value('cpsr', 'CPU', None), base=16)
        return self.modes[str(bin(cpsr))[-5:]]

    def set_mode(self, mode='svc'):
        modes = {value: key for key, value in self.modes.items()}
        mask = modes[mode]
        cpsr = int(self.get_register_value('cpsr', 'CPU', None), base=16)
        self.set_register_value('cpsr', 'CPU', None,
                                hex(int(str(bin(cpsr))[:-5]+mask, base=2)))
        with self.db as db:
            db.log_event('Information', 'Debugger', 'Set processor mode', mode,
                         success=True)

    def get_register_value(self, register, target, target_index):
        if 'CP' in self.targets[target] and self.targets[target]['CP']:
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
                                'Error getting register value')
            return \
                buff.split('\n')[1].split(':')[1].split()[0]

    def set_register_value(self, register, target, target_index, value):
        if 'CP' in self.targets[target] and self.targets[target]['CP']:
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
