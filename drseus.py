#!/usr/bin/python

from __future__ import print_function
import sys

import telnetlib
import serial

# TODO: do try except to run install dependencies
import paramiko
# TODO: remove scp and just use sftp in paramiko
import scp
import socket  # used for "except socket.error:"

import subprocess
import signal

import optparse
import shutil
import os
import time
import random
import difflib
import pickle

# import simics_targets
import checkpoint_injection
import checkpoint_comparison

# TODO: re-transfer files (and ssh key) if using initramfs
# TODO: add support for multiple boards (ethernet tests) and
#       concurrent simics injections
# TODO: isolate injections on real device
# TODO: add telnet setup for bdi (firmware, configs, etc.)
# TODO: make script for setting up tftp for BDI3000


class DrSEUSError(Exception):
    def __init__(self, error_type, console_buffer=None):
        self.type = error_type
        self.console_buffer = console_buffer


class dut:
    error_messages = ['panic', 'Oops', 'Segmentation fault']
    sighandler_messages = ['SIGSEGV', 'SIGILL', 'SIGBUS', 'SIGFPE', 'SIGABRT',
                           'SIGIOT', 'SIGTRAP', 'SIGSYS', 'SIGEMT']

    # TODO: should timeout increased?
    def __init__(self, ip_address, serial_port, baud_rate=115200,
                 prompt='root@p2020rdb:~#', timeout=120):
        self.output = ''
        try:
            self.serial = serial.Serial(port=serial_port, baudrate=baud_rate,
                                        timeout=timeout, rtscts=True)
        except:
            # TODO: make this automatic
            print('error opening serial port, are you a member of dialout?')
            sys.exit()
        self.prompt = prompt+' '
        self.ip_address = ip_address

    def close(self):
        self.serial.close()

    def send_files(self, files):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.ip_address, username='root', pkey=self.rsakey)
        dut_scp = scp.SCPClient(ssh.get_transport())
        dut_scp.put(files)
        ssh.close()

    def get_file(self, file, local_path='', delete_file=True):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.ip_address, username='root', pkey=self.rsakey)
        dut_scp = scp.SCPClient(ssh.get_transport())
        dut_scp.get(file, local_path=local_path)
        ssh.close()
        if delete_file:
            self.command('rm '+file)

    def is_logged_in(self, debug=True):
        self.serial.write('\n')
        buff = ''
        while True:
            char = self.serial.read()
            self.output += char
            if debug:
                print(char, end='')
            buff += char
            if not char:
                raise DrSEUSError('dut_hanging', buff)
            elif buff[-len(self.prompt):] == self.prompt:
                return True
            elif buff[-len('login: '):] == 'login: ':
                return False

    def read_until(self, string, debug=True):
        buff = ''
        done = False
        hanging = False
        while not done:
            char = self.serial.read()
            self.output += char
            if debug:
                print(char, end='')
            buff += char
            if not char:
                done = True
                hanging = True
            elif buff[-len(string):] == string:
                done = True
        caught_signal = False
        error = False
        if 'drseus_sighandler:' in buff:
            for message in self.sighandler_messages:
                if message in buff:
                    signal_message = message
                    caught_signal = True
                    break
        else:
            for message in self.error_messages:
                if message in buff:
                    error_message = message
                    error = True
                    break
        if caught_signal:
            raise DrSEUSError(signal_message, buff)
        elif error:
            raise DrSEUSError(error_message, buff)
        elif hanging:
            raise DrSEUSError('dut_hanging', buff)
        else:
            return buff

    def command(self, command):
        self.serial.write(command+'\n')
        return self.read_until(self.prompt)

    def do_login(self, debug=True):
        if not self.is_logged_in():
            self.serial.write('root\n')
            buff = ''
            while True:
                char = self.serial.read()
                self.output += char
                if debug:
                    print(char, end='')
                buff += char
                if not char:
                    raise DrSEUSError('dut_hanging', buff)
                elif buff[-len(self.prompt):] == self.prompt:
                    break
                elif buff[-len('Password: '):] == 'Password: ':
                    self.command('chrec')
                    break
        self.command('mkdir .ssh')
        self.command('touch .ssh/authorized_keys')
        self.command('echo \"ssh-rsa '+self.rsakey.get_base64() +
                     '\" > .ssh/authorized_keys')


