from __future__ import print_function
import sys
import telnetlib
import time
import random
import sqlite3

from termcolor import colored

from dut import dut


class bdi:
    # check debugger is ready and boot device
    def __init__(self, ip_address, dut_ip_address, rsakey,
                 dut_serial_port, dut_prompt, debug):
        self.debug = debug
        # TODO: populate output
        self.output = ''
        try:
            self.telnet = telnetlib.Telnet(ip_address)
        except:
            print('could not connect to debugger')
            # TODO: killall telnet
            sys.exit()
        self.dut = dut(dut_ip_address, rsakey,
                       dut_serial_port, dut_prompt, debug)
        if not self.ready():
            print('debugger not ready')
            sys.exit()

    def close(self):
        self.command('quit')
        self.telnet.close()
        self.dut.close()

    def ready(self):
        if self.telnet.expect(self.prompts, timeout=10)[0] < 0:
            return False
        else:
            return True

    def reset_dut(self):
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

    def time_application(self, command, iterations):
        start = time.time()
        for i in xrange(iterations):
            self.dut.command('./'+command)
        return (time.time() - start) / iterations

    def inject_fault(self, injection_number, injection_time, command):
        if self.debug:
            print(colored('injection time: '+str(injection_time), 'blue'))
        self.dut.serial.write('./'+command+'\n')
        time.sleep(injection_time)
        if not self.halt_dut():
            print('error halting dut')
            sys.exit()
        regs = self.get_dut_regs()
        core = random.randrange(2)
        register = random.choice(regs[core].keys())
        gold_value = regs[core][register]
        num_bits = len(gold_value.replace('0x', '')) * 4
        bit = random.randrange(num_bits)
        injected_value = '0x%X' % (int(gold_value, base=16) ^ (1 << bit))
        if self.debug:
            print()
            print(colored('core: '+str(core), 'blue'))
            print(colored('register: '+register, 'blue'))
            print(colored('bit: '+str(bit), 'blue'))
            print(colored('gold value: '+gold_value, 'blue'))
            print(colored('injected value: '+injected_value, 'blue'))
        self.command('select '+str(core))
        self.command('rm '+register+' '+injected_value)
        sql_db = sqlite3.connect('campaign-data/db.sqlite3')
        sql = sql_db.cursor()
        sql.execute(
            'INSERT INTO drseus_logging_hw_injection ' +
            '(injection_number,register,bit,gold_value,injected_value,' +
            'time,core) VALUES (?,?,?,?,?,?,?)',
            (
                injection_number, register, bit, gold_value, injected_value,
                injection_time, core
            )
        )
        sql_db.commit()
        sql_db.close()


class bdi_arm(bdi):
    def __init__(self, ip_address, dut_ip_address, rsakey, dut_serial_port,
                 dut_prompt, debug):
        self.prompts = ['A9#0>', 'A9#1>']
        bdi.__init__(self, ip_address, dut_ip_address, rsakey, dut_serial_port,
                     dut_prompt, debug)

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
    def __init__(self, ip_address, dut_ip_address, rsakey, dut_serial_port,
                 dut_prompt, debug):
        self.prompts = ['P2020>']
        bdi.__init__(self, ip_address, dut_ip_address, rsakey, dut_serial_port,
                     dut_prompt, debug)

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
