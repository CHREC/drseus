from __future__ import print_function
import subprocess
import os
import sys
import signal

from termcolor import colored

from error import DrSEUSError
from dut import dut
from simics_checkpoints import (inject_checkpoint, compare_registers,
                                compare_memory)


class simics:
    error_messages = ['where nothing is mapped', 'Error']

    # create simics instance and boot device
    def __init__(self, architecture, rsakey, use_aux, new, debug):
        self.debug = debug
        self.architecture = architecture
        self.rsakey = rsakey
        self.use_aux = use_aux
        if new:
            self.launch_simics()

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
                if self.architecture == 'p2020':
                    buff = self.command('run-command-file simics-p2020rdb/'
                                        'p2020rdb-linux'+('-ethernet' if
                                                          self.use_aux
                                                          else '') +
                                        '.simics')
                elif self.architecture == 'arm':
                    buff = self.command('run-command-file simics-vexpress-a9x4/'
                                        'vexpress-a9x4-linux'+('-ethernet' if
                                                               self.use_aux
                                                               else '') +
                                        '.simics')
            except IOError:
                print('lost contact with simics')
                if raw_input(
                    'launch simics_license.sh? [Y/n]: ') not in ['n', 'no',
                                                                 'N', 'No',
                                                                 'NO']:
                    subprocess.call(['gnome-terminal', '-x',
                                     os.getcwd()+'/simics_license.sh'])
                    raw_input('press enter to restart')
                    os.execv('drseus.py', sys.argv)
                sys.exit()
        else:
            self.injected_checkpoint = checkpoint
            buff = self.command('read-configuration '+checkpoint)
            buff += self.command('connect-real-network-port-in ssh '
                                 'ethernet_switch0 target-ip=10.10.0.100')
        found_settings = 0
        serial_ports = []
        ssh_ports = []
        for line in buff.split('\n'):
            if 'pseudo device opened: /dev/pts/' in line:
                serial_ports.append(line.split(':')[1].strip())
                found_settings += 1
            elif 'Host TCP port' in line:
                ssh_ports.append(int(line.split('->')[0].split(' ')[-2]))
                found_settings += 1
            if not self.use_aux and found_settings == 2:
                break
            elif self.use_aux and found_settings == 4:
                break
        else:
            print('could not find port or pseudoterminal to attach to')
            if raw_input('launch simics_license.sh? [Y/n]: ') not in ['n', 'no',
                                                                      'N', 'No',
                                                                      'NO']:
                subprocess.call(['gnome-terminal', '-x',
                                 os.getcwd()+'/simics_license.sh'])
                raw_input('press enter to restart')
                os.execv('drseus.py', sys.argv)
            sys.exit()
        if self.architecture == 'p2020':
            self.dut = dut('127.0.0.1', self.rsakey, serial_ports[0],
                           'root@p2020rdb:~#', self.debug, 38400, ssh_ports[0])
            if self.use_aux:
                self.aux = dut('127.0.0.1', self.rsakey, serial_ports[1],
                               'root@p2020rdb:~#', self.debug, 38400,
                               ssh_ports[1], 'cyan')
        elif self.architecture == 'arm':
            self.dut = dut('127.0.0.1', self.rsakey, serial_ports[0],
                           '#', self.debug, 38400, ssh_ports[0])
            if self.use_aux:
                self.aux = dut('127.0.0.1', self.rsakey, serial_ports[1],
                               '#', self.debug, 38400, ssh_ports[1], 'cyan')
        if checkpoint is None:
            self.continue_dut()
            self.do_uboot()
            self.dut.do_login(change_prompt=True)
            self.dut.command('ifconfig eth0 10.10.0.100 '
                             'netmask 255.255.255.0 up')
            if self.use_aux:
                self.dut.read_until()
                if self.debug:
                    print()
                self.aux.do_login(change_prompt=True)
                self.aux.command('ifconfig eth0 10.10.0.104 '
                                 'netmask 255.255.255.0 up')
                self.aux.read_until()
        else:
            self.dut.prompt = 'DrSEUS# '

    def close(self):
        self.halt_dut()
        self.command('quit')
        self.simics.wait()
        self.dut.close()
        if self.use_aux:
            self.aux.close()

    def halt_dut(self):
        self.simics.send_signal(signal.SIGINT)
        self.read_until()
        return True

    def continue_dut(self):
        self.simics.stdin.write('run\n')
        self.output += 'run\n'

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
                raise DrSEUSError(message, buff)
        return buff

    def command(self, command):
        self.simics.stdin.write(command+'\n')
        self.output += command+'\n'
        if self.debug:
            print(colored(command+'\n', 'yellow'), end='')
        return self.read_until()

    def do_uboot(self):
        if self.architecture == 'p2020':
            self.dut.read_until('autoboot: ')
            self.dut.serial.write('\n')
            if self.use_aux:
                self.aux.read_until('autoboot: ')
                self.aux.serial.write('\n')
            if self.debug:
                print()
            self.halt_dut()
            self.command('DUT_p2020rdb.soc.phys_mem.load-file '
                         '$initrd_image $initrd_addr')
            if self.use_aux:
                self.command('AUX_p2020rdb1.soc.phys_mem.load-file '
                             '$initrd_image $initrd_addr')
            if self.debug:
                print()
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
        elif self.architecture == 'arm':
            self.dut.read_until('autoboot: ')
            self.dut.serial.write('\n')
            if self.debug:
                print()
            self.halt_dut()
            self.command('DUT_a9x4.coretile.mpcore.phys_mem.load-file '
                         '$kernel_image $kernel_addr')
            self.command('DUT_a9x4.coretile.mpcore.phys_mem.load-file '
                         '$initrd_image $initrd_addr')
            if self.use_aux:
                self.command('AUX_a9x41.coretile.mpcore.phys_mem.load-file '
                             '$kernel_image $kernel_addr')
                self.command('AUX_a9x41.coretile.mpcore.phys_mem.load-file '
                             '$initrd_image $initrd_addr')
            if self.debug:
                print()
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

    def time_application(self, command, iterations):
        for i in xrange(iterations-1):
            self.dut.command('./'+command)
        self.dut.read_until()
        if self.debug:
            print()
        self.halt_dut()
        start_cycles = self.command(
            'print-time').split('\n')[-2].split()[2]
        if self.debug:
            print()
        self.continue_dut()
        self.dut.command('./'+command)
        if self.debug:
            print()
        self.halt_dut()
        end_cycles = self.command(
            'print-time').split('\n')[-2].split()[2]
        if self.debug:
            print()
        self.continue_dut()
        return int(end_cycles) - int(start_cycles)

    def create_checkpoints(self, command, cycles, num_checkpoints, merge_all):
        os.mkdir('simics-workspace/gold-checkpoints')
        step_cycles = cycles / num_checkpoints
        self.halt_dut()
        self.dut.serial.write('./'+command+'\n')
        for checkpoint in xrange(num_checkpoints):
            self.command('run-cycles '+str(step_cycles))
            incremental_checkpoint = ('gold-checkpoints/incremental-' +
                                      str(checkpoint)+'.ckpt')
            self.command('write-configuration '+incremental_checkpoint)
            merged_checkpoint = ('gold-checkpoints/checkpoint-' +
                                 str(checkpoint)+'.ckpt')
            if merge_all or checkpoint == num_checkpoints-1:
                if os.system('simics-workspace/bin/checkpoint-merge'
                             ' simics-workspace/'+incremental_checkpoint +
                             ' simics-workspace/'+merged_checkpoint):
                    raise Exception('simics.py:create_checkpoints(): '
                                    'Could not merge gold checkpoint: ' +
                                    incremental_checkpoint)
        if self.debug:
            print()
        self.continue_dut()
        self.dut.read_until()
        if self.debug:
            print()
        self.close()
        return step_cycles

    def inject_fault(self, injection_number, checkpoint_number, board,
                     selected_targets):
        injected_checkpoint = inject_checkpoint(injection_number,
                                                checkpoint_number, board,
                                                selected_targets, self.debug)
        self.launch_simics(checkpoint=injected_checkpoint)
        return injected_checkpoint

    def compare_checkpoints(self, injection_number, checkpoint, board,
                            cycles_between_checkpoints, num_checkpoints,
                            compare_all):
        if not os.path.exists('simics-workspace/'+checkpoint+'/monitored'):
            os.mkdir('simics-workspace/'+checkpoint+'/monitored')
        checkpoint_number = int(
            checkpoint.split('/')[-1][checkpoint.split('/')[-1].index(
                '-')+1:checkpoint.split('/')[-1].index('.ckpt')])
        for checkpoint_number in xrange(checkpoint_number+1,
                                        num_checkpoints):
            self.command('run-cycles '+str(cycles_between_checkpoints))
            if (compare_all or checkpoint_number == num_checkpoints-1):
                monitored_checkpoint = (checkpoint +
                                        '/monitored/checkpoint-' +
                                        str(checkpoint_number) +
                                        '.ckpt')
                self.command('write-configuration '+monitored_checkpoint)
                monitored_checkpoint = 'simics-workspace/'+monitored_checkpoint
                gold_checkpoint = ('simics-workspace/gold-checkpoints/'
                                   'checkpoint-' +
                                   str(checkpoint_number)+'.ckpt')
                if not os.path.exists(gold_checkpoint):
                    incremental_checkpoint = ('simics-workspace/'
                                              'gold-checkpoints/incremental-' +
                                              str(checkpoint_number)+'.ckpt')
                    if os.system('simics-workspace/bin/checkpoint-merge'
                                 ' simics-workspace/'+incremental_checkpoint +
                                 ' simics-workspace/'+gold_checkpoint):
                        raise Exception('simics.py:compare_checkpoints(): '
                                        'Could not merge gold checkpoint: ' +
                                        incremental_checkpoint)
                compare_registers(injection_number, checkpoint_number,
                                  gold_checkpoint, monitored_checkpoint, board)
                compare_memory(injection_number, checkpoint_number,
                               gold_checkpoint, monitored_checkpoint, board)
        if self.debug:
            print()