class bdi:
    # check debugger is ready and boot device
    def __init__(self, ip_address, dut, new):
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
        print('core to inject: ', core_to_inject)
        print('reg to inject: ', reg_to_inject)
        print('value to inject: ', hex(value_to_inject))
        bit_to_inject = random.randrange(64)
        value_injected = value_to_inject ^ (1 << bit_to_inject)
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
    def __init__(self, ip_address, dut, new=True):
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
    def __init__(self, ip_address, dut, new=True):
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


class simics:
    # create simics instance and boot device
    def __init__(self, dut_ip_address='10.10.0.100', new=True, checkpoint=None):
        self.output = ''
        self.simics = subprocess.Popen([os.getcwd()+'/simics-workspace/simics',
                                        '-no-win', '-no-gui', '-q'],
                                       cwd=os.getcwd()+'/simics-workspace',
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE)
        if new:
            self.command('$drseus=TRUE')
            try:
                self.command(
                    'run-command-file p2020rdb-simics/p2020rdb-linux.simics')
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
        try:
            buff = self.read_until('simics> ')
        except DrSEUSError as error:
            if error.type == 'simics_error':
                print('error initializing simics')
                if raw_input('killall simics-commont? [Y/n]: ') not in ['n', 'no',
                                                                        'N', 'No,',
                                                                        'NO']:
                    subprocess.call(['gnome-terminal', '-e',
                                     'sudo killall simics-common'])
                    raw_input('press enter to restart...')
                    os.execv(__file__, sys.argv)
            else:
                raise DrSEUSError(error.type, error.console_buffer)
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
        self.dut = dut(dut_ip_address, serial_port, baud_rate=38400)
        if new:
            self.continue_dut()
            self.do_uboot()

    def close(self):
        self.simics.send_signal(signal.SIGINT)
        self.simics.stdin.write('quit\n')
        self.simics.terminate()
        self.dut.close()

    def halt_dut(self, debug=True):
        self.simics.send_signal(signal.SIGINT)
        return self.read_until('simics> ', debug)

    def continue_dut(self):
        self.simics.stdin.write('run\n')

    # TODO: add timeout
    def read_until(self, string, debug=True):
        buff = ''
        while self.simics.poll() is None:
            char = self.simics.stdout.read(1)
            self.output += char
            if debug:
                print(char, end='')
            buff += char
            if buff[-len(string):] == string:
                if debug:
                    print('')
                if 'Error' in buff:
                    raise DrSEUSError('simics_error', buff)
                return buff
        if 'Error' in buff:
            raise DrSEUSError('simics_error', buff)
        return buff

    def command(self, command):
        self.simics.stdin.write(command+'\n')
        return self.read_until('simics> ',)

    def do_uboot(self):
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

    def compare_checkpoints(self, checkpoint,
                            cycles_between_checkpoints, num_checkpoints):
        if not os.path.exists('simics-workspace/'+checkpoint+'/monitored'):
            os.mkdir('simics-workspace/'+checkpoint+'/monitored')
        checkpoint_number = int(
            checkpoint.split('/')[-1][checkpoint.split('/')[-1].index(
                '-')+1:checkpoint.split('/')[-1].index('.ckpt')])
        incremental_results = []
        for i in xrange(checkpoint_number+1, num_checkpoints):
            self.command('run-cycles '+str(cycles_between_checkpoints))
            monitor_checkpoint = (checkpoint +
                                  '/monitored/checkpoint-'+str(i)+'.ckpt')
            self.command('write-configuration '+monitor_checkpoint)
            monitor_checkpoint = 'simics-workspace/'+monitor_checkpoint
            gold_checkpoint = ('simics-workspace/gold-checkpoints/checkpoint-' +
                               str(i)+'.ckpt')
            incremental_results.append(
                checkpoint_comparison.CompareCheckpoints(gold_checkpoint,
                                                         monitor_checkpoint))
        return incremental_results


