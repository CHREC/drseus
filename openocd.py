from __future__ import print_function
from datetime import datetime
from telnetlib import Telnet
from termcolor import colored
from threading import Thread
import time
import random
from signal import SIGINT
import sqlite3
import subprocess

from dut import dut
from error import DrSEUsError
from sql import insert_dict


class openocd:
    error_messages = ['timeout while waiting for halt',
                      'wrong state for requested command', 'read access failed']

    def __init__(self, ip_address, dut_ip_address, rsakey, dut_serial_port,
                 aux_ip_address, aux_serial_port, use_aux, dut_prompt,
                 aux_prompt, debug, timeout):
        self.timeout = 30
        self.openocd = subprocess.Popen(['openocd',
                                         '-f', 'board/digilent_zedboard.cfg'],
                                        cwd='/usr/share/openocd/scripts',
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        time.sleep(5)
        self.telnet = Telnet('127.0.0.1', 4444, timeout=self.timeout)
        self.prompts = ['>']
        # TODO: ttb1 cannot inject into bits 2, 8, 9, 11
        self.registers = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7', 'r8',
                          'r9', 'r10', 'r11', 'r12',  # 'r13', 'r14',
                          'pc', 'cpsr',
                          'sp', 'lr',
                          # 'spsr', 'mainid', 'cachetype', 'tcmstatus',
                          # 'tlbtype', 'mputype', 'multipid', 'procfeature0',
                          # 'procfeature1', 'dbgfeature0', auxfeature0',
                          # 'memfeature0', 'memfeature1', 'memfeature2',
                          # 'memfeature3', 'instrattr0', 'instrattr1',
                          # 'instrattr2', 'instrattr3', 'instrattr4',
                          # 'instrattr5', 'instrattr6', 'instrattr7', 'control',
                          # 'auxcontrol', 'cpaccess', 'securecfg', 'securedbg',
                          # 'nonsecure',
                          # 'ttb0', 'ttb1',  # 'ttbc',
                          # 'dac',  # 'dfsr', 'ifsr', 'dauxfsr', 'iaucfsr',
                          # 'dfar', 'ifar',  # 'fcsepid',
                          # 'context'
                          ]
        self.debug = debug
        self.use_aux = use_aux
        self.output = ''
        self.dut = dut(dut_ip_address, rsakey,
                       dut_serial_port, dut_prompt, debug, timeout)
        if self.use_aux:
            self.aux = dut(aux_ip_address, rsakey, aux_serial_port,
                           aux_prompt, debug, timeout, color='cyan')
        else:
            self.aux = None
        self.command('', error_message='Debugger not ready')

    def set_rsakey(self, rsakey):
        self.dut.rsakey = rsakey
        if self.aux is not None:
            self.aux.rsakey = rsakey

    def close(self):
        self.telnet.write('shutdown\n')
        self.telnet.close()
        self.openocd.send_signal(SIGINT)
        self.openocd.wait()
        self.dut.close()
        if self.use_aux:
            self.aux.close()

    def command(self, command, expected_output=[], error_message=None):
        return_buffer = ''
        if error_message is None:
            error_message = command
        buff = self.telnet.read_very_lazy()
        self.output += buff
        if self.debug:
            print(colored(buff, 'yellow'))
        if command:
            command = command+'\n'
            self.telnet.write(command)
        for i in xrange(len(expected_output)):
            index, match, buff = self.telnet.expect(expected_output,
                                                    timeout=self.timeout)
            self.output += buff
            return_buffer += buff
            print(colored(buff, 'yellow'), end='')
            if index < 0:
                raise DrSEUsError(error_message)
        else:
            print()
        index, match, buff = self.telnet.expect(self.prompts,
                                                timeout=self.timeout)
        self.output += buff
        return_buffer += buff
        print(colored(buff, 'yellow'))
        if index < 0:
            raise DrSEUsError(error_message)
        for message in self.error_messages:
            if message in buff:
                raise DrSEUsError(error_message)
        return return_buffer

    def time_application(self, command, aux_command, iterations, kill_dut):
        start = time.time()
        for i in xrange(iterations):
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
        return (end - start) / iterations, None

    def inject_fault(self, result_id, iteration, injection_times, command,
                     selected_targets):
        if selected_targets is None:
            registers = self.registers
        else:
            registers = []
            for register in self.registers:
                for target in selected_targets:
                    if target in register:
                        registers.append(register)
                        break
        for injection in xrange(1, len(injection_times)+1):
            injection_data = {'result_id': result_id,
                              'injection_number': injection,
                              'time': injection_times[injection-1],
                              'timestamp': datetime.now()}
            if self.debug:
                print(colored('injection time: '+str(injection_data['time']),
                              'magenta'))
            if injection == 1:
                self.dut.serial.write(str('./'+command+'\n'))
            else:
                self.continue_dut()
            time.sleep(injection_data['time'])
            self.halt_dut()
            injection_data['core'] = random.randrange(2)
            self.select_core(injection_data['core'])
            injection_data['register'] = random.choice(self.registers)
            injection_data['gold_value'] = self.get_register_value(
                injection_data['register'])
            num_bits = len(injection_data['gold_value'].replace('0x', '')) * 4
            injection_data['bit'] = random.randrange(num_bits)
            injection_data['injected_value'] = '0x%x' % (
                int(injection_data['gold_value'], base=16)
                ^ (1 << injection_data['bit']))
            if self.debug:
                print(colored('core: '+str(injection_data['core']), 'magenta'))
                print(colored('register: '+injection_data['register'],
                              'magenta'))
                print(colored('bit: '+str(injection_data['bit']), 'magenta'))
                print(colored('gold value: '+injection_data['gold_value'],
                              'magenta'))
                print(colored('injected value: ' +
                              injection_data['injected_value'], 'magenta'))
            self.set_register_value(injection_data['register'],
                                    injection_data['injected_value'])
            sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
            sql = sql_db.cursor()
            insert_dict(sql, 'injection', injection_data)
            sql_db.commit()
            sql_db.close()
            if int(injection_data['injected_value'], base=16) != int(
                    self.get_register_value(injection_data['register']),
                    base=16):
                raise DrSEUsError('Error injecting fault')

    def reset_dut(self):
        if self.telnet:
            self.command('reset', error_message='Error resetting DUT')
        else:
            self.dut.serial.write('\x03')
        self.dut.do_login()

    def halt_dut(self):
        self.command('halt',  # 'targets zynq.cpu0; halt; targets zynq.cpu1; halt;',
                     ['target state: halted',
                      'target halted in ARM state due to debug-request,'
                      ' current mode:', 'cpsr:', 'MMU:']*2,
                     'Error halting DUT')

    def continue_dut(self):
        self.command('resume',  # 'targets zynq.cpu0; resume; targets zynq.cpu1; resume;',
                     # ['dscr'],
                     error_message='Error continuing DUT')

    def select_core(self, core):
        # self.command('targets zynq.cpu'+str(core),
        #              error_message='Error selecting core')
        pass

    def get_register_value(self, register):
        buff = self.command('reg '+register, [':'],
                            error_message='Error getting register value')
        return buff.split('\n')[1].split(':')[1].strip().split(' ')[0].strip()

    def set_register_value(self, register, value):
        self.command('reg '+register+' '+value, error_message='Error setting '
                                                              'register value')
