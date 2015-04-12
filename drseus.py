#!/usr/bin/python

from __future__ import print_function
import sys

import telnetlib
import serial

import paramiko
# TODO: remove scp and just use sftp in paramiko
import scp

import subprocess
import signal

import optparse
import shutil
import os
import time
import random

# import simics_targets
import checkpoint_injection
import checkpoint_comparison

# TODO: add support for multiple boards (ethernet tests) and concurrent simics injections


class dut_hanging(Exception):
    def __init__(self, console_buffer):
        self.console_buffer = console_buffer


# TODO: use this for console monitoring
# class dut_panic(Exception):
#     def __init__(self, console_buffer):
#         self.console_buffer


class dut:
    def __init__(self, ip_address, serial_port, baud_rate=115200,
                 prompt='root@p2020rdb:~#', timeout=120):  # TODO: should timeout increased?
        self.serial = serial.Serial(port=serial_port, baudrate=baud_rate,
                                    timeout=timeout, rtscts=True)
        self.prompt = prompt+' '
        self.ip_address = ip_address

    def close(self):
        # TODO: remove this (used when resetting board alot)
        # self.command('sync')
        self.serial.close()

    def send_files(self, files):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.ip_address, username='root', pkey=self.rsakey)
        dut_scp = scp.SCPClient(ssh.get_transport())
        dut_scp.put(files)
        ssh.close()

    def get_file(self, file, local_path=''):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.ip_address, username='root', pkey=self.rsakey)
        dut_scp = scp.SCPClient(ssh.get_transport())
        dut_scp.get(file, local_path=local_path)
        ssh.close()

    # TODO: add console monitoring
    def read_until(self, string, debug=True):
        buff = ''
        while True:
            char = self.serial.read()
            if not char:
                raise dut_hanging(buff)
            if debug:
                print(char, end='')
            buff += char
            if buff[-len(string):] == string:
                return buff

    def command(self, command):
        self.serial.write(command+'\n')
        return self.read_until(self.prompt)

    def do_login(self):
        self.read_until('login: ')
        self.command('root')
        self.command('mkdir .ssh')
        self.command('touch .ssh/authorized_keys')
        self.command('echo \"ssh-rsa '+self.rsakey.get_base64() +
                     '\" > /home/root/.ssh/authorized_keys')


class bdi:
    # check debugger is ready and boot device
    def __init__(self, ip_address):
        self.telnet = telnetlib.Telnet(ip_address)
        if not self.ready():
            print('debugger not ready')
            sys.exit()

        if not self.reset_dut():
            print('error resetting dut')
            sys.exit()

    def close(self):
        self.command('quit')
        self.telnet.close()

    def ready(self):
        if self.telnet.expect(['P2020>'], timeout=10)[0] < 0:
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
        self.telnet.write('select '+str(core)+'\r\n')
        for i in xrange(8):
            if self.telnet.expect(['Target CPU', 'Core state',
                                   'Debug entry cause', 'Current PC',
                                   'Current CR', 'Current MSR', 'Current LR',
                                   'Current CCSRBAR'], timeout=10)[0] < 0:
                return False
        # TODO: replace this with regular expressions for getting hexadecimals for above categories
        self.telnet.read_very_eager()
        return True

    def command(self, command):
        # self.debugger.read_very_eager()  # clear telnet buffer
        self.telnet.write(command+'\r\n')
        index, match, text = self.telnet.expect(['P2020>'], timeout=10)
        if index < 0:
            return False
        else:
            return text

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

    def inject_fault(self, injection_time):
        self.dut.serial.write('./'+self.application+' '+self.arguments+'\n')
        time.sleep(injection_time)
        if not self.debugger.halt_dut():
            print('error halting dut')
            sys.exit()
        print(self.get_dut_regs())


class bdi_p2020(bdi):
    def __init__(self):
        pass


class bdi_arm(bdi):
    def __init__(self):
        pass


