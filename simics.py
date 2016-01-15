from __future__ import print_function
import os
from signal import SIGINT
import subprocess
import sys
from termcolor import colored
from threading import Thread
import time

from dut import dut
from error import DrSEUsError
import simics_checkpoints
from sql import sql


class simics:
    error_messages = ['Address not mapped', 'Illegal Instruction',
                      'Illegal instruction', 'Illegal memory mapping',
                      'Illegal Memory Mapping', 'Error setting attribute',
                      'dropping memop (peer attribute not set)',
                      'where nothing is mapped', 'Error']

    def __init__(self, campaign_number, architecture, rsakey, use_aux, debug,
                 timeout):
        self.simics = None
        self.output = ''
        self.campaign_number = campaign_number
        self.debug = debug
        self.timeout = timeout
        if architecture == 'p2020':
            self.board = 'p2020rdb'
        elif architecture == 'a9':
            self.board = 'a9x2'
        self.rsakey = rsakey
        self.use_aux = use_aux

    def __str__(self):
        string = 'Simics simulation of '+self.board
        return string

    def launch_simics(self, checkpoint=None):
        attempts = 10
        for attempt in xrange(attempts):
            self.simics = subprocess.Popen([os.getcwd()+'/simics-workspace/'
                                            'simics', '-no-win', '-no-gui',
                                            '-q'],
                                           cwd=os.getcwd()+'/simics-workspace',
                                           stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE)
            try:
                self.read_until()
            except DrSEUsError:
                self.simics.kill()
                print(colored('error launching simics (attempt ' +
                              str(attempt+1)+'/'+str(attempts)+')', 'red'))
                if attempt < attempts-1:
                    time.sleep(30)
                elif attempt == attempts-1:
                    raise Exception('error launching simics, check your '
                                    'license connection')
            else:
                break
        if checkpoint is None:
            self.command('$drseus=TRUE')
            buff = self.command('run-command-file simics-'+self.board+'/' +
                                self.board+'-linux'+('-ethernet' if
                                                     self.use_aux
                                                     else '') +
                                '.simics')
        else:
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
            self.close()
            raise DrSEUsError('Error finding port or pseudoterminal')
        if self.board == 'p2020rdb':
            prompt = 'root@p2020rdb:~#'
        elif self.board == 'a9x2':
            prompt = '#'
        self.dut = dut(self.rsakey, serial_ports[0], prompt, self.debug,
                       self.timeout, self.campaign_number, 38400, ssh_ports[0])
        if self.use_aux:
            self.aux = dut(self.rsakey, serial_ports[1], prompt, self.debug,
                           self.timeout, self.campaign_number, 38400,
                           ssh_ports[1], 'cyan')
        if checkpoint is None:
            self.continue_dut()
            self.do_uboot()
            if self.use_aux:
                aux_process = Thread(target=self.aux.do_login,
                                     kwargs={'ip_address': '10.10.0.104',
                                             'change_prompt': True,
                                             'simics': True})
                aux_process.start()
            self.dut.do_login(ip_address='10.10.0.100',
                              change_prompt=(prompt == '#'),
                              simics=True)
            if self.use_aux:
                aux_process.join()
        else:
            self.dut.ip_address = '127.0.0.1'
            if prompt == '#':
                self.dut.prompt = 'DrSEUs# '
            if self.use_aux:
                self.aux.ip_address = '127.0.0.1'
                if prompt == '#':
                    self.aux.prompt = 'DrSEUs# '

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
        try:
            self.dut.close()
            if self.use_aux:
                self.aux.close()
        except AttributeError:
            pass
        if self.simics:
            self.simics.send_signal(SIGINT)
            try:
                self.simics.stdin.write('quit\n')
            except IOError:
                pass

            def read_worker():
                try:
                    self.read_until()
                except DrSEUsError:
                    pass
            read_thread = Thread(target=read_worker)
            read_thread.start()
            read_thread.join(timeout=5)  # must be shorter than timeout in read
            if read_thread.is_alive():
                self.simics.kill()
                self.output += '\nkilled unresponsive simics process\n'
                if self.debug:
                    print(colored('killed unresponsive simics process',
                                  'yellow'))
            else:
                self.output += 'quit\n'
                if self.debug:
                    print(colored('quit', 'yellow'))
                self.simics.wait()
        self.simics = None

    def halt_dut(self):
        self.simics.send_signal(SIGINT)
        self.read_until()
        return True

    def continue_dut(self):
        self.simics.stdin.write('run\n')
        self.output += 'run\n'
        if self.debug:
            print(colored('run', 'yellow'))

    def read_char_worker(self):
        self.char = None
        self.char = self.simics.stdout.read(1).decode('utf-8', 'replace')

    def read_char(self):
        read_thread = Thread(target=self.read_char_worker)
        read_thread.start()
        read_thread.join(timeout=30)  # must be longer than timeout in close
        if read_thread.is_alive():
            raise DrSEUsError('Timeout reading from simics')
        return self.char

    def read_until(self, string=None):
        if string is None:
            string = 'simics> '
        buff = ''
        while True:
            char = self.read_char()
            if not char:
                break
            self.output += char
            if self.debug:
                print(colored(char, 'yellow'), end='')
                sys.stdout.flush()
            buff += char
            if buff[-len(string):] == string:
                break
        for message in self.error_messages:
            if message in buff:
                raise DrSEUsError(message)
        return buff

    def command(self, command):
        self.simics.stdin.write(command+'\n')
        self.output += command+'\n'
        if self.debug:
            print(colored(command, 'yellow'))
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

    def time_application(self, command, aux_command, timing_iterations,
                         kill_dut):
        num_cycles = 0
        self.halt_dut()
        start_cycles = self.command('print-time').split('\n')[-2].split()[2]
        start_time = time.time()
        self.continue_dut()
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
            self.halt_dut()
            end_cycles = self.command(
                'print-time').split('\n')[-2].split()[2]
            num_cycles += int(end_cycles) - int(start_cycles)
            start_cycles = end_cycles
            self.continue_dut()
        end_time = time.time()
        return ((end_time - start_time) / timing_iterations,
                int(num_cycles / timing_iterations))

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
        read_thread = Thread(target=self.dut.read_until)
        read_thread.start()
        checkpoint = 0
        while True:
            checkpoint += 1
            self.command('run-cycles '+str(step_cycles))
            self.dut.output += '***drseus_checkpoint: '+str(checkpoint)+'***\n'
            incremental_checkpoint = ('gold-checkpoints/' +
                                      str(self.campaign_number)+'/' +
                                      str(checkpoint))
            self.command('write-configuration '+incremental_checkpoint)
            if not read_thread.is_alive() or (self.use_aux and kill_dut
                                              and not aux_process.is_alive()):
                merged_checkpoint = incremental_checkpoint+'_merged'
                self.command('!bin/checkpoint-merge '+incremental_checkpoint +
                             ' '+merged_checkpoint)
                break
        self.continue_dut()
        if self.use_aux:
            aux_process.join()
        if kill_dut:
            self.dut.serial.write('\x03')
        read_thread.join()
        return step_cycles, checkpoint

    def inject_fault(self, result_id, checkpoints_to_inject, selected_targets,
                     cycles_between_checkpoints, num_checkpoints, compare_all):
        dut_output = ''
        if self.use_aux:
            aux_output = ''
        latent_faults = 0
        for injection_number in xrange(1, len(checkpoints_to_inject)+1):
            checkpoint_number = checkpoints_to_inject[injection_number-1]
            injected_checkpoint = simics_checkpoints.inject_checkpoint(
                self.campaign_number, result_id, injection_number,
                checkpoint_number, self.board, selected_targets, self.debug)
            self.launch_simics(injected_checkpoint)
            injections_remaining = (injection_number <
                                    len(checkpoints_to_inject))
            if injections_remaining:
                next_checkpoint = checkpoints_to_inject[injection_number]
            else:
                next_checkpoint = num_checkpoints
            errors = self.compare_checkpoints(result_id, checkpoint_number,
                                              next_checkpoint,
                                              cycles_between_checkpoints,
                                              num_checkpoints, compare_all)
            if errors > latent_faults:
                latent_faults = errors
            if injections_remaining:
                self.close()
            dut_output += self.dut.output
            if self.use_aux:
                aux_output += self.aux.output
        self.dut.output = dut_output
        if self.use_aux:
            self.aux.output = aux_output
        return latent_faults

    def regenerate_checkpoints(self, result_id, cycles_between, injection_data):
        for i in xrange(len(injection_data)):
            if i == 0:
                checkpoint = ('simics-workspace/gold-checkpoints/' +
                              str(self.campaign_number)+'/' +
                              str(injection_data[i]['checkpoint_number']))
            else:
                checkpoint = ('simics-workspace/injected-checkpoints/' +
                              str(self.campaign_number)+'/' +
                              str(result_id)+'/' +
                              str(injection_data[i]['checkpoint_number']))
            injected_checkpoint = ('simics-workspace/injected-checkpoints/' +
                                   str(self.campaign_number)+'/' +
                                   str(result_id)+'/' +
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
                             str(result_id)+'/' +
                             str(injection_data[i+1]['checkpoint_number']))
                self.close()
        return injected_checkpoint

    def compare_checkpoints(self, result_id, checkpoint_number, last_checkpoint,
                            cycles_between_checkpoints, num_checkpoints,
                            compare_all):
        reg_errors = 0
        mem_errors = 0
        for checkpoint_number in xrange(checkpoint_number + 1,
                                        last_checkpoint + 1):
            self.command('run-cycles '+str(cycles_between_checkpoints))
            incremental_checkpoint = ('injected-checkpoints/' +
                                      str(self.campaign_number)+'/' +
                                      str(result_id)+'/'+str(checkpoint_number))
            monitor = compare_all or checkpoint_number == num_checkpoints
            if monitor or checkpoint_number == last_checkpoint:
                self.command('write-configuration '+incremental_checkpoint)
            if monitor:
                monitored_checkpoint = incremental_checkpoint+'_merged'
                self.command('!bin/checkpoint-merge '+incremental_checkpoint +
                             ' '+monitored_checkpoint)
                # dev_null = open('/dev/null', 'w')
                # merge = subprocess.Popen([os.getcwd()+'/simics-workspace/'
                #                           '/bin/checkpoint-merge',
                #                           incremental_checkpoint,
                #                           monitored_checkpoint,
                #                           '--jobs', '4'],
                #                          cwd=(os.getcwd() +
                #                               '/simics-workspace'),
                #                          stdout=dev_null, stderr=dev_null)
                # if merge.wait():
                #     dev_null.close()
                #     raise DrSEUsError('Error merging checkpoint')
                # dev_null.close()
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
                    # dev_null = open('/dev/null', 'w')
                    # merge = subprocess.Popen([os.getcwd()+'/simics-workspace/'
                    #                           '/bin/checkpoint-merge',
                    #                           gold_incremental_checkpoint,
                    #                           gold_checkpoint, '--jobs', '4'],
                    #                          cwd=(os.getcwd() +
                    #                               '/simics-workspace'),
                    #                          stdout=dev_null, stderr=dev_null)
                    # if merge.wait():
                    #     dev_null.close()
                    #     raise DrSEUsError('Error merging checkpoint')
                    # dev_null.close()
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
        with sql(row_factory='row') as db:
            db.cursor.execute('SELECT config_object,register,register_index,'
                              'injected_value FROM log_injection '
                              'WHERE result_id=?', (result_id,))
            injections = db.cursor.fetchall()
            db.cursor.execute('SELECT * FROM log_simics_register_diff '
                              'WHERE result_id=?', (result_id,))
            register_diffs = db.cursor.fetchall()
            db.cursor.execute('SELECT * FROM log_simics_memory_diff '
                              'WHERE result_id=?', (result_id,))
            memory_diffs = db.cursor.fetchall()
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