class fault_injector:
    # setup dut and debugger
    # TODO: move dut into debugger
    def __init__(self, dut_ip_address='10.42.0.21',
                 dut_serial_port='/dev/ttyUSB1',
                 debugger_ip_address='10.42.0.50',
                 architecture='p2020',
                 use_simics=False, new=True):
        if not os.path.exists('campaign-data'):
            os.mkdir('campaign-data')
        self.architecture = architecture
        self.simics = use_simics
        if new:
            if use_simics:
                self.debugger = simics()
                self.dut = self.debugger.dut
            else:
                if architecture == 'p2020':
                    self.dut = dut(dut_ip_address, dut_serial_port)
                    self.debugger = bdi_p2020(debugger_ip_address, self.dut)
                elif architecture == 'arm':
                    self.dut = dut(dut_ip_address, dut_serial_port,
                                   prompt='[root@ZED]#')
                    self.debugger = bdi_arm(debugger_ip_address, self.dut)
                else:
                    print('invalid architecture: ', architecture)
                    sys.exit()
            self.dut.rsakey = paramiko.RSAKey.generate(1024)
            with open('campaign-data/private.key', 'w') as keyfile:
                self.dut.rsakey.write_private_key(keyfile)
            self.dut.do_login()
            if use_simics:
                self.dut.command('ifconfig eth0 '+dut_ip_address +
                                 ' netmask 255.255.255.0')
        elif not use_simics:  # continuing bdi campaign
            if architecture == 'p2020':
                self.dut = dut(dut_ip_address, dut_serial_port)
                self.debugger = bdi_p2020(debugger_ip_address, self.dut,
                                          new=False)
            elif architecture == 'arm':
                self.dut = dut(dut_ip_address, dut_serial_port,
                               prompt='[root@ZED]#')
                self.debugger = bdi_arm(debugger_ip_address, self.dut,
                                        new=False)
            # TODO: should not need this
            else:
                print('invalid architecture: ', architecture)
                sys.exit()
            with open('campaign-data/private.key', 'r') as keyfile:
                self.dut.rsakey = paramiko.RSAKey.from_private_key(keyfile)

    def exit(self):
        if not self.simics:
            self.debugger.close()
            self.dut.close()
        sys.exit()

    def setup_campaign(self, directory, application, arguments, output_file,
                       additional_files, iterations, num_checkpoints):
        self.application = application
        self.output_file = output_file
        if arguments:
            self.command = application+' '+arguments
        else:
            self.command = application
        files = []
        files.append(directory+'/'+application)
        if additional_files:
            for item in additional_files.split(','):
                files.append(directory+'/'+item.lstrip().rstrip())
        try:
            self.dut.send_files(files)
        except socket.error:
            print('could not connect to dut over ssh')
            sys.exit()
        self.exec_time = self.time_application(5)
        try:
            self.dut.get_file(self.output_file,
                              'campaign-data/gold_'+self.output_file)
        except scp.SCPException:
            print ('could not get gold output file from dut')
            sys.exit()
        campaign = {
            'application': self.application,
            'output_file': self.output_file,
            'command': self.command,
            'architecture': self.architecture,
            'use_simics': self.simics,
        }
        if self.simics:
            self.cycles_between = self.debugger.create_checkpoints(
                self.command, self.exec_time, num_checkpoints)
            campaign['cycles_between'] = self.cycles_between
            campaign['dut_output'] = self.dut.output
            campaign['debugger_output'] = self.debugger.output
        else:
            campaign['exec_time'] = self.exec_time
        with open('campaign-data/campaign.pickle', 'w') as campaign_pickle:
            pickle.dump(campaign, campaign_pickle)

    def time_application(self, iterations):
        if self.simics:
            for i in xrange(iterations-1):
                self.dut.command('./'+self.command)
            self.debugger.halt_dut()
            start_cycles = self.debugger.command(
                'print-time').split('\n')[-2].split()[2]
            self.debugger.continue_dut()
            self.dut.command('./'+self.command)
            self.debugger.halt_dut()
            end_cycles = self.debugger.command(
                'print-time').split('\n')[-2].split()[2]
            self.debugger.continue_dut()
            return int(end_cycles) - int(start_cycles)
        else:
            start = time.time()
            for i in xrange(iterations):
                self.dut.command('./'+self.command)
            return (time.time() - start) / iterations

    def inject_fault(self, injection_number):
        if not os.path.exists('campaign-data/results'):
            os.mkdir('campaign-data/results')
        os.mkdir('campaign-data/results/'+str(injection_number))
        if self.simics:
            self.injected_checkpoint = checkpoint_injection.InjectCheckpoint(
                injectionNumber=injection_number, selectedTargets=['GPR'])
            self.debugger = simics(new=False,
                                   checkpoint=self.injected_checkpoint)
            self.dut = self.debugger.dut
            with open('campaign-data/private.key') as keyfile:
                self.dut.rsakey = paramiko.RSAKey.from_private_key(keyfile)
        else:
            injection_time = random.uniform(0, self.exec_time)
            print('injection at: ', injection_time)
            self.injection_data = self.debugger.inject_fault(
                injection_time, self.command)

    def monitor_execution(self, injection_number):
        if self.simics:
            self.simics_results = self.debugger.compare_checkpoints(
                self.injected_checkpoint, self.cycles_between, 50)
        self.debugger.continue_dut()
        try:
            self.dut.read_until(self.dut.prompt)
        except DrSEUSError as error:
            if error.type == 'dut_hanging':
                print('hanging dut detected')
                hanging = True
            else:
                raise DrSEUSError(error.type, error.console_buffer)
        else:
            hanging = False
        self.data_diff = None
        if not hanging:
            try:
                output_location = ('campaign-data/results/' +
                                   str(injection_number)+'/'+self.output_file)
                gold_location = 'campaign-data/gold_'+self.output_file
                self.dut.get_file(self.output_file, output_location)
            except paramiko.ssh_exception.AuthenticationException:
                missing_output = True
                print('could not create ssh connection')
            except scp.SCPException:
                missing_output = True
                print('could not get output file')
            else:
                missing_output = False
                with open(gold_location, 'r') as solution:
                    solutionContents = solution.read()
                with open(output_location, 'r') as result:
                    resultContents = result.read()
                self.data_diff = difflib.SequenceMatcher(
                    None, solutionContents, resultContents).quick_ratio()
                data_error = self.data_diff < 1.0
        if hanging:
            self.outcome = 'hanging'
        elif missing_output:
            self.outcome = 'execution error'
        elif data_error:
            self.outcome = 'data error'
        else:
            self.outcome = 'no error'
        print('outcome: ', self.outcome)
        if self.simics:
            self.debugger.close()

    def log_injection(self, injection_number):
        with open('campaign-data/campaign.pickle', 'r') as campaign_pickle:
            campaign_data = pickle.load(campaign_pickle)
        if self.simics:
            with open('simics-workspace/'+self.injected_checkpoint +
                      '/InjectionData.pickle', 'r') as injection_data_pickle:
                self.injection_data = pickle.load(injection_data_pickle)
        log = {
            'injection_data': self.injection_data,
            'dut_output': self.dut.output,
            'debugger_output': self.debugger.output,
            'data_diff': self.data_diff,
            'outcome': self.outcome,
        }
        if self.simics:
            log['checkpoint_comparisons'] = self.simics_results
            log['dut_output_previous'] = campaign_data['dut_output']
            log['debugger_output_previous'] = campaign_data['debugger_output']
        if not os.path.exists('campaign-data/results'):
            os.mkdir('campaign-data/results')
        with open('campaign-data/results/'+str(injection_number)+'/log.pickle',
                  'w') as log_pickle:
            pickle.dump(log, log_pickle)


