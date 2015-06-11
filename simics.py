from __future__ import print_function
import subprocess
import os
import sys
import signal

from termcolor import colored

from error import DrSEUSError
from dut import dut
import checkpoint_comparison


class simics:
    # create simics instance and boot device
    def __init__(self, architecture='p2020', dut_ip_address='127.0.0.1',
                 new=True, checkpoint=None, debug=True):
        if 'simics-common' in subprocess.check_output('ps -a', shell=True):
            if raw_input('simics is already running, ' +
                         'killall simics-common? [Y/n]: ') not in ['n', 'no',
                                                                   'N', 'No,',
                                                                   'NO']:
                subprocess.call(['killall', 'simics-common'])

        self.debug = debug
        self.output = ''
        self.architecture = architecture
        self.simics = subprocess.Popen([os.getcwd()+'/simics-workspace/simics',
                                        '-no-win', '-no-gui', '-q'],
                                       cwd=os.getcwd()+'/simics-workspace',
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE)
        if new:
            # self.command('$drseus=TRUE')
            try:
                if self.architecture == 'p2020':
                    self.command(
                        'run-command-file simics-p2020rdb/drseus.simics')
                elif self.architecture == 'arm':
                    self.command(
                        'run-command-file simics-vexpress-a9x4/drseus.simics')
                else:
                    print('invalid architecture:', self.architecture)
                    sys.exit()
            except IOError:
                print('lost contact with simics')
                if raw_input(
                    'launch simics_license.sh? [Y/n]: ') not in ['n', 'no',
                                                                 'N', 'No',
                                                                 'NO']:
                    subprocess.call(['gnome-terminal', '-x',
                                     os.getcwd()+'/simics_license.sh'])
                    raw_input('press enter to restart')
                    os.execv(__file__, sys.argv)
                sys.exit()
        else:
            self.injected_checkpoint = checkpoint
            self.command('read-configuration '+checkpoint)
        # try:
        buff = self.read_until('simics> ')
        # except DrSEUSError as error:
        #     if error.type == 'simics_error':
        #         print('error initializing simics')
        #         if raw_input(
        #             'killall simics-common? [Y/n]: ') not in ['n', 'no',
        #                                                        'N', 'No,',
        #                                                        'NO']:
        #             subprocess.call(['gnome-terminal', '-e',
        #                              'sudo killall simics-common'])
        #             raw_input('press enter to restart...')
        #             os.execv(__file__, sys.argv)
        #     else:
        #         raise DrSEUSError(error.type, error.console_buffer)
        for line in buff.split('\n'):
            if 'pseudo device opened: /dev/pts/' in line:
                serial_port = line.split(':')[1].strip()
                break
        else:
            print('could not find pseudoterminal to attach to')
            if raw_input('launch simics_license.sh? [Y/n]: ') not in ['n', 'no',
                                                                      'N', 'No',
                                                                      'NO']:
                subprocess.call(['gnome-terminal', '-x',
                                 os.getcwd()+'/simics_license.sh'])
                raw_input('press enter to restart...')
                os.execv(__file__, sys.argv)
            sys.exit()
        if self.architecture == 'p2020':
            self.dut = dut(dut_ip_address, serial_port, baud_rate=38400,
                           ssh_port=4022)
        elif self.architecture == 'arm':
            self.dut = dut(dut_ip_address, serial_port, prompt='#',
                           baud_rate=38400, ssh_port=4022)
        if new:
            self.continue_dut()
            self.do_uboot()
        else:
            self.dut.prompt = 'DrSEUS# '

    def close(self):
        self.simics.send_signal(signal.SIGINT)
        self.simics.stdin.write('quit\n')
        self.output += 'quit\n'
        self.simics.terminate()
        self.simics.wait()
        self.dut.close()

    def halt_dut(self):
        self.simics.send_signal(signal.SIGINT)
        return self.read_until('simics> ')

    def continue_dut(self):
        self.simics.stdin.write('run\n')
        self.output += 'run\n'

    # TODO: add timeout
    def read_until(self, string):
        buff = ''
        while self.simics.poll() is None:
            char = self.simics.stdout.read(1)
            self.output += char
            if self.debug:
                print(colored(char, 'yellow'), end='')
            buff += char
            if buff[-len(string):] == string:
                if self.debug:
                    print('')  # TODO: why is this here?
                if 'Error' in buff:
                    raise DrSEUSError('simics_error', buff)
                return buff
        if 'Error' in buff:
            raise DrSEUSError('simics_error', buff)
        return buff

    def command(self, command):
        self.simics.stdin.write(command+'\n')
        self.output += command+'\n'
        return self.read_until('simics> ',)

    def do_uboot(self):
        if self.architecture == 'p2020':
            self.dut.read_until('autoboot: ')
            self.dut.serial.write('\n')
            self.halt_dut()
            self.command('$system.soc.phys_mem.load-file ' +
                         '$initrd_image $initrd_addr')
            self.command('$dut_system = $system')
            self.continue_dut()
            self.dut.serial.write('setenv ethaddr 00:01:af:07:9b:8a\n' +
                                  # 'setenv ipaddr 10.10.0.100\n' +
                                  'setenv eth1addr 00:01:af:07:9b:8b\n' +
                                  # 'setenv ip1addr 10.10.0.101\n' +
                                  'setenv eth2addr 00:01:af:07:9b:8c\n' +
                                  # 'setenv ip2addr 10.10.0.102\n' +
                                  # 'setenv othbootargs\n' +
                                  'setenv consoledev ttyS0\n' +
                                  'setenv bootargs root=/dev/ram rw console=' +
                                  # '$consoledev,$baudrate $othbootargs\n' +
                                  '$consoledev,$baudrate\n' +
                                  'bootm ef080000 10000000 ef040000\n')
        elif self.architecture == 'arm':
            self.dut.read_until('autoboot: ')
            self.dut.serial.write('\n')
            self.halt_dut()
            self.command('$phys_mem.load-file $kernel_image $kernel_addr')
            self.command('$phys_mem.load-file $initrd_image $initrd_addr')
            self.command('$dut_system = $system')
            self.continue_dut()
            self.dut.read_until('VExpress# ')
            self.dut.serial.write('setenv bootargs console=ttyAMA0 ' +
                                  'root=/dev/ram0 rw\n')
            self.dut.read_until('VExpress# ')
            self.dut.serial.write('bootm 0x40800000 0x70000000\n')
            # TODO: remove these after fixing command prompt of simics arm
            self.dut.read_until('##')
            self.dut.read_until('##')

    def create_checkpoints(self, command, cycles, num_checkpoints):
        os.mkdir('simics-workspace/gold-checkpoints')
        step_cycles = cycles / num_checkpoints
        self.halt_dut()
        self.dut.serial.write('./'+command+'\n')
        for checkpoint in xrange(num_checkpoints):
            self.command('run-cycles '+str(step_cycles))
            self.command('write-configuration gold-checkpoints/checkpoint-' +
                         str(checkpoint)+'.ckpt')
            # TODO: merge checkpionts?
        self.close()
        return step_cycles

    def compare_checkpoints(self, injection_number, checkpoint, board,
                            cycles_between_checkpoints, num_checkpoints):
        if not os.path.exists('simics-workspace/'+checkpoint+'/monitored'):
            os.mkdir('simics-workspace/'+checkpoint+'/monitored')
        checkpoint_number = int(
            checkpoint.split('/')[-1][checkpoint.split('/')[-1].index(
                '-')+1:checkpoint.split('/')[-1].index('.ckpt')])
        for monitored_checkpoint_number in xrange(checkpoint_number+1,
                                                  num_checkpoints):
            self.command('run-cycles '+str(cycles_between_checkpoints))
            monitor_checkpoint = (checkpoint +
                                  '/monitored/checkpoint-' +
                                  str(monitored_checkpoint_number)+'.ckpt')
            self.command('write-configuration '+monitor_checkpoint)
            monitor_checkpoint = 'simics-workspace/'+monitor_checkpoint
            gold_checkpoint = ('simics-workspace/gold-checkpoints/checkpoint-' +
                               str(monitored_checkpoint_number)+'.ckpt')
            checkpoint_comparison.CompareRegisters(
                injection_number, monitored_checkpoint_number,
                gold_checkpoint, monitor_checkpoint, board
            )