class simics:
    # create simics instance and boot device
    def __init__(self, dut_ip_address='10.10.0.100', new=True, checkpoint=None):
        self.simics = subprocess.Popen([os.getcwd()+'/simics-workspace/simics',
                                        '-no-win', '-no-gui', '-q'],
                                       cwd=os.getcwd()+'/simics-workspace',
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        if new:
            self.command('$drseus=TRUE')
            self.command(
                'run-command-file p2020rdb-simics/p2020rdb-linux.simics')
        else:
            self.injected_checkpoint = checkpoint
            self.command('read-configuration '+checkpoint)
        buff = self.read_until('simics> ')
        for line in buff.split('\n'):
            if 'pseudo device opened: /dev/pts/' in line:
                serial_port = line.split(':')[1].strip()
                break
        else:
            print('could not find pseudoterminal to attach to')
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
        # self.read_until('running>', debug=True)

    # TODO: add timeout and remove print
    def read_until(self, string, debug=True):
        buff = ''
        while True:
            char = self.simics.stdout.read(1)
            if debug:
                print(char, end='')
            buff += char
            if buff[-len(string):] == string:
                if debug:
                    print('')
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
                              'setenv othbootargs\n' +
                              'setenv consoledev ttyS0\n' +
                              'setenv bootargs root=/dev/ram rw console=' +
                              '$consoledev,$baudrate $othbootargs\n' +
                              'bootm ef080000 10000000 ef040000\n')

    def create_checkpoints(self, target_app, cycles, num_checkpoints):
        os.mkdir('simics-workspace/gold-checkpoints')
        step_cycles = cycles / num_checkpoints
        self.halt_dut()
        self.dut.serial.write('./'+target_app+'\n')
        for checkpoint in xrange(num_checkpoints):
            self.command('run-cycles '+str(step_cycles))
            self.command('write-configuration gold-checkpoints/checkpoint-' +
                         str(checkpoint)+'.ckpt')
            # TODO: merge and delete partial checkpoints
        self.close()
        with open('cycles', 'w') as cycle_file:
            cycle_file.write(str(step_cycles)+'\n')
        return step_cycles

    def compare_checkpoints(self, checkpoint,
                            cycles_between_checkpoints, num_checkpoints):
        checkpoint_number = int(
            checkpoint.split('/')[-1][checkpoint.split('/')[-1].index(
                '-')+1:checkpoint.split('/')[-1].index('.ckpt')])
        incremental_results = []
        for i in xrange(checkpoint_number+1, num_checkpoints):
            self.command('run-cycles '+str(cycles_between_checkpoints))
            gold_checkpoint = ('simics-workspace/gold-checkpoints/checkpoint-' +
                               str(i)+'.ckpt')
            incremental_results.append(
                checkpoint_comparison.CompareCheckpoints(gold_checkpoint,
                                                         checkpoint))
        return incremental_results


class fault_injector:
    # setup dut and debugger
    def __init__(self, dut_ip_address='10.42.0.21',
                 dut_serial_port='/dev/ttyUSB2',
                 debugger_ip_address='10.42.0.50',
                 use_simics=False, new=True):
        self.simics = use_simics
        if new:
            if use_simics:
                self.debugger = simics(new=new)
                self.dut = self.debugger.dut
            else:
                self.debugger = bdi(debugger_ip_address)
                self.dut = dut(dut_ip_address, dut_serial_port)
            # generate key while we wait for system to boot
            self.dut.rsakey = paramiko.RSAKey.generate(1024)
            with open('private.key', 'w') as keyfile:
                self.dut.rsakey.write_private_key(keyfile)
            self.dut.do_login()
            if use_simics:
                self.dut.command('ifconfig eth0 '+dut_ip_address +
                                 ' netmask 255.255.255.0')

    def exit(self):
        self.debugger.close()
        if not self.simics:
            self.dut.serial.close()
        sys.exit()

    def setup_campaign(self, directory, application, arguments='',
                       additional_files=None, num_checkpoints=50):
        if arguments:
            self.target_app = application+' '+arguments
        else:
            self.target_app = application
        files = []
        files.append(directory+'/'+application)
        if additional_files:
            for item in additional_files:
                files.append(directory+'/'+item)
        self.dut.send_files(files)
        self.exec_time = self.time_application(5)
        self.dut.get_file('result.dat')
        self.dut.command('rm result.dat')
        os.rename('result.dat', 'gold.dat')
        if self.simics:
            self.cycles_between = self.debugger.create_checkpoints(
                self.target_app, self.exec_time, num_checkpoints)

    # TODO: get cycles if using simics
    def time_application(self, iterations):
        if self.simics:
            for i in xrange(iterations-1):
                self.dut.command('./'+self.target_app)
            self.debugger.halt_dut()
            start_cycles = self.debugger.command(
                'print-time').split('\n')[-2].split()[2]
            self.debugger.continue_dut()
            self.dut.command('./'+self.target_app)
            self.debugger.halt_dut()
            end_cycles = self.debugger.command(
                'print-time').split('\n')[-2].split()[2]
            self.debugger.continue_dut()
            return int(end_cycles) - int(start_cycles)
        else:
            start = time.time()
            for i in xrange(iterations):
                self.dut.command('./'+self.target_app)
            return (time.time() - start) / iterations

    def inject_fault(self, injection_number):
        if self.simics:
            self.injected_checkpoint = checkpoint_injection.InjectCheckpoint(
                injectionNumber=injection_number, selectedTargets=None)  # ['GPR'])
            self.debugger = simics(new=False,
                                   checkpoint=self.injected_checkpoint)
            self.dut = self.debugger.dut
            with open('private.key') as keyfile:
                self.dut.rsakey = paramiko.RSAKey.from_private_key(keyfile)
        else:
            self.injection_time = random.uniform(0, self.exec_time)
            print('injection at: '+str(self.injection_time))
            self.debugger.inject_fault(self.injection_time)

    def monitor_execution(self):
        if self.simics:
            self.simics_results = self.debugger.compare_checkpoints(
                'simics-workspace/'+self.injected_checkpoint,
                self.cycles_between, 50)
            # TODO: log simics results
        self.debugger.continue_dut()
        try:
            self.dut.read_until(self.dut.prompt)
        except dut_hanging:  # as dut:
            print('hanging dut detected')
            # log the partial buffer
            # print(dut.buff)
        missing_output = False
        try:
            self.dut.get_file('result.dat')
        except paramiko.ssh_exception.AuthenticationException:
            missing_output = True
            print('could not create ssh connection')
        except scp.SCPException:
            missing_output = True
            print('could not get output file')
        else:
            pass
            # TODO: check output
        if self.simics:
            if not missing_output:
                shutil.move('result.dat', 'simics-workspace/' +
                            self.injected_checkpoint+'/')
            self.debugger.close()