class supervisor:
    def __init__(self, dut_ip_address='10.42.0.21',
                 dut_serial_port='/dev/ttyUSB1',
                 aux_ip_address='10.42.0.20',
                 aux_serial_port='/dev/ttyUSB0',
                 use_aux=True, new=True):
        self.use_aux = use_aux
        if not os.path.exists('campaign-data'):
            os.mkdir('campaign-data')
        if new:
            self.dut = dut(dut_ip_address, dut_serial_port)
            self.aux = dut(aux_ip_address, aux_serial_port)
            self.dut.rsakey = paramiko.RSAKey.generate(1024)
            self.aux.rsakey = self.dut.rsakey
            with open('campaign-data/private.key', 'w') as keyfile:
                self.dut.rsakey.write_private_key(keyfile)
            self.dut.do_login()
            self.aux.do_login()
        else:
            self.dut = dut(dut_ip_address, dut_serial_port)
            self.aux = dut(aux_ip_address, aux_serial_port)
            with open('campaign-data/private.key', 'r') as keyfile:
                self.dut.rsakey = paramiko.RSAKey.from_private_key(keyfile)

    def exit(self):
        self.dut.serial.close()
        self.aux.serial.close()
        sys.exit()

    def setup_campaign(self, directory, application, arguments,
                       aux_application, aux_arguments):
        self.application = application
        self.aux_application = aux_application
        if arguments:
            self.command = application+' '+arguments
        else:
            self.command = application
        if aux_arguments:
            self.aux_command = aux_application+' '+aux_arguments
        else:
            self.aux_command = aux_application
        files = []
        files.append(directory+'/'+application)
        aux_files = []
        aux_files.append(directory+'/'+aux_application)
        try:
            self.dut.send_files(files)
        except socket.error:
            print('could not connect to dut over ssh')
            sys.exit()
        try:
            self.aux.send_files(aux_files)
        except socket.error:
            print('could not connect to aux over ssh')
            sys.exit()
        campaign = {
            'application': self.application,
            'aux_application': self.aux_application,
            'command': self.command,
            'aux_command': self.aux_command,
            'use_aux': self.use_aux,
        }
        with open('campaign-data/campaign.pickle', 'w') as campaign_pickle:
            pickle.dump(campaign, campaign_pickle)

    def monitor_execution(self):
        self.dut.serial.write('./'+self.command+'\n')
        self.aux.serial.write('./'+self.aux_command+'\n')
        self.aux.read_until(self.aux.prompt)
        self.dut.read_until(self.dut.prompt)

