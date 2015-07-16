from __future__ import print_function
import sys
import telnetlib
import time
import random
import sqlite3
import threading

from termcolor import colored

from dut import dut
from error import DrSEUSError


class bdi:
    # check debugger is ready and boot device
    def __init__(self, ip_address, dut_ip_address, rsakey, dut_serial_port,
                 aux_ip_address, aux_serial_port, use_aux, dut_prompt, debug,
                 timeout):
        self.timeout = 30
        self.debug = debug
        self.use_aux = use_aux
        # TODO: populate output
        self.output = ''
        try:
            self.telnet = telnetlib.Telnet(ip_address, timeout=self.timeout)
            self.command('', error_message='Debugger not ready')
        except:
            print('could not connect to debugger')
            # TODO: killall telnet
            sys.exit()
        self.dut = dut(dut_ip_address, rsakey,
                       dut_serial_port, dut_prompt, debug, timeout)
        if self.use_aux:
            self.aux = dut(aux_ip_address, rsakey, aux_serial_port,
                           'root@p2020rdb:~#', debug, timeout, color='cyan')

    def close(self):
        self.telnet.write('quit\r')
        self.telnet.close()
        self.dut.close()
        if self.use_aux:
            self.aux.close()

    def reset_dut(self):
        self.command('reset', ['- TARGET: processing target startup passed'],
                     'Error resetting DUT')

    def command(self, command, expected_output=[], error_message=None):
        return_buffer = ''
        if error_message is None:
            error_message = command
        buff = self.telnet.read_very_lazy()
        self.output += buff
        if self.debug:
            print(colored(buff, 'yellow'))
        if command:
            command = command+'\r'
            # for i in xrange(2):
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
            print (colored(buff, 'yellow'), end='')
            if index < 0:
                raise DrSEUSError(error_message)
        else:
            print()
        index, match, buff = self.telnet.expect(self.prompts,
                                                timeout=self.timeout)
        self.output += buff
        return_buffer += buff
        print(colored(buff, 'yellow'))
        if index < 0:
            raise DrSEUSError(error_message)
        return return_buffer

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
            self.halt_dut()
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
            self.select_core(core)
            self.command('rm '+register+' '+injected_value)
            self.command('rd '+register)
            sql_db = sqlite3.connect('campaign-data/db.sqlite3')
            sql = sql_db.cursor()
            sql.execute(
                'INSERT INTO drseus_logging_injection '
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
        self.command('halt 3', ['- TARGET: core #0 has entered debug mode',
                                '- TARGET: core #1 has entered debug mode'],
                     'Error halting DUT')

    def continue_dut(self):
        self.command('cont 3', error_message='Error continuing DUT')

    def select_core(self, core):
        # TODO: check if cores are running (not in debug mode)
        self.command('select '+str(core), ['Core number', 'Core state',
                                           'Debug entry cause', 'Current PC',
                                           'Current CPSR', 'Current SPSR'],
                     'Error selecting core')

    def get_dut_regs(self, selected_targets):
        # TODO: get GPRs
        # TODO: check for unused registers ttbc? iaucfsr?
        regs = [{}, {}]
        for core in xrange(2):
            self.select_core(core)
            debug_reglist = self.command('rdump')
            for line in debug_reglist.split('\r')[:-1]:
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
        self.command('halt 0; halt 1', ['Target CPU', 'Core state',
                                        'Debug entry cause', 'Current PC',
                                        'Current CR', 'Current MSR',
                                        'Current LR']*2,
                     'Error halting DUT')

    def continue_dut(self):
        self.command('go 0 1', error_message='Error continuing DUT')

    def select_core(self, core):
        # TODO: check if cores are running (not in debug mode)
        self.command('select '+str(core), ['Target CPU', 'Core state',
                                           'Debug entry cause', 'Current PC',
                                           'Current CR', 'Current MSR',
                                           'Current LR', 'Current CCSRBAR'],
                     'Error selecting core')

    def get_dut_regs(self, selected_targets):
        regs = [{}, {}]
        for core in xrange(2):
            self.select_core(core)
            debug_reglist = self.command('rdump',
                                         error_message='Error getting register '
                                                       'values')
            for line in debug_reglist.split('\r')[:-2]:
                line = line.split(': ')
                register = line[0].strip()
                if selected_targets is None:
                    try:
                        value = line[1].split(' ')[0].strip()
                    except:
                        print(line)
                    regs[core][register] = value
                else:
                    for target in selected_targets:
                        if target in register:
                            value = line[1].split(' ')[0].strip()
                            regs[core][register] = value
                            break
        return regs
