from json import load
from os.path import abspath, dirname, exists
from subprocess import DEVNULL, Popen, TimeoutExpired
from termcolor import colored
from time import sleep

from ..error import DrSEUsError
from . import find_open_port, find_devices, jtag


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

    def __init__(self, database, options, power_switch):
        self.power_switch = power_switch
        if exists('devices.json'):
            with open('devices.json', 'r') as device_file:
                device_info = load(device_file)
            for device in device_info:
                if device['uart'] == (find_devices()['uart']
                                                    [options.dut_serial_port]
                                                    ['serial']):
                    self.device_info = device
                    break
            else:
                raise Exception('could not find entry in "devices.json" for '
                                'device at {}'.format(options.dut_serial_port))
        else:
            raise Exception(
                'could not find device information file "devices.json", use '
                'command "detect" (or "power detect" if using a web power '
                'switch) to detect devices and generate the file')
        options.debugger_ip_address = '127.0.0.1'
        self.prompts = ['>']
        self.port = find_open_port()
        super().__init__(database, options)
        self.set_targets()
        if self.options.command == 'openocd' and self.options.gdb:
            self.gdb_port = find_open_port()
        else:
            self.gdb_port = 0
        self.open()

    def __str__(self):
        string = 'OpenOCD at localhost port {}'.format(self.port)
        if hasattr(self, 'gdb_port') and self.gdb_port:
            string += ' (GDB port {})'.format(self.gdb_port)
        return string

    def set_targets(self):
        super().set_targets('a9')

    def open(self):
        self.openocd = Popen([
            'openocd/src/openocd', '-c',
            'gdb_port {}; '
            'tcl_port 0; '
            'telnet_port {}; '
            'interface ftdi; '
            'ftdi_serial {};'.format(
                self.gdb_port,
                self.port,
                self.device_info['jtag']),
            '-f', '{}/openocd_{}.cfg'.format(
                dirname(abspath(__file__)),
                'smp' if self.options.smp else 'amp')],
            stderr=(DEVNULL if self.options.command != 'openocd' else None))
        if self.options.command != 'openocd':
            self.db.log_event(
                'Information', 'Debugger', 'Launched openocd')
            sleep(1)
            super().open()

    def close(self):
        try:
            self.telnet.write(bytes('shutdown\n', encoding='utf-8'))
        except:
            pass
        try:
            self.openocd.wait(timeout=30)
        except TimeoutExpired:
            self.openocd.kill()
            self.db.log_event(
                'Warning', 'Debugger', 'Killed unresponsive openocd')
        else:
            self.db.log_event(
                'Information', 'Debugger', 'Closed openocd')
        super().close()

    def command(self, command, expected_output=[], error_message=None,
                log_event=True):
        return super().command(command, expected_output, error_message,
                               log_event, '\n', True)

    def reset_dut(self, attempts=10):
        if self.power_switch:
            if self.options.command == 'supervise':
                for attempt in range(attempts):
                    try:
                        self.power_cycle_dut()
                        super().reset_dut(
                            ['JTAG tap: zynq.dap tap/device found: 0x4ba00477'],
                            1)
                    except Exception as error:
                        if attempt < attempts-1:
                            sleep(10)
                        else:
                            raise error
                    else:
                        break
            else:
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
        if self.device_info['outlet'] is None:
            print(colored(
                'Could not power cycle device at {}, it is not associated with'
                ' a power outlet'.format(self.dut.serial.port), 'red'))
            return
        event = self.db.log_event(
            'Information', 'Debugger', 'Power cycled DUT', success=False)
        self.close()
        attempts = 5
        for attempt in range(attempts):
            try:
                with self.power_switch as ps:
                    ps.set_outlet(self.device_info['outlet'], 'off')
                    ps.set_outlet(self.device_info['outlet'], 'on')
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception:
                self.db.log_event(
                    'Warning' if attempt < attempts-1 else 'Error', 'DrSEUs',
                    'Error power cycling DUT', self.db.log_exception)
                if attempt < attempts-1:
                    sleep(30)
                else:
                    raise Exception('Error power cycling DUT')
            else:
                break
        for attempt in range(attempts):
            try:
                for serial_port, info in find_devices()['uart'].items():
                    if 'serial' in info and \
                            info['serial'] == self.device_info['uart']:
                        self.options.dut_serial_port = serial_port
                        self.db.result.dut_serial_port = serial_port
                        break
                else:
                    raise Exception('Could not find uart device')
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception:
                self.db.log_event(
                    'Warning' if attempt < attempts-1 else 'Error', 'DrSEUs',
                    'Error getting device information', self.db.log_exception)
                if attempt < attempts-1:
                    sleep(30)
                else:
                    raise Exception(
                        'Error finding uart device after power cycle')
            else:
                break
        self.open()
        print(colored('Power cycled device: {}'.format(self.dut.serial.port),
                      'red'))
        event.success = True
        event.save()

    def halt_dut(self):
        super().halt_dut('halt', ['target halted']*2)

    def continue_dut(self):
        super().continue_dut('resume')

    def select_core(self, core):
        self.command('targets zynq.cpu{}'.format(core),
                     error_message='Error selecting core')

    def get_mode(self):
        cpsr = int(self.command(
            'reg cpsr', [':'], 'Error getting register value'
        ).split('\n')[1].split(':')[1].split()[0], base=16)
        return self.modes[str(bin(cpsr))[-5:]]

    def set_mode(self, mode='svc'):
        modes = {value: key for key, value in self.modes.items()}
        mask = modes[mode]
        cpsr = self.command(
            'reg cpsr', [':'], 'Error getting register value'
        ).split('\n')[1].split(':')[1].split()[0]
        cpsr = hex(int(str(bin(int(cpsr, base=16)))[:-5]+mask, base=2))
        self.command('reg cpsr {}'.format(cpsr),
                     error_message='Error setting register value')
        self.db.log_event(
            'Information', 'Debugger', 'Set processor mode', mode)

    def get_register_value(self, register_info):
        target = self.targets[register_info.target]
        if register_info.register_alias is None:
            register_name = register_info.register
        else:
            register_name = register_info.register_alias
        register = target['registers'][register_info.register]
        if 'type' in target and target['type'] == 'CP':
            buff = self.command('arm mrc {} {} {} {} {}'.format(
                register['CP'], register['Op1'], register['CRn'],
                register['CRm'], register['Op2']),
                error_message='Error getting register value')
            return hex(int(buff.split('\n')[1].strip()))
        else:
            buff = self.command('reg {}'.format(register_name), [':'],
                                'Error getting register value')
            return \
                buff.split('\n')[1].split(':')[1].split()[0]

    def set_register_value(self, register_info):
        target = self.targets[register_info.target]
        if register_info.register_alias is None:
            register_name = register_info.register
        else:
            register_name = register_info.register_alias
        register = target['registers'][register_info.register]
        value = register_info.injected_value
        if 'type' in target and target['type'] == 'CP':
            self.command('arm mrc {} {} {} {} {} {}'.format(
                register['CP'], register['Op1'], register['CRn'],
                register['CRm'], register['Op2'], value),
                error_message='Error setting register value')
        else:
            self.command('reg {} {}'.format(register_name, value),
                         error_message='Error setting register value')
