from __future__ import print_function
import sys
import telnetlib
import time
import random
import sqlite3
import threading

from termcolor import colored

from dut import dut


class bdi:
    # check debugger is ready and boot device
    def __init__(self, ip_address, dut_ip_address, rsakey, dut_serial_port,
                 aux_ip_address, aux_serial_port, use_aux, dut_prompt, debug,
                 timeout):
        self.debug = debug
        self.use_aux = use_aux
        # TODO: populate output
        self.output = ''
        try:
            self.telnet = telnetlib.Telnet(ip_address)
        except:
            print('could not connect to debugger')
            # TODO: killall telnet
            sys.exit()
        self.dut = dut(dut_ip_address, rsakey,
                       dut_serial_port, dut_prompt, debug, timeout)
        if self.use_aux:
            self.aux = dut(aux_ip_address, rsakey, aux_serial_port,
                           'root@p2020rdb:~#', debug, timeout, color='cyan')
        if not self.ready():
            print('debugger not ready')
            sys.exit()

    def close(self):
        self.telnet.write('quit\r\n')
        self.telnet.close()
        self.dut.close()
        if self.use_aux:
            self.aux.close()

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

    def time_application(self, command, aux_command, iterations):
        start = time.time()
        for i in xrange(iterations):
            if self.use_aux:
                aux_process = threading.Thread(target=self.aux.command,
                                               args=('./'+aux_command, ))
                aux_process.start()
            self.dut.command('./'+command)
            end = time.time()
            if self.use_aux:
                aux_process.join()
        return (end - start) / iterations

    def inject_fault(self, iteration, injection_times, command,
                     selected_targets):
        for injection in xrange(len(injection_times)):
            injection_time = injection_times[injection]
            if self.debug:
                print(colored('injection time: '+str(injection_time),
                              'magenta'))
            if injection == 0:
                self.dut.serial.write('./'+command+'\n')
            else:
                self.continue_dut()
            time.sleep(injection_time)
            if not self.halt_dut():
                print('error halting dut')
                sys.exit()
            regs = self.get_dut_regs(selected_targets)
            core = random.randrange(2)
            register = random.choice(regs[core].keys())
            gold_value = regs[core][register]
            num_bits = len(gold_value.replace('0x', '')) * 4
            bit = random.randrange(num_bits)
            injected_value = '0x%x' % (int(gold_value, base=16) ^ (1 << bit))
            if self.debug:
                print(colored('core: '+str(core), 'magenta'))
                print(colored('register: '+register, 'magenta'))
                print(colored('bit: '+str(bit), 'magenta'))
                print(colored('gold value: '+gold_value, 'magenta'))
                print(colored('injected value: '+injected_value, 'magenta'))
            self.command('select '+str(core))
            self.command('rm '+register+' '+injected_value)
            sql_db = sqlite3.connect('campaign-data/db.sqlite3')
            sql = sql_db.cursor()
            sql.execute(
                'INSERT INTO drseus_logging_hw_injection '
                '(result_id,injection_number,register,bit,gold_value,'
                'injected_value,time,time_rounded,core) VALUES '
                '(?,?,?,?,?,?,?,?,?)',
                (
                    iteration, injection, register, bit, gold_value,
                    injected_value, injection_time, round(injection_time, 1),
                    core
                )
            )
            sql_db.commit()
            sql_db.close()


class bdi_arm(bdi):
    def __init__(self, ip_address, dut_ip_address, rsakey, dut_serial_port,
                 aux_ip_address, aux_serial_port, use_aux, dut_prompt, debug,
                 timeout):
        self.prompts = ['A9#0>', 'A9#1>']
        bdi.__init__(self, ip_address, dut_ip_address, rsakey, dut_serial_port,
                     aux_ip_address, aux_serial_port, use_aux, dut_prompt,
                     debug, timeout)

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

    def get_dut_regs(self, selected_targets):
        # TODO: get GPRs
        # TODO: check for unused registers ttbc? iaucfsr?
        regs = [{}, {}]
        for core in xrange(2):
            self.select_core(core)
            debug_reglist = self.command('rdump')
            for line in debug_reglist.split('\r\n')[:-1]:
                line = line.split(': ')
                register = line[0].strip()
                if selected_targets is None:
                    value = line[1].split(' ')[0].strip()
                    regs[core][register] = value
                else:
                    for target in selected_targets:
                        if target in register:
                            value = line[1].split(' ')[0].strip()
                            regs[core][register] = value
                            break
        return regs


class bdi_p2020(bdi):
    def __init__(self, ip_address, dut_ip_address, rsakey, dut_serial_port,
                 aux_ip_address, aux_serial_port, use_aux, dut_prompt, debug,
                 timeout):
        self.prompts = ['P2020>']
        bdi.__init__(self, ip_address, dut_ip_address, rsakey, dut_serial_port,
                     aux_ip_address, aux_serial_port, use_aux, dut_prompt,
                     debug, timeout)

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

    def get_dut_regs(self, selected_targets):
        regs = [{}, {}]
        for core in xrange(2):
            self.select_core(core)
            debug_reglist = self.command('rdump')
            for line in debug_reglist.split('\r\n')[:-1]:
                line = line.split(': ')
                register = line[0].strip()
                if selected_targets is None:
                    value = line[1].split(' ')[0].strip()
                    regs[core][register] = value
                else:
                    for target in selected_targets:
                        if target in register:
                            value = line[1].split(' ')[0].strip()
                            regs[core][register] = value
                            break
        return regs
