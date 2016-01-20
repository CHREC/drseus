from collections import OrderedDict
from paramiko import AutoAddPolicy, SSHClient
from paramiko.ssh_exception import NoValidConnectionsError, SSHException
from scp import SCPClient, SCPException
from serial import Serial
from socket import error as SocketError
from socket import timeout as SocketTimeout
import sys
from termcolor import colored
from time import sleep

from error import DrSEUsError
from sql import sql


class dut(object):
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
         ('login: ', 'Reboot')])

    def __init__(self, campaign_data, result_data, options, rsakey, aux=False):
        self.campaign_data = campaign_data
        self.result_data = result_data
        self.options = options
        self.aux = aux
        serial_port = (options.dut_serial_port if not aux
                       else options.aux_serial_port)
        baud_rate = (options.dut_baud_rate if not aux
                     else options.aux_baud_rate)
        self.serial = Serial(port=None, baudrate=baud_rate,
                             timeout=options.timeout, rtscts=True)
        if self.campaign_data['use_simics']:
            # workaround for pyserial 3
            self.serial._dsrdtr = True
        self.serial.port = serial_port
        # try:
        self.serial.open()
        # except:
        #     raise Exception('error opening serial port', serial_port,
        #                     ', are you a member of dialout?')
        self.serial.reset_input_buffer()
        self.prompt = options.dut_prompt if not aux else options.aux_prompt
        self.prompt += ' '
        self.rsakey = rsakey

    def __str__(self):
        string = ('Serial Port: '+self.serial.port+'\n\tTimeout: ' +
                  str(self.serial.timeout)+' seconds\n\tPrompt: \"' +
                  self.prompt+'\"')
        try:
            string += '\n\tIP Address: '+self.ip_address
        except AttributeError:
            pass
        string += '\n\tSCP Port: '+str(self.options.dut_scp_port if not self.aux
                                       else self.options.aux_scp_port)
        return string

    def close(self):
        self.serial.close()

    def send_files(self, files):
        if self.options.debug:
            print(colored('sending file(s)...', 'blue'))
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        attempts = 10
        for attempt in range(attempts):
            try:
                ssh.connect(self.ip_address, port=(self.options.dut_scp_port
                                                   if not self.aux else
                                                   self.options.aux_scp_port),
                            username='root', pkey=self.rsakey,
                            allow_agent=False, look_for_keys=False)
            except (EOFError, NoValidConnectionsError, SocketError,
                    SSHException) as error:
                print(colored('error sending file(s) (attempt '+str(attempt+1) +
                              '/'+str(attempts)+'): '+str(error), 'red'))
                if attempt < attempts-1:
                    sleep(30)
                else:
                    raise DrSEUsError(DrSEUsError.ssh_error)
            else:
                dut_scp = SCPClient(ssh.get_transport())
                try:
                    dut_scp.put(files)
                except (SCPException, SocketError, SocketTimeout) as error:
                    dut_scp.close()
                    ssh.close()
                    print(colored('error sending file(s) (attempt ' +
                                  str(attempt+1)+'/'+str(attempts)+'): ' +
                                  str(error), 'red'))
                    if attempt < attempts-1:
                        sleep(30)
                    else:
                        raise DrSEUsError(DrSEUsError.scp_error)
                else:
                    dut_scp.close()
                    ssh.close()
                    if self.options.debug:
                        print(colored('done', 'blue'))
                    break

    def get_file(self, file_, local_path=''):
        if self.options.debug:
            print(colored('getting file...', 'blue'), end='')
            sys.stdout.flush()
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        attempts = 10
        for attempt in range(attempts):
            try:
                ssh.connect(self.ip_address, port=(self.options.dut_scp_port
                                                   if not self.aux else
                                                   self.options.aux_scp_port),
                            username='root', pkey=self.rsakey,
                            allow_agent=False, look_for_keys=False)
            except (EOFError, NoValidConnectionsError, SocketError,
                    SSHException) as error:
                print(colored('error getting file (attempt '+str(attempt+1) +
                              '/'+str(attempts)+'): '+str(error), 'red'))
                if attempt < attempts-1:
                    sleep(30)
                else:
                    raise DrSEUsError(DrSEUsError.ssh_error)
            else:
                dut_scp = SCPClient(ssh.get_transport())
                try:
                    dut_scp.get(file_, local_path=local_path)
                except (SCPException, SocketError, SocketTimeout) as error:
                    dut_scp.close()
                    ssh.close()
                    print(colored('error getting file (attempt ' +
                                  str(attempt+1)+'/'+str(attempts)+'): ' +
                                  str(error), 'red'))
                    if attempt < attempts-1:
                        sleep(30)
                    else:
                        raise DrSEUsError(DrSEUsError.scp_error)
                else:
                    dut_scp.close()
                    ssh.close()
                    if self.options.debug:
                        print(colored('done', 'blue'))
                    break

    def write(self, string):
        self.serial.write(bytes(string, encoding='utf-8'))

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
            if self.options.command == 'new':
                self.campaign_data['dut_output' if not self.aux
                                   else 'aux_output'] += char
            else:
                self.result_data['dut_output' if not self.aux
                                 else 'aux_output'] += char
            if self.options.debug:
                print(colored(char, 'green' if not self.aux else 'cyan'),
                      end='')
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
            if buff[-1] == '\n' and self.options.command != 'supervise':
                with sql() as db:
                    if self.options.command == 'new':
                        db.update_dict('campaign', self.campaign_data)
                    else:
                        db.update_dict('result', self.result_data)
        if self.serial.timeout != self.options.timeout:
            self.serial.timeout = self.options.timeout
        if self.options.debug:
            print()
        if self.options.command != 'supervise':
            with sql() as db:
                if self.options.command == 'new':
                    db.update_dict('campaign', self.campaign_data)
                else:
                    db.update_dict('result', self.result_data)
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
        self.write(command+'\n')
        return self.read_until()

    def do_login(self, ip_address=None, change_prompt=False, simics=False):

        def is_logged_in():
            self.write('\n')
            buff = ''
            while True:
                char = self.serial.read().decode('utf-8', 'replace')
                self.result_data['dut_output' if not self.aux
                                 else 'aux_output'] += char
                if self.options.debug:
                    print(colored(char, 'green' if not self.aux else 'cyan'),
                          end='')
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

    # def do_login(self, ip_address=None, change_prompt=False, simics=False):
        if not is_logged_in():
            self.write('root\n')
            buff = ''
            while True:
                char = self.serial.read().decode('utf-8', 'replace')
                self.result_data['dut_output' if not self.aux
                                 else 'aux_output'] += char
                if self.options.debug:
                    print(colored(char, 'green' if not self.aux else 'cyan'),
                          end='')
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
            self.write('export PS1=\"DrSEUs# \"\n')
            self.read_until('export PS1=\"DrSEUs# \"')
            self.prompt = 'DrSEUs# '
            self.read_until()
        self.command('mkdir ~/.ssh')
        self.command('touch ~/.ssh/authorized_keys')
        self.command('echo \"ssh-rsa '+self.rsakey.get_base64() +
                     '\" > ~/.ssh/authorized_keys')
        if ip_address is None:
            attempts = 10
            for attempt in range(attempts):
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
            self.command('ip addr show')
        if simics:
            self.ip_address = '127.0.0.1'
        else:
            self.ip_address = ip_address