# main()
parser = optparse.OptionParser('drseus.py {application} {options}')

# general options
parser.add_option('-d', '--delete', action='store_true', dest='clean',
                  default=False,
                  help='delete results and/or injected checkpoints')
parser.add_option('-i', '--inject', action='store_true', dest='inject',
                  default=False,
                  help='perform fault injections on an existing campaign')

# new campaign options
parser.add_option('-t', '--timing', action='store', type='int',
                  dest='iterations', default=5,
                  help='number of timing iterations of application ' +
                       'to run [default=5]')
parser.add_option('-o', '--output', action='store', type='str',
                  dest='output_file', default='result.dat',
                  help='target application output file [default=result.dat]')
parser.add_option('-a', '--arguments', action='store', type='str',
                  dest='arguments', default='',
                  help='arguments for application')
parser.add_option('-f', '--files', action='store', type='str', dest='files',
                  default='',
                  help='additional files to copy to dut (comma-seperated list)')
parser.add_option('-r', '--architecture', action='store', type='str',
                  dest='architecture', default='p2020',
                  help='target architecture [default=p2020]')
parser.add_option('-s', '--simics', action='store_true', dest='simics',
                  default=False, help='use simics simulator')
parser.add_option('-x', '--auxiliary', action='store_true', dest='aux',
                  default=False, help='use second device during testing')
parser.add_option('-y', '--auxiliary_application', action='store', type='str',
                  dest='aux_app', default=None,
                  help='target application for auxiliary device ' +
                  '[default={application}]')
parser.add_option('-z', '--auxiliary_arguments', action='store', type='str',
                  dest='aux_args', default=None,
                  help='arguments for auxiliary application')

# injection options
parser.add_option('-n', '--num', action='store', type='int',
                  dest='num_injections', default=10,
                  help='number of injections to perform [default=10]')

# simics options
parser.add_option('-c', '--checkpoints', action='store', type='int',
                  dest='num_checkpoints', default=50,
                  help='number of gold checkpoints to create [default=50]')

options, args = parser.parse_args()

# clean campaign (results and injected checkpoints)
if options.clean:
    if os.path.exists('campaign-data/results'):
        shutil.rmtree('campaign-data/results')
        print ('deleted results')
    if os.path.exists('simics-workspace/injected-checkpoints'):
        shutil.rmtree('simics-workspace/injected-checkpoints')
        print('deleted injected checkpoints')

