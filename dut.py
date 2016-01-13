from __future__ import print_function
from collections import OrderedDict
# from multiprocessing import Process
# import os
import paramiko
from scp import SCPClient
from serial import Serial
import sys
from termcolor import colored
from time import sleep

from error import DrSEUsError


class dut:
    error_messages = OrderedDict(
        [('drseus_sighandler', 'Signal raised'),
         ('Kernel panic', 'Kernel error'),
         ('panic', 'Kernel error'),
         ('Oops', 'Kernel error'),
         ('Segmentation fault', 'Segmentation fault'),
         ('Illegal instruction', 'Illegal instruction'),
         ('Call Trace:', 'Kernel error'),
         ('detected stalls on CPU', 'Stall detected'),
         ('malloc(), memory corruption', 'Kernel error'),
         ('Bad swap file entry', 'Kernel error'),
         ('Unable to handle kernel paging request', 'Kernel error'),
         ('Alignment trap', 'Kernel error'),
         ('Unhandled fault', 'Kernel error'),
         ('free(), invalid next size', 'Kernel error'),
         ('double free or corruption', 'Kernel error'),
         ('????????', '????????'),
         ('login: ', 'Reboot')]
    )

    def __init__(self, rsakey, serial_port, prompt, debug, timeout,
                 campaign_number, baud_rate=115200, ssh_port=22, color='green'):
        self.output = ''
        self.default_timeout = timeout
        try:
            self.serial = Serial(port=serial_port, baudrate=baud_rate,
                                 timeout=timeout, rtscts=True)
        except:
            raise Exception('error opening serial port', serial_port,
                            ', are you a member of dialout?')
        try:
            self.serial.reset_input_buffer()  # pyserial 3
        except AttributeError:
            self.serial.flushInput()  # pyserial 2.7
        self.prompt = prompt+' '
        self.ssh_port = ssh_port
        self.debug = debug
        self.rsakey = rsakey
        self.campaign_number = campaign_number
        self.color = color

    def __str__(self):
        string = ('Serial Port: '+self.serial.port+'\n\tTimeout: ' +
                  str(self.serial.timeout)+' seconds\n\tPrompt: \"' +
                  self.prompt+'\"')
        try:
            string += '\n\tIP Address: '+self.ip_address
        except AttributeError:
            pass
        string += '\n\tSCP Port: '+str(self.ssh_port)
        return string

    def close(self):
        self.serial.close()

    def send_files(self, files):
        if self.debug:
            print(colored('sending file(s)', 'blue'))
        attempts = 10
        for attempt in xrange(attempts):
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.ip_address, port=self.ssh_port,
                            username='root', pkey=self.rsakey,
                            allow_agent=False, look_for_keys=False)
                dut_scp = SCPClient(ssh.get_transport())
                dut_scp.put(files)
                dut_scp.close()
                ssh.close()
            except:
                try:
                    dut_scp.close()
                    ssh.close()
                except:
                    pass
                print(colored('error sending file(s) (attempt ' +
                              str(attempt+1)+'/'+str(attempts)+')', 'red'))
                if attempt < attempts-1:
                    sleep(30)
                else:
                    raise DrSEUsError(DrSEUsError.scp_error)
            else:
                break
        # try:
        #     ssh = paramiko.SSHClient()
        #     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #     ssh.connect(self.ip_address, port=self.ssh_port, username='root',
        #                 pkey=self.rsakey, look_for_keys=False)
        #     dut_scp = SCPClient(ssh.get_transport())
        #     dut_scp.put(files)
        #     dut_scp.close()
        #     ssh.close()
        # except Exception as error:
        #     print(error)
        #     for file_ in files:
        #         scp_process = Process(target=os.system,
        #                               args=('scp -P '+str(self.ssh_port) +
        #                                     ' -i campaign-data/' +
        #                                     str(self.campaign_number) +
        #                                     '/private.key '
        #                                     '-o StrictHostKeyChecking=no ' +
        #                                     file_+' root@' +
        #                                     str(self.ip_address)+':',))
        #         scp_process.start()
        #         scp_process.join(timeout=30)
        #         if scp_process.exitcode != 0:
        #             scp_process.terminate()
        #             raise DrSEUsError(DrSEUsError.scp_error)
        if self.debug:
            print(colored('files sent', 'blue'))

    def get_file(self, file_, local_path=''):
        if self.debug:
            print(colored('getting file', 'blue'))
        attempts = 10
        for attempt in xrange(attempts):
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(self.ip_address, port=self.ssh_port,
                            username='root', pkey=self.rsakey,
                            allow_agent=False, look_for_keys=False)
                dut_scp = SCPClient(ssh.get_transport())
                dut_scp.get(file_, local_path=local_path)
                dut_scp.close()
                ssh.close()
            except:
                try:
                    dut_scp.close()
                    ssh.close()
                except:
                    pass
                print(colored('error getting file (attempt ' +
                              str(attempt+1)+'/'+str(attempts)+')', 'red'))
                if attempt < attempts-1:
                    sleep(30)
                else:
                    raise DrSEUsError(DrSEUsError.scp_error)
            else:
                break
        # try:
        #     ssh = paramiko.SSHClient()
        #     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #     ssh.connect(self.ip_address, port=self.ssh_port, username='root',
        #                 pkey=self.rsakey, look_for_keys=False)
        #     dut_scp = SCPClient(ssh.get_transport())
        #     dut_scp.get(file_, local_path=local_path)
        #     dut_scp.close()
        #     ssh.close()
        # except Exception as error:
        #     print(error)
        #     scp_process = Process(target=os.system,
        #                           args=('scp -P '+str(self.ssh_port) +
        #                                 ' -i campaign-data/' +
        #                                 str(self.campaign_number) +
        #                                 '/private.key '
        #                                 '-o StrictHostKeyChecking=no '
        #                                 'root@'+str(self.ip_address)+':' +
        #                                 file_+' ./'+local_path,))
        #     scp_process.start()
        #     scp_process.join(timeout=30)
        #     if scp_process.exitcode != 0:
        #         scp_process.terminate()
        #         raise DrSEUsError(DrSEUsError.scp_error)
        if self.debug:
            print(colored('file received', 'blue'))

    def is_logged_in(self):
        self.serial.write('\n')
        buff = ''
        while True:
            char = self.serial.read().decode('utf-8', 'replace')
            self.output += char
            if self.debug:
                print(colored(char, self.color), end='')
            buff += char
            if not char:
                raise DrSEUsError(DrSEUsError.hanging)
            elif buff[-len(self.prompt):] == self.prompt:
                return True
            elif buff[-len('login: '):] == 'login: ':
                return False
            elif buff[-len('can\'t get kernel image'):] == \
                    'can\'t get kernel image':
                raise DrSEUsError('error booting')

    def read_until(self, string=None):
        if string is None:
            string = self.prompt
        buff = ''
        hanging = False
        errors = 0
        while True:
            char = self.serial.read().decode('utf-8', 'replace')
            if not char:
                hanging = True
                break
            self.output += char
            if self.debug:
                print(colored(char, self.color), end='')
                sys.stdout.flush()
            buff += char
            if buff[-len(string):] == string:
                break
            for message in self.error_messages.keys():
                if buff[-len(message):] == message:
                    if errors == 0:
                        self.serial.timeout = 30
                    errors += 1
            if errors > 5:
                break
        if self.serial.timeout != self.default_timeout:
            self.serial.timeout = self.default_timeout
        if self.debug:
            print()
        if 'drseus_sighandler:' in buff:
            signal = 'Signal received'
            for line in buff.split('\n'):
                if 'drseus_sighandler:' in line:
                    signal = line[line.index('drseus_sighandler:'):
                                  ].replace('drseus_sighandler:', '').strip()
                    break
            raise DrSEUsError('Signal '+signal)
        else:
            for message in self.error_messages.keys():
                if message in buff:
                    raise DrSEUsError(self.error_messages[message])
        if hanging:
            raise DrSEUsError(DrSEUsError.hanging)
        else:
            return buff

    def command(self, command=''):
        self.serial.write(str(command+'\n'))
        return self.read_until()

    def do_login(self, ip_address=None, change_prompt=False, simics=False):
        if not self.is_logged_in():
            self.serial.write('root\n')
            buff = ''
            while True:
                char = self.serial.read().decode('utf-8', 'replace')
                self.output += char
                if self.debug:
                    print(colored(char, self.color), end='')
                    sys.stdout.flush()
                buff += char
                if not char:
                    raise DrSEUsError(DrSEUsError.hanging)
                elif buff[-len(self.prompt):] == self.prompt:
                    break
                elif buff[-len('Password: '):] == 'Password: ':
                    self.command('chrec')
                    break
        if change_prompt:
            self.serial.write('export PS1=\"DrSEUs# \"\n')
            self.read_until('export PS1=\"DrSEUs# \"')
            self.prompt = 'DrSEUs# '
            self.read_until()
        self.command('mkdir ~/.ssh')
        self.command('touch ~/.ssh/authorized_keys')
        self.command('echo \"ssh-rsa '+self.rsakey.get_base64() +
                     '\" > ~/.ssh/authorized_keys')
        if ip_address is None:
            attempts = 10
            for attempt in xrange(attempts):
                for line in self.command('ip addr show').split('\n'):
                    line = line.strip().split()
                    if len(line) > 0 and line[0] == 'inet':
                        addr = line[1].split('/')[0]
                        if addr != '127.0.0.1':
                            ip_address = addr
                            break
                else:
                    if attempt < attempts-1:
                        sleep(5)
                    else:
                        raise DrSEUsError('Error finding device ip address')
                if ip_address is not None:
                    break
        else:
            self.command('ip addr add '+ip_address+'/24 dev eth0')
            self.command('ip link set eth0 up')
        if simics:
            self.ip_address = '127.0.0.1'
        else:
            self.ip_address = ip_address
