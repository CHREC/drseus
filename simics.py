from __future__ import print_function
import os
from signal import SIGINT
import sqlite3
import subprocess
from termcolor import colored
from threading import Thread
from time import time

from dut import dut
from error import DrSEUSError
import simics_checkpoints


class simics:
    error_messages = ['Address not mapped', 'Illegal Instruction',
                      'Illegal instruction', 'Illegal memory mapping',
                      'Illegal Memory Mapping',
                      'dropping memop (peer attribute not set)',
                      'where nothing is mapped', 'Error']

    # create simics instance and boot device
    def __init__(self, campaign_number, architecture, rsakey, use_aux, debug,
                 timeout):
        self.campaign_number = campaign_number
        self.debug = debug
        self.timeout = timeout
        if architecture == 'p2020':
            self.board = 'p2020rdb'
        elif architecture == 'a9':
            self.board = 'a9x2'
        self.rsakey = rsakey
        self.use_aux = use_aux

    def launch_simics(self, checkpoint=None):
        self.output = ''
        self.simics = subprocess.Popen([os.getcwd()+'/simics-workspace/simics',
                                        '-no-win', '-no-gui', '-q'],
                                       cwd=os.getcwd()+'/simics-workspace',
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE)
        self.read_until()
        if checkpoint is None:
            try:
                self.command('$drseus=TRUE')
                buff = self.command('run-command-file simics-'+self.board+'/' +
                                    self.board+'-linux'+('-ethernet' if
                                                         self.use_aux
                                                         else '') +
                                    '.simics')
            except IOError:
                raise Exception('lost contact with simics')
        else:
            self.injected_checkpoint = checkpoint
            buff = self.command('read-configuration '+checkpoint)
            buff += self.command('connect-real-network-port-in ssh '
                                 'ethernet_switch0 target-ip=10.10.0.100')
            if self.use_aux:
                buff += self.command('connect-real-network-port-in ssh '
                                     'ethernet_switch0 target-ip=10.10.0.104')
        found_settings = 0
        if checkpoint is None:
            serial_ports = []
        else:
            serial_ports = [0, 0]
        ssh_ports = []
        for line in buff.split('\n'):
            if 'pseudo device opened: /dev/pts/' in line:
                if checkpoint is None:
                    serial_ports.append(line.split(':')[1].strip())
                else:
                    if 'AUX_' in line:
                        serial_ports[1] = line.split(':')[1].strip()
                    else:
                        serial_ports[0] = line.split(':')[1].strip()
                found_settings += 1
            elif 'Host TCP port' in line:
                ssh_ports.append(int(line.split('->')[0].split(' ')[-2]))
                found_settings += 1
            if not self.use_aux and found_settings == 2:
                break
            elif self.use_aux and found_settings == 4:
                break
        else:
            raise Exception('could not find port or pseudoterminal to attach')
        if self.board == 'p2020rdb':
            self.dut = dut('127.0.0.1', self.rsakey, serial_ports[0],
                           'root@p2020rdb:~#', self.debug, self.timeout, 38400,
                           ssh_ports[0])
            if self.use_aux:
                self.aux = dut('127.0.0.1', self.rsakey, serial_ports[1],
                               'root@p2020rdb:~#', self.debug, self.timeout,
                               38400, ssh_ports[1], 'cyan')
        elif self.board == 'a9x2':
            self.dut = dut('127.0.0.1', self.rsakey, serial_ports[0],
                           '#', self.debug, self.timeout, 38400, ssh_ports[0])
            if self.use_aux:
                self.aux = dut('127.0.0.1', self.rsakey, serial_ports[1],
                               '#', self.debug, self.timeout, 38400,
                               ssh_ports[1], 'cyan')
        if checkpoint is None:
            self.continue_dut()
            self.do_uboot()
            if self.use_aux:
                def aux_login():
                    self.aux.do_login(change_prompt=True)
                    self.aux.command('ifconfig eth0 10.10.0.104 '
                                     'netmask 255.255.255.0 up')
                    self.aux.read_until()
                aux_process = Thread(target=aux_login)
                aux_process.start()
            self.dut.do_login(change_prompt=True)
            self.dut.command('ifconfig eth0 10.10.0.100 '
                             'netmask 255.255.255.0 up')
            self.dut.read_until()
            if self.use_aux:
                aux_process.join()
        else:
            self.dut.prompt = 'DrSEUS# '
            if self.use_aux:
                self.aux.prompt = 'DrSEUS# '

    def launch_simics_gui(self, checkpoint):
        dut_board = 'DUT_'+self.board
        if self.board == 'p2020rdb':
            serial_port = 'serial[0]'
        elif self.board == 'a9x2':
            serial_port = 'serial0'
        simics_commands = ('read-configuration '+checkpoint+';'
                           'new-text-console-comp text_console0;'
                           'disconnect '+dut_board+'.console0.serial'
                           ' '+dut_board+'.'+serial_port+';'
                           'connect text_console0.serial'
                           ' '+dut_board+'.'+serial_port+';'
                           'connect-real-network-port-in ssh '
                           'ethernet_switch0 target-ip=10.10.0.100;')
        if self.use_aux:
            aux_board = 'AUX_'+self.board+'_1'
            simics_commands += ('new-text-console-comp text_console1;'
                                'disconnect '+aux_board+'.console0.serial'
                                ' '+aux_board+'.'+serial_port+';'
                                'connect text_console1.serial'
                                ' '+aux_board+'.'+serial_port+';'
                                'connect-real-network-port-in ssh '
                                'ethernet_switch0 target-ip=10.10.0.104;')
        os.system('cd simics-workspace; '
                  './simics-gui -e \"'+simics_commands+'\"')

    def close(self):
        self.dut.close()
        if self.use_aux:
            self.aux.close()
        self.simics.send_signal(SIGINT)
        self.simics.stdin.write('quit\n')
        read_thread = Thread(target=self.read_until)
        read_thread.start()
        read_thread.join(timeout=30)
        if read_thread.is_alive():
            self.simics.kill()
            raise DrSEUSError('Simics close error')
        self.output += 'quit'+'\n'
        if self.debug:
            print(colored('quit'+'\n', 'yellow'), end='')
        self.simics.wait()

    def halt_dut(self):
        self.simics.send_signal(SIGINT)
        self.read_until()
        return True

    def continue_dut(self):
        self.simics.stdin.write('run\n')
        self.output += 'run\n'
        if self.debug:
            print(colored('run\n', 'yellow'), end='')

    def read_until(self, string=None):
        # TODO: add timeout
        if string is None:
            string = 'simics> '
        buff = ''
        while True:
            char = self.simics.stdout.read(1)
            if not char:
                break
            self.output += char
            if self.debug:
                print(colored(char, 'yellow'), end='')
            buff += char
            if buff[-len(string):] == string:
                break
        for message in self.error_messages:
            if message in buff:
                raise DrSEUSError(message)
        return buff

    def command(self, command):
        self.simics.stdin.write(command+'\n')
        self.output += command+'\n'
        if self.debug:
            print(colored(command+'\n', 'yellow'), end='')
        return self.read_until()

    def do_uboot(self):
        if self.use_aux:
            def stop_aux_boot():
                self.aux.read_until('autoboot: ')
                self.aux.serial.write('\n')
            aux_process = Thread(target=stop_aux_boot)
            aux_process.start()
        self.dut.read_until('autoboot: ')
        self.dut.serial.write('\n')
        if self.use_aux:
            aux_process.join()
        self.halt_dut()
        if self.board == 'p2020rdb':
            self.command('DUT_p2020rdb.soc.phys_mem.load-file '
                         '$initrd_image $initrd_addr')
            if self.use_aux:
                self.command('AUX_p2020rdb_1.soc.phys_mem.load-file '
                             '$initrd_image $initrd_addr')
            self.continue_dut()
            self.dut.serial.write('setenv ethaddr 00:01:af:07:9b:8a\n'
                                  'setenv eth1addr 00:01:af:07:9b:8b\n'
                                  'setenv eth2addr 00:01:af:07:9b:8c\n'
                                  'setenv consoledev ttyS0\n'
                                  'setenv bootargs root=/dev/ram rw '
                                  'console=$consoledev,$baudrate\n'
                                  'bootm ef080000 10000000 ef040000\n')
            if self.use_aux:
                self.aux.serial.write('setenv ethaddr 00:01:af:07:9b:8d\n'
                                      'setenv eth1addr 00:01:af:07:9b:8e\n'
                                      'setenv eth2addr 00:01:af:07:9b:8f\n'
                                      'setenv consoledev ttyS0\n'
                                      'setenv bootargs root=/dev/ram rw '
                                      'console=$consoledev,$baudrate\n'
                                      'bootm ef080000 10000000 ef040000\n')
        elif self.board == 'a9x2':
            self.command('DUT_a9x2.coretile.mpcore.phys_mem.load-file '
                         '$kernel_image $kernel_addr')
            self.command('DUT_a9x2.coretile.mpcore.phys_mem.load-file '
                         '$initrd_image $initrd_addr')
            if self.use_aux:
                self.command('AUX_a9x2_1.coretile.mpcore.phys_mem.load-file '
                             '$kernel_image $kernel_addr')
                self.command('AUX_a9x2_1.coretile.mpcore.phys_mem.load-file '
                             '$initrd_image $initrd_addr')
            self.continue_dut()
            self.dut.read_until('VExpress# ')
            self.dut.serial.write('setenv bootargs console=ttyAMA0 '
                                  'root=/dev/ram0 rw\n')
            self.dut.read_until('VExpress# ')
            self.dut.serial.write('bootm 0x40800000 0x70000000\n')
            # TODO: remove these after fixing command prompt of simics arm
            self.dut.read_until('##')
            self.dut.read_until('##')
            if self.use_aux:
                self.aux.read_until('VExpress# ')
                self.aux.serial.write('setenv bootargs console=ttyAMA0 '
                                      'root=/dev/ram0 rw\n')
                self.aux.read_until('VExpress# ')
                self.aux.serial.write('bootm 0x40800000 0x70000000\n')
                # TODO: remove these after fixing command prompt of simics arm
                self.aux.read_until('##')
                self.aux.read_until('##')

    def calculate_cycles(self, command, aux_command, kill_dut):
        self.halt_dut()
        start_cycles = self.command(
            'print-time').split('\n')[-2].split()[2]
        self.continue_dut()
        self.time_application(command, aux_command, 1, kill_dut)
        self.halt_dut()
        end_cycles = self.command(
            'print-time').split('\n')[-2].split()[2]
        self.continue_dut()
        return int(end_cycles) - int(start_cycles)

    def time_application(self, command, aux_command, iterations, kill_dut):
        start = time()
        for i in xrange(iterations):
            if self.use_aux:
                aux_process = Thread(target=self.aux.command,
                                     args=('./'+aux_command, ))
                aux_process.start()
            self.dut.serial.write('./'+command+'\n')
            if self.use_aux:
                aux_process.join()
            if kill_dut:
                self.dut.serial.write('\x03')
            self.dut.read_until()
        end = time()
        return (end - start) / iterations

    def create_checkpoints(self, command, aux_command, cycles, num_checkpoints,
                           kill_dut):
        os.makedirs('simics-workspace/gold-checkpoints/' +
                    str(self.campaign_number))
        step_cycles = cycles / num_checkpoints
        self.halt_dut()
        if self.use_aux:
                aux_process = Thread(target=self.aux.command,
                                     args=('./'+aux_command, ))
                aux_process.start()
        self.dut.serial.write('./'+command+'\n')
        for checkpoint in xrange(num_checkpoints):
            self.command('run-cycles '+str(step_cycles))
            incremental_checkpoint = ('gold-checkpoints/' +
                                      str(self.campaign_number)+'/' +
                                      str(checkpoint))
            self.command('write-configuration '+incremental_checkpoint)
            merged_checkpoint = incremental_checkpoint+'_merged'
            if checkpoint == num_checkpoints-1:
                self.command('!bin/checkpoint-merge '+incremental_checkpoint +
                             ' '+merged_checkpoint)
        self.continue_dut()
        if self.use_aux:
            aux_process.join()
        if kill_dut:
            self.dut.serial.write('\x03')
        self.dut.read_until()
        self.close()
        return step_cycles

    def inject_fault(self, result_id, iteration, checkpoints_to_inject,
                     selected_targets, cycles_between_checkpoints,
                     num_checkpoints, compare_all):
        simics_output = ''
        dut_output = ''
        paramiko_output = ''
        if self.use_aux:
            aux_output = ''
            aux_paramiko_output = ''
        latent_faults = 0
        for injection_number in xrange(len(checkpoints_to_inject)):
            checkpoint_number = checkpoints_to_inject[injection_number]
            injected_checkpoint = simics_checkpoints.inject_checkpoint(
                self.campaign_number, result_id, iteration, injection_number,
                checkpoint_number, self.board, selected_targets, self.debug)
            self.launch_simics(checkpoint=injected_checkpoint)
            injections_remaining = (injection_number + 1 <
                                    len(checkpoints_to_inject))
            if injections_remaining:
                next_checkpoint = checkpoints_to_inject[injection_number + 1]
            else:
                next_checkpoint = num_checkpoints
            errors = self.compare_checkpoints(result_id, iteration,
                                              checkpoint_number,
                                              next_checkpoint,
                                              cycles_between_checkpoints,
                                              num_checkpoints, compare_all)
            if errors > latent_faults:
                latent_faults = errors
            if injections_remaining:
                self.close()
            simics_output += self.output
            dut_output += self.dut.output
            paramiko_output += self.dut.paramiko_output
            if self.use_aux:
                aux_output += self.aux.output
                aux_paramiko_output += self.aux.paramiko_output
        self.output = simics_output
        self.dut.output = dut_output
        self.dut.paramiko_output = paramiko_output
        if self.use_aux:
            self.aux.output = aux_output
            self.aux.paramiko_output = aux_paramiko_output
        return latent_faults

    def regenerate_checkpoints(self, iteration, cycles_between, injection_data):
        for i in xrange(len(injection_data)):
            if i == 0:
                checkpoint = ('simics-workspace/gold-checkpoints/' +
                              str(self.campaign_number)+'/' +
                              str(injection_data[i]['checkpoint_number']))
            else:
                checkpoint = ('simics-workspace/injected-checkpoints/' +
                              str(self.campaign_number)+'/' +
                              str(iteration)+'/' +
                              str(injection_data[i]['checkpoint_number']))
            injected_checkpoint = ('simics-workspace/injected-checkpoints/' +
                                   str(self.campaign_number)+'/' +
                                   str(iteration)+'/' +
                                   str(injection_data[i]['checkpoint_number']) +
                                   '_injected')
            os.makedirs(injected_checkpoint)
            injected_checkpoint = \
                simics_checkpoints.regenerate_injected_checkpoint(
                    self.board, checkpoint, injected_checkpoint,
                    injection_data[i])
            if i < len(injection_data) - 1:
                self.launch_simics(checkpoint=injected_checkpoint)
                for j in xrange(injection_data[i]['checkpoint_number'],
                                injection_data[i+1]['checkpoint_number']):
                    self.command('run-cycles '+str(cycles_between))
                self.command('write-configuration injected-checkpoints/' +
                             str(self.campaign_number)+'/' +
                             str(iteration)+'/' +
                             str(injection_data[i+1]['checkpoint_number']))
                self.close()
        return injected_checkpoint

    def compare_checkpoints(self, result_id, iteration, checkpoint_number,
                            last_checkpoint, cycles_between_checkpoints,
                            num_checkpoints, compare_all):
        reg_errors = 0
        mem_errors = 0
        for checkpoint_number in xrange(checkpoint_number + 1,
                                        last_checkpoint + 1):
            self.command('run-cycles '+str(cycles_between_checkpoints))
            incremental_checkpoint = ('injected-checkpoints/' +
                                      str(self.campaign_number)+'/' +
                                      str(iteration)+'/'+str(checkpoint_number))
            monitor = compare_all or checkpoint_number == num_checkpoints - 1
            if monitor or checkpoint_number == last_checkpoint:
                self.command('write-configuration '+incremental_checkpoint)
            if monitor:
                monitored_checkpoint = incremental_checkpoint+'_merged'
                self.command('!bin/checkpoint-merge '+incremental_checkpoint +
                             ' '+monitored_checkpoint)
                gold_incremental_checkpoint = ('gold-checkpoints/' +
                                               str(self.campaign_number)+'/' +
                                               str(checkpoint_number))
                gold_checkpoint = ('gold-checkpoints/' +
                                   str(self.campaign_number)+'/' +
                                   str(checkpoint_number)+'_merged')
                if not os.path.exists('simics-workspace/'+gold_checkpoint):
                    self.command('!bin/checkpoint-merge ' +
                                 gold_incremental_checkpoint+' ' +
                                 gold_checkpoint)
                gold_checkpoint = 'simics-workspace/'+gold_checkpoint
                monitored_checkpoint = 'simics-workspace/'+monitored_checkpoint
                errors = simics_checkpoints.compare_registers(
                    result_id, checkpoint_number, gold_checkpoint,
                    monitored_checkpoint, self.board)
                if errors > reg_errors:
                    reg_errors = errors
                errors = simics_checkpoints.compare_memory(
                    result_id, checkpoint_number, gold_checkpoint,
                    monitored_checkpoint, self.board)
                if errors > reg_errors:
                    mem_errors = errors
        return reg_errors + mem_errors

    def persistent_faults(self, result_id):
        sql_db = sqlite3.connect('campaign-data/db.sqlite3')
        sql_db.row_factory = sqlite3.Row
        sql = sql_db.cursor()
        sql.execute('SELECT config_object,register,register_index,'
                    'injected_value FROM drseus_logging_injection WHERE '
                    'result_id=?', (result_id,))
        injections = sql.fetchall()
        sql.execute('SELECT * FROM drseus_logging_simics_register_diff WHERE '
                    'result_id=?', (result_id,))
        register_diffs = sql.fetchall()
        sql.execute('SELECT * FROM drseus_logging_simics_memory_diff WHERE '
                    'result_id=?', (result_id,))
        memory_diffs = sql.fetchall()
        sql_db.close()
        if len(memory_diffs) > 0:
            return False
        for register_diff in register_diffs:
            for injection in injections:
                if injection['register_index']:
                    injected_register = (injection['register']+':' +
                                         injection['register_index'])
                else:
                    injected_register = injection['register']
                if (register_diff['config_object'] == injection['config_object']
                        and register_diff['register'] == injected_register):
                    if (int(register_diff['monitored_value'], base=0) ==
                            int(injection['injected_value'], base=0)):
                        break
            else:
                return False
        else:
            return True