parser = optparse.OptionParser('drseus.py application {options}')
parser.add_option('-n', action='store', type='int', dest='num_injections',
                  default=1, help='number of injections to perform')
parser.add_option('-s', action='store_true', dest='simics', default=False,
                  help='use simics simulator')

simics_group = optparse.OptionGroup(parser, 'Simics Options')
simics_group.add_option('-d', action='store_true', dest='clean', default=False,
                        help='clean simics workspace')
simics_group.add_option('-c', action='store_true', dest='resume',
                        default=False, help='continue a previous campaign')
parser.add_option_group(simics_group)
# bdi_group = optparse.OptionGroup(parser, 'BDI3000 Options')
# parser.add_option_group(bdi_group)

options, args = parser.parse_args()
if options.clean:
    shutil.rmtree('simics-workspace/injected-checkpoints')
    print('deleted injected checkpoints')
if len(args) < 1:
    if options.clean:
        sys.exit()
    else:
        parser.error('please specify an application')

if not os.path.exists('fiapps'):
    os.system('./setup_apps.sh')

if not os.path.exists('fiapps/'+args[0]):
    os.system('cd fiapps/; make '+args[0])

if options.simics:
    if not os.path.exists('simics-workspace'):
        os.system('./setup_simics.sh')
    if options.resume:
        drseus = fault_injector(dut_ip_address='10.10.0.100',
                                use_simics=True, new=False)
        with open('cycles', 'r') as cycle_file:
            drseus.cycles_between = int(cycle_file.readline())
    else:
        if os.path.exists('simics-workspace/gold-checkpoints'):
            print('warning: checkpoint directories already exist, ' +
                  'continuing will delete them')
            if raw_input('continue? [Y/n]: ') in ['n', 'N', 'no', 'No', 'NO']:
                sys.exit()
            else:
                shutil.rmtree('simics-workspace/gold-checkpoints')
                print('deleted gold checkpoints')
                if os.path.exists('simics-workspace/injected-checkpoints'):
                    shutil.rmtree('simics-workspace/injected-checkpoints')
                print('deleted injected checkpoints')
        drseus = fault_injector(dut_ip_address='10.10.0.100', use_simics=True)
        drseus.setup_campaign('fiapps', args[0])
else:
    drseus = fault_injector()
    drseus.setup_campaign('fiapps', args[0])

start = 0
if drseus.simics:
    if os.path.exists('simics-workspace/injected-checkpoints'):
        start = len(os.listdir('simics-workspace/injected-checkpoints'))
try:
    for injection_number in xrange(start, start + options.num_injections):
        drseus.inject_fault(injection_number)
        drseus.monitor_execution()
    drseus.exit()
except KeyboardInterrupt:
    drseus.exit()
    if drseus.simics:
        shutil.rmtree('simics-workspace/'+drseus.debugger.injected_checkpoint)