# setup fault injection campaign
if not options.inject and not options.aux:
    if len(args) < 1:
        if options.clean:
            sys.exit()
        else:
            parser.error('please specify an application')
    if not os.path.exists('fiapps'):
        os.system('./setup_apps.sh')
    if not os.path.exists('fiapps/'+args[0]):
        os.system('cd fiapps/; make '+args[0])
    if options.simics and not os.path.exists('simics-workspace'):
        os.system('./setup_simics.sh')
    if os.path.exists('campaign-data'):
        print('warning: previous campaign data exists, ',
              'continuing will delete it')
        if raw_input('continue? [Y/n]: ') in ['n', 'N', 'no', 'No', 'NO']:
            sys.exit()
        else:
            shutil.rmtree('campaign-data')
            print('deleted campaign data')
            if os.path.exists('simics-workspace/gold-checkpoints'):
                shutil.rmtree('simics-workspace/gold-checkpoints')
                print('deleted gold checkpoints')
            if os.path.exists('simics-workspace/injected-checkpoints'):
                shutil.rmtree('simics-workspace/injected-checkpoints')
                print('deleted injected checkpoints')
    if options.simics:
        drseus = fault_injector(dut_ip_address='10.10.0.100', use_simics=True)
    else:
        if options.architecture == 'p2020':
            drseus = fault_injector()
        elif options.architecture == 'arm':
            drseus = fault_injector(dut_ip_address='10.42.0.30',
                                    dut_serial_port='/dev/ttyACM0',
                                    architecture=options.architecture)
        else:
            print('invalid architecture: ', options.architecture)
            sys.exit()
    drseus.setup_campaign('fiapps', args[0], options.arguments,
                          options.output_file, options.files,
                          options.iterations, options.num_checkpoints)
    print('\nsuccessfully setup fault injection campaign:')
    print('\tcopied target application to dut')
    print('\ttimed target application')
    print('\tgot gold output')
    if options.simics:
        print('\tcreated gold checkpoints')

# perform fault injections
elif options.inject:
    # TODO: check state of dut
    if not os.path.exists('campaign-data'):
        print('could not find previously created campaign')
        sys.exit()
    with open('campaign-data/campaign.pickle', 'r') as campaign_pickle:
        campaign_data = pickle.load(campaign_pickle)
    if len(args) > 0:
        if args[0] != campaign_data['application']:
            print('campaign created with different application: ',
                  campaign_data['application'])
            sys.exit()
    if options.simics and not campaign_data['use_simics']:
        print('previous campaign was not created with simics')
        sys.exit()
    if campaign_data['architecture'] == 'p2020':
        drseus = fault_injector(use_simics=campaign_data['use_simics'],
                                new=False)
    elif campaign_data['architecture'] == 'arm':
        drseus = fault_injector(dut_ip_address='10.42.0.30',
                                dut_serial_port='/dev/ttyACM0',
                                architecture='arm',
                                use_simics=campaign_data['use_simics'],
                                new=False)
    # TODO: should not need this
    else:
        print('invalid architecture: ', campaign_data['architecture'])
        sys.exit()
    drseus.command = campaign_data['command']
    drseus.output_file = campaign_data['output_file']
    if campaign_data['use_simics']:
        drseus.cycles_between = campaign_data['cycles_between']
    else:
        drseus.exec_time = campaign_data['exec_time']
    if os.path.exists('campaign-data/results'):
        start = len(os.listdir('campaign-data/results'))
    else:
        start = 0
    try:
        for injection_number in xrange(start, start + options.num_injections):
            drseus.inject_fault(injection_number)
            drseus.monitor_execution(injection_number)
            drseus.log_injection(injection_number)
        drseus.exit()
    except KeyboardInterrupt:
        if not simics:
            drseus.debugger.continue_dut()
        drseus.exit()
        # TODO: delete results folder for injection in progress
        if drseus.simics:
            shutil.rmtree('simics-workspace/' +
                          drseus.debugger.injected_checkpoint)

# setup supervisor
elif options.aux:
    if len(args) < 1:
        if options.clean:
            sys.exit()
        else:
            parser.error('please specify an application')
    drseus = supervisor()
    drseus.setup_campaign('fiapps', args[0], options.arguments,
                          args[0] if options.aux_app is None else
                          options.aux_app,
                          options.arguments if options.aux_args is None else
                          options.aux_args)
    drseus.monitor_execution()
    drseus.exit()
# ./drseus.py ppc_fi_socket_echo -a "65222" -x -y ppc_fi_socket_send_recv -z "10.42.0.21 65222 -i 10"
