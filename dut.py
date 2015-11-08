from __future__ import print_function
from multiprocessing import Process
import os
import paramiko
from scp import SCPClient
from serial import Serial
from termcolor import colored

from error import DrSEUsError


class dut:
    error_messages = ['Kernel panic', 'panic', 'Oops', 'Segmentation fault',
                      'Illegal instruction', 'Call Trace:',
                      'detected stalls on CPU', 'malloc(): memory corruption',
                      'Unable to handle kernel paging request',
                      'Bad swap file entry']

    def __init__(self, ip_address, rsakey, serial_port, prompt, debug, timeout,
                 baud_rate=115200, ssh_port=22, color='green'):
        if debug:
            paramiko.util.log_to_file('campaign-data/paramiko_'+ip_address+'_' +
                                      str(ssh_port)+'.log')
        self.output = ''
        self.paramiko_output = ''
        self.default_timeout = timeout
        try:
            self.serial = Serial(port=serial_port, baudrate=baud_rate,
                                 timeout=timeout, rtscts=True)
        except:
            raise Exception('error opening serial port', serial_port,
                            ', are you a member of dialout?')
        self.prompt = prompt+' '
        self.ip_address = ip_address
        self.ssh_port = ssh_port
        self.debug = debug
        self.rsakey = rsakey
        self.color = color

    def close(self):
        self.serial.close()

    def send_files(self, files):
        fallback = False
        fallback_failed = False
        if self.debug:
            print(colored('sending files...', 'blue'))
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ip_address, port=self.ssh_port, username='root',
                        pkey=self.rsakey, look_for_keys=False)
            dut_scp = SCPClient(ssh.get_transport())
            dut_scp.put(files)
            dut_scp.close()
            ssh.close()
        except Exception as error:
            print(error)
            fallback = True
            if self.debug:
                print(colored('falling back to scp...', 'blue'))
            for file_ in files:
                scp_process = Process(target=os.system,
                                      args=('scp -P '+str(self.ssh_port) +
                                            ' -i campaign-data/private.key '
                                            '-o StrictHostKeyChecking=no ' +
                                            file_+' root@' +
                                            str(self.ip_address)+':',))
                scp_process.start()
                scp_process.join(timeout=30)
                if scp_process.is_alive():
                    scp_process.terminate()
                    fallback_failed = True
                    if self.debug:
                        print(colored('fallback failed', 'blue'))
                    break
        paramiko_log = ('campaign-data/paramiko_'+self.ip_address+'_' +
                        str(self.ssh_port)+'.log')
        if os.path.exists(paramiko_log):
            with open(paramiko_log) as log_file:
                self.paramiko_output += log_file.read()
            os.remove(paramiko_log)
        if fallback:
            self.paramiko_output += '\nFallback to SCP used'
            if fallback_failed:
                self.paramiko_output += ', but failed'
                raise DrSEUsError(DrSEUsError.scp_error)
        if self.debug:
            print(colored('files sent', 'blue'))

    def get_file(self, file_, local_path=''):
        fallback = False
        fallback_failed = False
        if self.debug:
            print(colored('getting file...', 'blue'))
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ip_address, port=self.ssh_port, username='root',
                        pkey=self.rsakey, look_for_keys=False)
            dut_scp = SCPClient(ssh.get_transport())
            dut_scp.get(file_, local_path=local_path)
            dut_scp.close()
            ssh.close()
        except Exception as error:
            print(error)
            fallback = True
            if self.debug:
                print(colored('falling back to scp...', 'blue'))
            scp_process = Process(target=os.system,
                                  args=('scp -P '+str(self.ssh_port) +
                                        ' -i campaign-data/private.key '
                                        '-o StrictHostKeyChecking=no '
                                        'root@'+str(self.ip_address)+':'+file_ +
                                        ' ./'+local_path,))
            scp_process.start()
            scp_process.join(timeout=30)
            if scp_process.is_alive():
                scp_process.terminate()
                fallback_failed = True
                if self.debug:
                    print(colored('fallback failed', 'blue'))
        paramiko_log = ('campaign-data/paramiko_'+self.ip_address+'_' +
                        str(self.ssh_port)+'.log')
        if os.path.exists(paramiko_log):
            with open(paramiko_log) as log_file:
                self.paramiko_output += log_file.read()
            os.remove(paramiko_log)
        if fallback:
            self.paramiko_output += '\nFallback to SCP used'
            if fallback_failed:
                self.paramiko_output += ', but failed'
                raise DrSEUsError(DrSEUsError.scp_error)
        if self.debug:
            print(colored('file received', 'blue'))

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
                raise DrSEUsError(DrSEUsError.hanging)
            elif buff[-len(self.prompt):] == self.prompt:
                return True
            elif buff[-len('login: '):] == 'login: ':
                return False

    def read_until(self, string=None):
        if string is None:
            string = self.prompt
        buff = ''
        hanging = False
        errors = 0
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
            for message in self.error_messages:
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
            for message in self.error_messages:
                if message in buff:
                    raise DrSEUsError(message)
        if hanging:
            raise DrSEUsError(DrSEUsError.hanging)
        else:
            return buff

    def command(self, command=''):
        self.serial.write(str(command+'\n'))
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
