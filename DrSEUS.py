#!/usr/bin/python

from __future__ import print_function
import sys

import telnetlib
import serial

import paramiko
import scp

import subprocess
import signal

import time
import random


class dut:
    def __init__(self, ip_address, serial_port, baud_rate=115200,
                 prompt='root@p2020rdb:~#'):
        self.serial = serial.Serial(port=serial_port,
                                    baudrate=baud_rate,
                                    timeout=None, rtscts=True)
        self.prompt = prompt
        self.ip_address = ip_address

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

    # TODO: add timeout, delete print statement
    def read_until(self, string):
        buff = ''
        while True:
            char = self.serial.read()
            print (char, end='')
            buff += char
            if buff[-len(string):] == string:
                return buff

    def command(self, command):
        self.serial.write(command+'\n')
        self.read_until(self.prompt)

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
        self.simics = None
        self.telnet = telnetlib.Telnet(ip_address)
        if not self.ready():
            print('debugger not ready')
            sys.exit()

        if not self.reset_dut():
            print('error resetting dut')
            sys.exit()

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


class bdi_p2020(bdi):
    def __init__(self):
        pass


class bdi_arm(bdi):
    def __init__(self):
        pass


class simics:
    # create simics instance and boot device
    def __init__(self, simics_workspace='/home/ed/simics-workspace/',
                 dut_ip_address='10.10.0.100'):
        self.simics = subprocess.Popen([simics_workspace+'simics',
                                        '-no-win', '-no-gui', '-q', '-x',
                                        'simplifi/DrSEUS.simics'],
                                       cwd=simics_workspace,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE)
        self.simics.stdin.write('run\n')
        # TODO: add timeout
        while True:
            line = self.simics.stdout.readline()
            if 'pseudo device opened: /dev/pts/' in line:
                serial_port = line.split(':')[1].strip()
                break
        self.dut = dut(dut_ip_address, serial_port, baud_rate=38400)
        self.do_uboot()

    def halt_dut(self):
        self.simics.send_signal(signal.SIGINT)

    def continue_dut(self):
        self.simics.stdin.write('run\n')

    # TODO: add timeout
    def read_until(self, string):
        buff = ''
        while True:
            line = self.simics.stdout.readline()
            buff += line
            if string in line:
                return buff

    def command(self, command):
        self.simics.stdin.write(command+'\n')
        self.read_until('simics>')

    def do_uboot(self):
        self.dut.read_until('autoboot: ')
        self.dut.serial.write('\n')
        self.halt_dut()
        self.command('$system.soc.phys_mem.load-file ' +
                     '$initrd_image $initrd_addr')
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


class simics_p2020(simics):
    def __init__(self):
        pass


class fault_injector:
    # setup dut and debugger
    def __init__(self, dut_ip_address='10.42.0.21',
                 dut_serial_port='/dev/ttyUSB2',
                 debugger_ip_address='10.42.0.50', use_simics=False):
        if use_simics:
            self.debugger = simics()
            self.dut = self.debugger.dut
        else:
            self.debugger = bdi(debugger_ip_address)
            self.dut = dut(dut_ip_address, dut_serial_port)
        # generate key while we wait for system to boot
        self.dut.rsakey = paramiko.RSAKey.generate(1024)
        self.dut.do_login()
        if use_simics:
            self.dut.command('ifconfig eth0 '+dut_ip_address +
                             ' netmask 255.255.255.0')

    def exit(self):
        if self.debugger.simics:
            self.debugger.halt_dut()
            self.debugger.command('quit')
            self.debugger.simics.terminate()
        else:
            self.debugger.command('quit')
            self.debugger.telnet.close()
            # TODO: new solution instead of sync to preserver filesystem, maybe halt?
            self.dut.command('sync')
        self.dut.serial.close()
        sys.exit()

    def setup_campaign(self, directory, application, arguments='',
                       additional_files=None):
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

    # TODO: get cycles if using simics
    def time_application(self, iterations):
        start = time.time()
        for i in xrange(iterations):
            self.dut.command('./'+self.target_app)
        return (time.time() - start) / iterations

    def main(self):
        if self.debugger.simics is None:
            injection_time = random.uniform(0, self.exec_time)
            print('injection at: '+str(injection_time))
            self.dut.serial.write('./'+self.application+' '+self.arguments+'\n')

            time.sleep(injection_time)
            if not self.debugger.halt_dut():
                print('error halting dut')
                sys.exit()

            print(self.debugger.get_dut_regs())

            self.debugger.continue_dut()
            self.dut.read_until(self.dut.serial_prompt)
# try:
DrSEUS = fault_injector(dut_ip_address='10.10.0.100', use_simics=True)
DrSEUS.setup_campaign('../simics-workspace/simicsfs', 'ppc_fi_mm_omp')
# DrSEUS = fault_injector()
# DrSEUS.setup_campaign('../FIapps', 'ppc_fi_mm_omp')
# finally:
DrSEUS.exit()
