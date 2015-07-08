from __future__ import print_function
import serial
import sys

import paramiko
import scp
from termcolor import colored

from error import DrSEUSError


class dut:
    error_messages = ['panic', 'Oops', 'Segmentation fault']
    sighandler_messages = ['SIGSEGV', 'SIGILL', 'SIGBUS', 'SIGFPE', 'SIGABRT',
                           'SIGIOT', 'SIGTRAP', 'SIGSYS', 'SIGEMT']

    # TODO: should timeout be increased?
    def __init__(self, ip_address, rsakey, serial_port, prompt, debug,
                 baud_rate=115200, ssh_port=22, color='green', timeout=120):
        if debug:
            paramiko.util.log_to_file('paramiko_'+ip_address+'.log')
        self.output = ''
        try:
            self.serial = serial.Serial(port=serial_port, baudrate=baud_rate,
                                        timeout=timeout, rtscts=True)
        except:
            print('error opening serial port', serial_port,
                  ', are you a member of dialout?')
            sys.exit()
        self.prompt = prompt+' '
        self.ip_address = ip_address
        self.ssh_port = ssh_port
        self.debug = debug
        self.rsakey = rsakey
        self.color = color

    def close(self):
        self.serial.close()

    def send_files(self, files):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.ip_address, port=self.ssh_port, username='root',
                    pkey=self.rsakey)
        dut_scp = scp.SCPClient(ssh.get_transport())
        dut_scp.put(files)
        dut_scp.close()
        ssh.close()

    def get_file(self, file, local_path='', delete_file=True):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.ip_address, port=self.ssh_port, username='root',
                    pkey=self.rsakey)
        dut_scp = scp.SCPClient(ssh.get_transport())
        dut_scp.get(file, local_path=local_path)
        dut_scp.close()
        ssh.close()
        if delete_file:
            self.command('rm '+file)

    def is_logged_in(self):
        self.serial.write('\n')
        buff = ''
        while True:
            char = self.serial.read()
            self.output += char
            if self.debug:
                print(colored(char, self.color), end='')
            buff += char
            if not char:
                raise DrSEUSError(DrSEUSError.dut_hanging, buff)
            elif buff[-len(self.prompt):] == self.prompt:
                return True
            elif buff[-len('login: '):] == 'login: ':
                return False

    def read_until(self, string=None):
        if string is None:
            string = self.prompt
        buff = ''
        hanging = False
        while True:
            char = self.serial.read()
            if not char:
                hanging = True
                break
            self.output += char
            if self.debug:
                print(colored(char, self.color), end='')
            buff += char
            if buff[-len(string):] == string:
                break
        if self.debug:
            print()
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
            raise DrSEUSError(DrSEUSError.dut_hanging, buff)
        else:
            return buff

    def command(self, command=''):
        self.serial.write(command+'\n')
        return self.read_until()

    def do_login(self, change_prompt=False):
        if not self.is_logged_in():
            self.serial.write('root\n')
            buff = ''
            while True:
                char = self.serial.read()
                self.output += char
                if self.debug:
                    print(colored(char, self.color), end='')
                buff += char
                if not char:
                    raise DrSEUSError(DrSEUSError.dut_hanging, buff)
                elif buff[-len(self.prompt):] == self.prompt:
                    break
                elif buff[-len('Password: '):] == 'Password: ':
                    self.command('chrec')
                    break
        if change_prompt:
            self.serial.write('export PS1=\"DrSEUS# \"\n')
            self.prompt = 'DrSEUS# '
            self.read_until()
        self.command('mkdir ~/.ssh')
        self.command('touch ~/.ssh/authorized_keys')
        self.command('echo \"ssh-rsa '+self.rsakey.get_base64() +
                     '\" > ~/.ssh/authorized_keys')
