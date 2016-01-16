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

    def __init__(self, campaign_data, result_data, options, rsakey):
        self.simics = None
        self.campaign_data = campaign_data  # TODO: only used for id and use_aux
        self.result_data = result_data
        self.options = options
        if campaign_data['architecture'] == 'p2020':
            self.board = 'p2020rdb'
        elif campaign_data['architecture'] == 'a9':
            self.board = 'a9x2'
        self.rsakey = rsakey

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
            buff = self.command(
                'run-command-file simics-'+self.board+'/'+self.board+'-linux' +
                ('-ethernet' if self.campaign_data['use_aux'] else '') +
                '.simics')
        else:
            buff = self.command('read-configuration '+checkpoint)
            buff += self.command('connect-real-network-port-in ssh '
                                 'ethernet_switch0 target-ip=10.10.0.100')
            if self.campaign_data['use_aux']:
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
            if not self.campaign_data['use_aux'] and found_settings == 2:
                break
            elif self.campaign_data['use_aux'] and found_settings == 4:
                break
        else:
            self.close()
            raise DrSEUsError('Error finding port or pseudoterminal')
        if self.board == 'p2020rdb':
            self.options.aux_prompt = self.options.dut_prompt = \
                'root@p2020rdb:~#'
        elif self.board == 'a9x2':
            self.options.aux_prompt = self.options.dut_prompt = '#'
        self.options.dut_serial_port = serial_ports[0]
        self.options.dut_baud_rate = 38400
        self.options.dut_scp_port = ssh_ports[0]
        self.dut = dut(self.campaign_data, self.result_data, self.options,
                       self.rsakey)
        if self.campaign_data['use_aux']:
            self.options.aux_serial_port = serial_ports[1]
            self.options.aux_baud_rate = ssh_ports[1]
            self.options.aux_scp_port = ssh_ports[1]
            self.aux = dut(self.campaign_data, self.result_data, self.options,
                           self.rsakey, aux=True)
        if checkpoint is None:
            self.continue_dut()
            self.do_uboot()
            if self.campaign_data['use_aux']:
                aux_process = Thread(
                    target=self.aux.do_login,
                    kwargs={'ip_address': '10.10.0.104',
                            'change_prompt': (self.board == 'a9x2'),
                            'simics': True})
                aux_process.start()
            self.dut.do_login(ip_address='10.10.0.100',
                              change_prompt=(self.board == 'a9x2'),
                              simics=True)
            if self.campaign_data['use_aux']:
                aux_process.join()
        else:
            self.dut.ip_address = '127.0.0.1'
            if self.board == 'a9x2':
                self.dut.prompt = 'DrSEUs# '
            if self.campaign_data['use_aux']:
                self.aux.ip_address = '127.0.0.1'
                if self.board == 'a9x2':
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
        if self.campaign_data['use_aux']:
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
            if self.campaign_data['use_aux']:
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
                if self.options.application:
                    self.campaign_data['debugger_output'] += \
                        '\nkilled unresponsive simics process\n'
                else:
                    self.result_data['debugger_output'] += \
                        '\nkilled unresponsive simics process\n'
                if self.options.debug:
                    print(colored('killed unresponsive simics process',
                                  'yellow'))
            else:
                if self.options.application:
                    self.campaign_data['debugger_output'] += 'quit\n'
                else:
                    self.result_data['debugger_output'] += 'quit\n'
                if self.options.debug:
                    print(colored('quit', 'yellow'))
                self.simics.wait()
        self.simics = None

    def halt_dut(self):
        self.simics.send_signal(SIGINT)
        self.read_until()
        return True

    def continue_dut(self):
        self.simics.stdin.write('run\n')
        if self.options.application:
            self.campaign_data['debugger_output'] += 'run\n'
        else:
            self.result_data['debugger_output'] += 'run\n'
        if self.options.debug:
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
            if self.options.application:
                self.campaign_data['debugger_output'] += char
            else:
                self.result_data['debugger_output'] += char
            if self.options.debug:
                print(colored(char, 'yellow'), end='')
                sys.stdout.flush()
            buff += char
            if buff[-len(string):] == string:
                break
        if self.options.inject:
            with sql() as db:
                if self.options.application:
                    db.update_dict('campaign', self.campaign_data)
                else:
                    db.update_dict('result', self.result_data)
        for message in self.error_messages:
            if message in buff:
                raise DrSEUsError(message)
        return buff

    def command(self, command):
        self.simics.stdin.write(command+'\n')
        if self.options.application:
            self.campaign_data['debugger_output'] += command+'\n'
        else:
            self.result_data['debugger_output'] += command+'\n'
        if self.options.debug:
            print(colored(command, 'yellow'))
        return self.read_until()

    def do_uboot(self):
        if self.campaign_data['use_aux']:
            def stop_aux_boot():
                self.aux.read_until('autoboot: ')
                self.aux.serial.write('\n')
            aux_process = Thread(target=stop_aux_boot)
            aux_process.start()
        self.dut.read_until('autoboot: ')
        self.dut.serial.write('\n')
        if self.campaign_data['use_aux']:
            aux_process.join()
        self.halt_dut()
        if self.board == 'p2020rdb':
            self.command('DUT_p2020rdb.soc.phys_mem.load-file '
                         '$initrd_image $initrd_addr')
            if self.campaign_data['use_aux']:
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
            if self.campaign_data['use_aux']:
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
            if self.campaign_data['use_aux']:
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
            if self.campaign_data['use_aux']:
                self.aux.read_until('VExpress# ')
                self.aux.serial.write('setenv bootargs console=ttyAMA0 '
                                      'root=/dev/ram0 rw\n')
                self.aux.read_until('VExpress# ')
                self.aux.serial.write('bootm 0x40800000 0x70000000\n')
                # TODO: remove these after fixing command prompt of simics arm
                self.aux.read_until('##')
                self.aux.read_until('##')

    def time_application(self, timing_iterations):
        self.halt_dut()
        time_data = self.command('print-time').split('\n')[-2].split()
        start_cycles = int(time_data[2])
        start_sim_time = float(time_data[3])
        start_time = time.time()
        self.continue_dut()
        for i in xrange(timing_iterations):
            if self.campaign_data['use_aux']:
                aux_process = Thread(
                    target=self.aux.command,
                    args=('./'+self.campaign_data['aux_command'], ))
                aux_process.start()
            self.dut.serial.write(str('./'+self.campaign_data['command']+'\n'))
            if self.campaign_data['use_aux']:
                aux_process.join()
            if self.campaign_data['kill_dut']:
                self.dut.serial.write('\x03')
            self.dut.read_until()
        self.halt_dut()
        end_time = time.time()
        time_data = self.command('print-time').split('\n')[-2].split()
        end_cycles = int(time_data[2])
        end_sim_time = float(time_data[3])
        self.continue_dut()
        self.campaign_data['exec_time'] = \
            (end_time - start_time) / timing_iterations
        self.campaign_data['num_cycles'] = \
            int((end_cycles - start_cycles) / timing_iterations)
        self.campaign_data['sim_time'] = \
            (end_sim_time - start_sim_time) / timing_iterations

    def create_checkpoints(self):
        os.makedirs('simics-workspace/gold-checkpoints/' +
                    str(self.campaign_data['id']))
        self.campaign_data['cycles_between'] = \
            self.campaign_data['num_cycles'] / self.options.num_checkpoints
        self.halt_dut()
        if self.campaign_data['use_aux']:
                aux_process = Thread(
                    target=self.aux.command,
                    args=('./'+self.campaign_data['aux_command'], ))
                aux_process.start()
        self.dut.serial.write('./'+self.campaign_data['command']+'\n')
        read_thread = Thread(target=self.dut.read_until)
        read_thread.start()
        checkpoint = 0
        while True:
            checkpoint += 1
            self.command('run-cycles ' +
                         str(self.campaign_data['cycles_between']))
            self.campaign_data['dut_output'] += ('***drseus_checkpoint: ' +
                                                 str(checkpoint)+'***\n')
            incremental_checkpoint = ('gold-checkpoints/' +
                                      str(self.campaign_data['id'])+'/' +
                                      str(checkpoint))
            self.command('write-configuration '+incremental_checkpoint)
            if not read_thread.is_alive() or (self.campaign_data['use_aux'] and
                                              self.campaign_data['kill_dut'] and
                                              not aux_process.is_alive()):
                merged_checkpoint = incremental_checkpoint+'_merged'
                self.command('!bin/checkpoint-merge '+incremental_checkpoint +
                             ' '+merged_checkpoint)
                break
        self.campaign_data['num_checkpoints'] = checkpoint
        self.continue_dut()
        if self.campaign_data['use_aux']:
            aux_process.join()
        if self.campaign_data['kill_dut']:
            self.dut.serial.write('\x03')
        read_thread.join()

    def inject_fault(self, checkpoints_to_inject, selected_targets):
        latent_faults = 0
        for injection_number in xrange(1, len(checkpoints_to_inject)+1):
            checkpoint_number = checkpoints_to_inject[injection_number-1]
            injected_checkpoint = simics_checkpoints.inject_checkpoint(
                self.campaign_data['id'], self.result_data['id'],
                injection_number, checkpoint_number, self.board,
                selected_targets, self.options.debug)
            self.launch_simics(injected_checkpoint)
            injections_remaining = (injection_number <
                                    len(checkpoints_to_inject))
            if injections_remaining:
                next_checkpoint = checkpoints_to_inject[injection_number]
            else:
                next_checkpoint = self.campaign_data['num_checkpoints']
            errors = self.compare_checkpoints(checkpoint_number,
                                              next_checkpoint)
            if errors > latent_faults:
                latent_faults = errors
            if injections_remaining:
                self.close()
        return latent_faults

    #  TODO: update
    def regenerate_checkpoints(self, result_id, cycles_between, injection_data):
        for i in xrange(len(injection_data)):
            if i == 0:
                checkpoint = ('simics-workspace/gold-checkpoints/' +
                              str(self.campaign_data['id'])+'/' +
                              str(injection_data[i]['checkpoint_number']))
            else:
                checkpoint = ('simics-workspace/injected-checkpoints/' +
                              str(self.campaign_data['id'])+'/' +
                              str(result_id)+'/' +
                              str(injection_data[i]['checkpoint_number']))
            injected_checkpoint = ('simics-workspace/injected-checkpoints/' +
                                   str(self.campaign_data['id'])+'/' +
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
                             str(self.campaign_data['id'])+'/' +
                             str(result_id)+'/' +
                             str(injection_data[i+1]['checkpoint_number']))
                self.close()
        return injected_checkpoint

    def compare_checkpoints(self, checkpoint_number, last_checkpoint):
        reg_errors = 0
        mem_errors = 0
        for checkpoint_number in xrange(checkpoint_number + 1,
                                        last_checkpoint + 1):
            self.command('run-cycles ' +
                         str(self.campaign_data['cycles_between']))
            incremental_checkpoint = (
                'injected-checkpoints/'+str(self.campaign_data['id'])+'/' +
                str(self.result_data['id'])+'/'+str(checkpoint_number))
            monitor = self.options.compare_all or \
                checkpoint_number == self.campaign_data['num_checkpoints']
            if monitor or checkpoint_number == last_checkpoint:
                self.command('write-configuration '+incremental_checkpoint)
            if monitor:
                monitored_checkpoint = incremental_checkpoint+'_merged'
                self.command('!bin/checkpoint-merge '+incremental_checkpoint +
                             ' '+monitored_checkpoint)
                gold_incremental_checkpoint = ('gold-checkpoints/' +
                                               str(self.campaign_data['id']) +
                                               '/'+str(checkpoint_number))
                gold_checkpoint = ('gold-checkpoints/' +
                                   str(self.campaign_data['id'])+'/' +
                                   str(checkpoint_number)+'_merged')
                if not os.path.exists('simics-workspace/'+gold_checkpoint):
                    self.command('!bin/checkpoint-merge ' +
                                 gold_incremental_checkpoint+' ' +
                                 gold_checkpoint)
                gold_checkpoint = 'simics-workspace/'+gold_checkpoint
                monitored_checkpoint = 'simics-workspace/'+monitored_checkpoint
                errors = simics_checkpoints.compare_registers(
                    self.result_data['id'], checkpoint_number, gold_checkpoint,
                    monitored_checkpoint, self.board)
                if errors > reg_errors:
                    reg_errors = errors
                errors = simics_checkpoints.compare_memory(
                    self.result_data['id'], checkpoint_number, gold_checkpoint,
                    monitored_checkpoint, self.board)
                if errors > reg_errors:
                    mem_errors = errors
        return reg_errors + mem_errors

    def persistent_faults(self):
        with sql(row_factory='row') as db:
            db.cursor.execute('SELECT config_object,register,register_index,'
                              'injected_value FROM log_injection '
                              'WHERE result_id=?', (self.result_data['id'],))
            injections = db.cursor.fetchall()
            db.cursor.execute('SELECT * FROM log_simics_register_diff '
                              'WHERE result_id=?', (self.result_data['id'],))
            register_diffs = db.cursor.fetchall()
            db.cursor.execute('SELECT * FROM log_simics_memory_diff '
                              'WHERE result_id=?', (self.result_data['id'],))
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
