from paramiko import AutoAddPolicy, SSHClient
from scp import SCPClient
from serial import Serial
import sys
from termcolor import colored
from time import sleep

from error import DrSEUsError
from sql import sql


class dut(object):
    error_messages = [
        ('drseus_sighandler: SIGSEGV', 'Signal SIGSEGV'),
        ('drseus_sighandler: SIGILL', 'Signal SIGILL'),
        ('drseus_sighandler: SIGBUS', 'Signal SIGBUS'),
        ('drseus_sighandler: SIGFPE', 'Signal SIGFPE'),
        ('drseus_sighandler: SIGABRT', 'Signal SIGABRT'),
        ('drseus_sighandler: SIGIOT', 'Signal SIGIOT'),
        ('drseus_sighandler: SIGTRAP', 'Signal SIGTRAP'),
        ('drseus_sighandler: SIGSYS', 'Signal SIGSYS'),
        ('drseus_sighandler: SIGEMT', 'Signal SIGEMT'),
        ('command not found', 'Invalid command'),
        ('No such file or directory', 'Missing file'),
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
        ('Hit any key to stop autoboot:', 'Reboot'),
        ('can\'t get kernel image', 'Error booting')]

    def __init__(self, campaign_data, result_data, options, rsakey, aux=False):
        self.campaign_data = campaign_data
        self.result_data = result_data
        self.options = options
        self.aux = aux
        self.uboot_command = self.options.dut_uboot if not self.aux \
            else self.options.aux_uboot
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
        self.serial.open()
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

    def send_files(self, files, attempts=10):
        if self.options.debug:
            print(colored('sending file(s)...', 'blue'), end='')
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        for attempt in range(attempts):
            try:
                ssh.connect(self.ip_address, port=(self.options.dut_scp_port
                                                   if not self.aux else
                                                   self.options.aux_scp_port),
                            username='root', pkey=self.rsakey,
                            allow_agent=False, look_for_keys=False)
            except Exception as error:
                if self.options.command != 'new':
                    with sql() as db:
                        db.log_event_exception(
                            self.result_data['id'],
                            ('DUT' if not self.aux else 'AUX'),
                            'SSH error')
                print(colored(
                    self.serial.port+' '+str(self.result_data['id'])+': '
                    'error sending file(s) (attempt '+str(attempt+1)+'/' +
                    str(attempts)+'): '+str(error), 'red'))
                if attempt < attempts-1:
                    sleep(30)
                else:
                    raise DrSEUsError(DrSEUsError.ssh_error)
            else:
                dut_scp = SCPClient(ssh.get_transport())
                try:
                    dut_scp.put(files)
                except Exception as error:
                    if self.options.command != 'new':
                        with sql() as db:
                            db.log_event_exception(
                                self.result_data['id'],
                                ('DUT' if not self.aux else 'AUX'),
                                'SCP error')
                    print(colored(
                        self.serial.port+' '+str(self.result_data['id'])+': '
                        'error sending file(s) (attempt '+str(attempt+1)+'/' +
                        str(attempts)+'): '+str(error), 'red'))
                    dut_scp.close()
                    ssh.close()
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

    def get_file(self, file_, local_path='', attempts=10):
        if self.options.debug:
            print(colored('getting file...', 'blue'), end='')
            sys.stdout.flush()
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        for attempt in range(attempts):
            try:
                ssh.connect(self.ip_address, port=(self.options.dut_scp_port
                                                   if not self.aux else
                                                   self.options.aux_scp_port),
                            username='root', pkey=self.rsakey,
                            allow_agent=False, look_for_keys=False)
            except Exception as error:
                if self.options.command != 'new':
                    with sql() as db:
                        db.log_event_exception(
                            self.result_data['id'],
                            ('DUT' if not self.aux else 'AUX'),
                            'SSH error')
                print(colored(
                    self.serial.port+' '+str(self.result_data['id'])+': '
                    'error receiving file (attempt '+str(attempt+1)+'/' +
                    str(attempts)+'): '+str(error), 'red'))
                if attempt < attempts-1:
                    sleep(30)
                else:
                    raise DrSEUsError(DrSEUsError.ssh_error)
            else:
                dut_scp = SCPClient(ssh.get_transport())
                try:
                    dut_scp.get(file_, local_path=local_path)
                except:
                    if self.options.command != 'new':
                        with sql() as db:
                            db.log_event_exception(
                                self.result_data['id'],
                                ('DUT' if not self.aux else 'AUX'),
                                'SCP error')
                    print(colored(
                        self.serial.port+' '+str(self.result_data['id'])+': '
                        'error receiving file (attempt '+str(attempt+1)+'/' +
                        str(attempts)+'): '+str(error), 'red'))
                    dut_scp.close()
                    ssh.close()
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

    def read_until(self, string=None, continuous=False, boot=False):
        if string is None:
            string = self.prompt
        buff = ''
        event_buff = ''
        event_buff_logged = ''
        errors = 0
        while True:
            char = self.serial.read().decode('utf-8', 'replace')
            if not char:
                if self.options.command != 'new':
                    with sql() as db:
                        event_buff = buff.replace(event_buff_logged, '')
                        db.log_event(self.result_data['id'],
                                     ('DUT' if not self.aux else 'AUX'),
                                     'Read timeout', event_buff)
                        event_buff_logged += event_buff
                if not continuous:
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
            if not continuous and buff[-len(string):] == string:
                break
            elif buff[-len('autoboot: '):] == 'autoboot: ' and \
                    self.uboot_command:
                self.write('\n')
                self.write(self.uboot_command+'\n')
            elif buff[-len('login: '):] == 'login: ':
                self.write(self.options.username+'\n')
            elif buff[-len('Password: '):] == 'Password: ':
                self.write(self.options.password+'\n')
            elif buff[-len('can\'t get kernel image'):] == \
                    'can\'t get kernel image':
                self.write('reset\n')
                errors += 1
            for message, category in self.error_messages:
                if buff[-len(message):] == message:
                    if not continuous and not boot:
                        self.serial.timeout = 30
                        errors += 1
                    if self.options.command != 'new' and not (boot):
                            # boot and category == 'Reboot'):
                        with sql() as db:
                            event_buff = buff.replace(event_buff_logged, '')
                            db.log_event(self.result_data['id'],
                                         ('DUT' if not self.aux else 'AUX'),
                                         category, event_buff)
                            event_buff_logged += event_buff
            if not continuous and errors > 10:
                break
            if not boot and buff and buff[-1] == '\n':
                with sql() as db:
                    if self.options.command == 'new':
                        db.update_dict('campaign', self.campaign_data)
                    else:
                        db.update_dict('result', self.result_data)
        if self.serial.timeout != self.options.timeout:
            self.serial.timeout = self.options.timeout
        if self.options.debug:
            print()
        with sql() as db:
            if self.options.command == 'new':
                db.update_dict('campaign', self.campaign_data)
            else:
                db.update_dict('result', self.result_data)
        if errors and not boot:
            for message, category in self.error_messages:
                if message in buff:
                    raise DrSEUsError(category)
        return buff

    def command(self, command=''):
        self.write(command+'\n')
        return self.read_until()

    def do_login(self, ip_address=None, change_prompt=False, simics=False):
        # try:
        self.write('\n')
        self.read_until(boot=True)
        # except DrSEUsError as error:
        #     if error.type == 'Reboot':
        #         pass
        #     else:
        #         raise DrSEUsError(error.type)
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
