from io import StringIO
from paramiko import AutoAddPolicy, RSAKey, SSHClient
from scp import SCPClient
from serial import Serial
from sys import stdout
from termcolor import colored
from time import sleep

from error import DrSEUsError


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
        ('malloc(): memory corruption', 'Kernel error'),
        ('Bad swap file entry', 'Kernel error'),
        ('Unable to handle kernel paging request', 'Kernel error'),
        ('Alignment trap', 'Kernel error'),
        ('Unhandled fault', 'Kernel error'),
        ('free(), invalid next size', 'Kernel error'),
        ('double free or corruption', 'Kernel error'),
        ('Rebooting in', 'Kernel error'),
        ('????????', '????????'),
        ('Hit any key to stop autoboot:', 'Reboot'),
        ('can\'t get kernel image', 'Error booting')]

    def __init__(self, campaign_data, result_data, database, options,
                 aux=False):
        self.campaign_data = campaign_data
        self.result_data = result_data
        self.database = database
        self.options = options
        self.aux = aux
        self.prompt = options.dut_prompt if not aux else options.aux_prompt
        self.prompt += ' '
        rsakey_file = StringIO(campaign_data['rsakey'])
        self.rsakey = RSAKey.from_private_key(rsakey_file)
        rsakey_file.close()
        self.uboot_command = options.dut_uboot if not self.aux \
            else options.aux_uboot
        self.login_command = options.dut_login if not self.aux \
            else options.aux_login
        serial_port = (options.dut_serial_port if not aux
                       else options.aux_serial_port)
        if result_data:
            result_data[('dut' if not aux else 'aux') +
                        '_serial_port'] = serial_port
        baud_rate = (options.dut_baud_rate if not aux
                     else options.aux_baud_rate)
        self.serial = Serial(port=None, baudrate=baud_rate,
                             timeout=options.timeout, rtscts=True)
        if campaign_data['use_simics']:
            # workaround for pyserial 3
            self.serial._dsrdtr = True
        self.serial.port = serial_port
        self.serial.open()
        self.serial.reset_input_buffer()
        with self.database as db:
            db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                         'Connected to serial port', serial_port)

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
        with self.database as db:
            db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                         'Closed serial port')

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
                with self.database as db:
                    db.log_event('Warning' if attempt < attempts-1 else 'Error',
                                 'DUT' if not self.aux else 'AUX', 'SSH error',
                                 db.log_exception)
                print(colored(
                    self.serial.port+', '+str(self.result_data['id'])+': '
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
                    with self.database as db:
                        db.log_event('Warning' if attempt < attempts-1
                                     else 'Error',
                                     'DUT' if not self.aux else 'AUX',
                                     'SCP error', db.log_exception)
                    print(colored(
                        self.serial.port+', '+str(self.result_data['id'])+': '
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
                    with self.database as db:
                        db.log_event('Information',
                                     'DUT' if not self.aux else 'AUX',
                                     'Sent files', ', '.join(files))
                    break

    def get_file(self, file_, local_path='', attempts=10):
        if self.options.debug:
            print(colored('getting file...', 'blue'), end='')
            stdout.flush()
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
                with self.database as db:
                    db.log_event('Warning' if attempt < attempts-1 else 'Error',
                                 'DUT' if not self.aux else 'AUX', 'SSH error',
                                 db.log_exception)
                print(colored(
                    self.serial.port+', '+str(self.result_data['id'])+': '
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
                except Exception as error:
                    with self.database as db:
                        db.log_event('Warning' if attempt < attempts-1
                                     else 'Error',
                                     'DUT' if not self.aux else 'AUX',
                                     'SCP error', db.log_exception)
                    print(colored(
                        self.serial.port+', '+str(self.result_data['id'])+': '
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
                    with self.database as db:
                        db.log_event('Information',
                                     'DUT' if not self.aux else 'AUX',
                                     'Received file', file_)
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
        hanging = False
        while True:
            char = self.serial.read().decode('utf-8', 'replace')
            if not char:
                hanging = True
                with self.database as db:
                    db.log_event('Warning' if boot else 'Error',
                                 'DUT' if not self.aux else 'AUX',
                                 'Read timeout', db.log_trace)
                if not continuous:
                    break
            if self.result_data:
                self.result_data['dut_output' if not self.aux
                                 else 'aux_output'] += char
            else:
                self.campaign_data['dut_output' if not self.aux
                                   else 'aux_output'] += char
            if self.options.debug:
                print(colored(char, 'green' if not self.aux else 'cyan'),
                      end='')
                stdout.flush()
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
                    if boot:
                        if category in ('Reboot', 'Missing file'):
                            continue
                    elif not continuous:
                        self.serial.timeout = 30
                        errors += 1
                    event_buff = buff.replace(event_buff_logged, '')
                    with self.database as db:
                        db.log_event('Warning' if boot else 'Error',
                                     'DUT' if not self.aux else 'AUX',
                                     category, event_buff)
                    event_buff_logged += event_buff
            if not continuous and errors > 10:
                break
            if not boot and buff and buff[-1] == '\n':
                with self.database as db:
                    if self.result_data:
                        db.update_dict('result')
                    else:
                        db.update_dict('campaign')
        if self.serial.timeout != self.options.timeout:
            self.serial.timeout = self.options.timeout
        if self.options.debug:
            print()
        with self.database as db:
            if self.result_data:
                db.update_dict('result')
            else:
                db.update_dict('campaign')
        if errors and not boot:
            for message, category in self.error_messages:
                if message in buff:
                    raise DrSEUsError(category)
        if hanging:
            raise DrSEUsError(DrSEUsError.hanging)
        if boot:
            with self.database as db:
                db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                             'Booted')
        return buff

    def command(self, command=None):
        if command:
            self.write(command+'\n')
        else:
            self.write('\n')
        buff = self.read_until()
        with self.database as db:
            db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                         'Command', command)
        return buff

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
        if self.login_command:
            self.command(self.login_command)
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
        with self.database as db:
            db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                         'Logged in')
