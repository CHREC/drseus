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


class fault_injector:
    debugger_prompts = ['BDI>', 'P2020>']

    def __init__(self, dut_serial_port, dut_ip_address, debugger_ip_address,
                 application, arguments='', files=None, simics=None,
                 prompt='root@p2020rdb:~# ', dut_serial_baud=115200):
        self.dut_ip_address = dut_ip_address
        self.application = application
        self.arguments = arguments
        self.simics = simics
        self.prompt = prompt

        if files is None:
            self.files = ['/home/ed/simics-workspace/simicsfs/'+application, ]

        if simics is None:
            self.debugger = telnetlib.Telnet(debugger_ip_address)
            self.dut_serial = serial.Serial(port=dut_serial_port,
                                            baudrate=dut_serial_baud,
                                            timeout=None, rtscts=True)
            self.main()
        else:
            self.main_simics()

    def get_debugger_status(self):
        index, match, text = self.debugger.expect(self.debugger_prompts,
                                                  timeout=10)
        if index == 1:
            return match
        else:
            return False

    def reset_dut(self):
        self.debugger.write('reset\r\n')
        index, match, text = self.debugger.expect(self.debugger_prompts,
                                                  timeout=10)
        if index != 1:
            return False

        self.debugger.write('go\r\n')
        index, match, text = self.debugger.expect(self.debugger_prompts,
                                                  timeout=10)
        if index != 1:
            return False

        return True

    def send_files(self, files):
        dut_ssh = paramiko.SSHClient()
        # dut_ssh.load_system_host_keys()
        dut_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        dut_ssh.connect(self.dut_ip_address, username='root', pkey=self.rsakey)
        dut_scp = scp.SCPClient(dut_ssh.get_transport())

        dut_scp.put(files)

        dut_ssh.close()

    # TODO: add timeout
    def read_until(self, string):
        buff = ''
        while True:
            char = self.dut_serial.read()
            print (char, end='')
            buff += char
            if buff[-len(string):] == string:
                return buff

    def dut_command(self, command):
        self.dut_serial.write(command+'\n')
        self.read_until(self.prompt)

    def main_simics(self):
        self.simics = subprocess.Popen(['/home/ed/simics-workspace/simics',
                                        '-no-win', '-no-gui', '-q', '-x',
                                        'spfi.simics'],
                                       cwd='/home/ed/simics-workspace',
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE)
        self.simics.stdin.write('run\n')
        # TODO: add timeout
        while True:
            line = self.simics.stdout.readline()
            if 'pseudo device opened: /dev/pts/' in line:
                serial_port = line.split(':')[1].strip()
                break
        self.dut_serial = serial.Serial(port=serial_port,
                                        baudrate=38400,
                                        timeout=None)
        self.read_until('autoboot: ')
        self.dut_serial.write('\n')
        self.simics.send_signal(signal.SIGINT)
        # TODO: make simics_command() function
        self.simics.stdin.write('$system.soc.phys_mem.load-file ' +
                                '$initrd_image $initrd_addr\n')
        self.simics.stdin.write('run\n')
        self.dut_serial.write('setenv ethaddr 00:01:af:07:9b:8a\n' +
                              'setenv ipaddr 10.10.0.100\n' +
                              'setenv eth1addr 00:01:af:07:9b:8b\n' +
                              'setenv ip1addr 10.10.0.101\n' +
                              'setenv eth2addr 00:01:af:07:9b:8c\n' +
                              'setenv ip2addr 10.10.0.102\n' +
                              'setenv othbootargs\n' +
                              'setenv consoledev ttyS0\n' +
                              'setenv bootargs root=/dev/ram rw console=' +
                              '$consoledev,$baudrate $othbootargs\n' +
                              'bootm ef080000 10000000 ef040000\n')

        # TODO: add other cpu-intensive things here while we wait for booting
        self.rsakey = paramiko.RSAKey.generate(1024)

        self.read_until('login: ')
        self.dut_command('root')
        self.dut_command('ifconfig eth0 10.10.0.100 netmask 255.255.255.0')
        self.dut_command('mkdir .ssh')
        self.dut_command('touch .ssh/authorized_keys')
        self.dut_command('echo \"ssh-rsa '+self.rsakey.get_base64() +
                         '\" > /home/root/.ssh/authorized_keys')

        self.send_files(self.files)

        # TODO: fix timing for simulation
        start = time.time()
        for i in xrange(10):
            self.dut_command('./'+self.application+' '+self.arguments)
        self.exec_time = (time.time() - start) / 10
        print('average time: '+str(self.exec_time))

        self.dut_serial.close()
        self.simics.send_signal(signal.SIGINT)
        self.simics.stdin.write('quit\n')
        self.simics.terminate()

    def main(self):
        if not self.get_debugger_status():
            print('debugger not ready')
            sys.exit()

        if not self.reset_dut():
            print('error resetting dut')
            sys.exit()

        self.read_until('login: ')
        self.dut_command('root')

        self.send_files(self.files)

        start = time.time()
        for i in xrange(10):
            self.dut_command('./'+self.application+' '+self.arguments)
        self.exec_time = (time.time() - start) / 10
        print('average time: '+str(self.exec_time))

        self.dut_serial.close()
        self.debugger.close()

fault_injector('/dev/', '10.10.0.100', '0.0.0.0', 'ppc_fi_mm_omp',
               simics=True)
