from __future__ import print_function
import sys
import telnetlib
import time
import random

from error import DrSEUSError


class bdi:
    # check debugger is ready and boot device
    def __init__(self, ip_address, dut, new, debug):
        self.output = ''
        try:
            self.telnet = telnetlib.Telnet(ip_address)
        except:
            print('could not connect to debugger')
            # TODO: killall telnet
            sys.exit()
        self.dut = dut
        if not self.ready():
            print('debugger not ready')
            sys.exit()
        if new:
            if not self.reset_dut():
                print('error resetting dut')
                sys.exit()

    def close(self):
        self.command('quit')
        self.telnet.close()

    def ready(self):
        if self.telnet.expect(self.prompts, timeout=10)[0] < 0:
            return False
        else:
            return True

    def reset_dut(self):
        try:
            if self.dut.is_logged_in():
                self.dut.command('sync')
        except DrSEUSError as error:
            if error.type == 'dut_hanging':
                pass
            else:
                raise DrSEUSError(error.type, error.console_buffer)
        self.telnet.write('reset\r\n')
        if self.telnet.expect(['- TARGET: processing target startup passed'],
                              timeout=10) < 0:
            return False
        else:
            return True

    def command(self, command):
        # TODO: make robust
        # self.debugger.read_very_eager()  # clear telnet buffer
        self.telnet.write(command+'\r\n')
        index, match, text = self.telnet.expect(self.prompts, timeout=10)
        if index < 0:
            return False
        else:
            return text

    def inject_fault(self, injection_time, command):
        self.dut.serial.write('./'+command+'\n')
        time.sleep(injection_time)
        if not self.halt_dut():
            print('error halting dut')
            sys.exit()
        regs = self.get_dut_regs()
        core_to_inject = random.randrange(2)
        reg_to_inject = random.choice(regs[core_to_inject].keys())
        value_to_inject = int(regs[core_to_inject][reg_to_inject], base=16)
        bit_to_inject = random.randrange(64)
        value_injected = value_to_inject ^ (1 << bit_to_inject)
        if self.debug:
            print('core to inject: ', core_to_inject)
            print('reg to inject: ', reg_to_inject)
            print('value to inject: ', hex(value_to_inject))
            print('injected value: ', hex(value_injected))
        self.command('select '+str(core_to_inject))
        self.command('rm '+reg_to_inject+' '+hex(value_injected))
        injection_data = {
            'time': injection_time,
            'core': core_to_inject,
            'register': reg_to_inject,
            'bit': bit_to_inject,
            'value': value_to_inject,
            'injected_value': value_injected,
        }
        return injection_data


class bdi_arm(bdi):
    def __init__(self, ip_address, dut, new=True, debug=False):
        self.prompts = ['A9#0>', 'A9#1>']
        bdi.__init__(self, ip_address, dut, new)

    def halt_dut(self):
        self.telnet.write('halt 3\r\n')
        for i in xrange(2):
            if self.telnet.expect(['- TARGET: core #0 has entered debug mode',
                                   '- TARGET: core #1 has entered debug mode'],
                                  timeout=10)[0] < 0:
                return False
        return True

    def continue_dut(self):
        self.telnet.write('cont 3\r\n')
        # TODO: check for prompt

    def select_core(self, core):
        # TODO: check if cores are running (not in debug mode)
        self.telnet.write('select '+str(core)+'\r\n')
        for i in xrange(6):
            if self.telnet.expect(['Core number', 'Core state',
                                   'Debug entry cause', 'Current PC',
                                   'Current CPSR', 'Current SPSR'],
                                  timeout=10)[0] < 0:
                return False
        # TODO: replace this with regular expressions for
        #       getting hexadecimals for above categories
        self.telnet.read_very_eager()
        return True

    def get_dut_regs(self):
        # TODO: get GPRs
        # TODO: check for unused registers ttbc? iaucfsr?
        regs = [{}, {}]
        for core in xrange(2):
            self.select_core(core)
            debug_reglist = self.command('rdump')
            for line in debug_reglist.split('\r\n')[:-1]:
                line = line.split(': ')
                register = line[0].strip()
                value = line[1].split(' ')[0].strip()
                regs[core][register] = value
        return regs


class bdi_p2020(bdi):
    def __init__(self, ip_address, dut, new=True, debug=False):
        self.prompts = ['P2020>']
        bdi.__init__(self, ip_address, dut, new)

    def halt_dut(self):
        self.telnet.write('halt 0 1\r\n')
        for i in xrange(2):
            if self.telnet.expect(['- TARGET: core #0 has entered debug mode',
                                   '- TARGET: core #1 has entered debug mode'],
                                  timeout=10)[0] < 0:
                return False
        return True

    def continue_dut(self):
        self.telnet.write('go 0 1\r\n')
        # TODO: check for prompt

    def select_core(self, core):
        # TODO: check if cores are running (not in debug mode)
        self.telnet.write('select '+str(core)+'\r\n')
        for i in xrange(8):
            if self.telnet.expect(['Target CPU', 'Core state',
                                   'Debug entry cause', 'Current PC',
                                   'Current CR', 'Current MSR', 'Current LR',
                                   'Current CCSRBAR'], timeout=10)[0] < 0:
                return False
        # TODO: replace this with regular expressions for
        #       getting hexadecimals for above categories
        self.telnet.read_very_eager()
        return True

    def get_dut_regs(self):
        regs = [{}, {}]
        for core in xrange(2):
            self.select_core(core)
            debug_reglist = self.command('rdump')
            for line in debug_reglist.split('\r\n')[:-1]:
                line = line.split(': ')
                register = line[0].strip()
                value = line[1].split(' ')[0].strip()
                regs[core][register] = value
        return regs
