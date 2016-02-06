from io import StringIO
from paramiko import AutoAddPolicy, RSAKey, SSHClient
from scp import SCPClient
from serial import Serial
from serial.serialutil import SerialException
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

    def __init__(self, database, options, aux=False):

        self.db = database
        self.options = options
        self.aux = aux
        self.ip_address = options.dut_ip_address if not aux \
            else options.aux_ip_address
        self.scp_port = options.dut_scp_port if not aux \
            else options.aux_scp_port
        self.prompt = options.dut_prompt if not aux else options.aux_prompt
        self.prompt += ' '
        rsakey_file = StringIO(database.campaign['rsakey'])
        self.rsakey = RSAKey.from_private_key(rsakey_file)
        rsakey_file.close()
        self.uboot_command = options.dut_uboot if not aux \
            else options.aux_uboot
        self.login_command = options.dut_login if not aux \
            else options.aux_login
        self.open()

    def __str__(self):
        string = ('Serial Port: '+self.serial.port+'\n\tTimeout: ' +
                  str(self.serial.timeout)+' seconds\n\tPrompt: \"' +
                  self.prompt+'\"\n\tIP Address: '+str(self.ip_address) +
                  '\n\tSCP Port: '+str(self.scp_port))
        return string

    def open(self, attempts=10):
        serial_port = (self.options.dut_serial_port if not self.aux
                       else self.options.aux_serial_port)
        if self.db.result:
            self.db.result[('dut' if not self.aux else 'aux') +
                           '_serial_port'] = serial_port
            with self.db as db:
                db.update('result')
        baud_rate = (self.options.dut_baud_rate if not self.aux
                     else self.options.aux_baud_rate)
        self.serial = Serial(port=None, baudrate=baud_rate,
                             timeout=self.options.timeout, rtscts=True)
        if self.db.campaign['simics']:
            # workaround for pyserial 3
            self.serial._dsrdtr = True
        self.serial.port = serial_port
        for attempt in range(attempts):
            try:
                self.serial.open()
            except Exception as error:
                with self.db as db:
                    db.log_event('Warning' if attempt < attempts-1 else 'Error',
                                 'DUT' if not self.aux else 'AUX',
                                 'Error opening serial port',
                                 db.log_exception)
                print(colored(
                    'Error opening serial port '+serial_port+' (attempt ' +
                    str(attempt+1)+'/'+str(attempts)+'): '+str(error), 'red'))
                if attempt < attempts-1:
                    sleep(30)
                else:
                    raise DrSEUsError('Error opening serial port')
            else:
                break
        self.serial.reset_input_buffer()
        with self.db as db:
            db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                         'Connected to serial port', serial_port)

    def close(self):
        self.serial.close()
        with self.db as db:
            db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                         'Closed serial port')

    def flush(self):
        try:
            in_bytes = self.serial.in_waiting
        except:
            pass
        else:
            if in_bytes:
                buff = self.serial.read(in_bytes).decode('utf-8', 'replace')
                if self.db.result:
                    self.db.result['dut_output' if not self.aux
                                   else 'aux_output'] += buff
                else:
                    self.db.campaign['dut_output' if not self.aux
                                     else 'aux_output'] += buff
                with self.db as db:
                    db.log_event('Information',
                                 'DUT' if not self.aux else 'AUX',
                                 'Flushed serial buffer')

    def send_files(self, files, attempts=10):
        if self.options.debug:
            print(colored('sending file(s)...', 'blue'), end='')
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        for attempt in range(attempts):
            try:
                ssh.connect(self.ip_address, port=self.scp_port,
                            username='root', pkey=self.rsakey, timeout=30,
                            allow_agent=False, look_for_keys=False)
            except Exception as error:
                with self.db as db:
                    db.log_event('Warning' if attempt < attempts-1 else 'Error',
                                 'DUT' if not self.aux else 'AUX', 'SSH error',
                                 db.log_exception)
                print(colored(
                    self.serial.port+': Error sending file(s) (attempt ' +
                    str(attempt+1)+'/'+str(attempts)+'): '+str(error), 'red'))
                if attempt < attempts-1:
                    sleep(30)
                else:
                    raise DrSEUsError(DrSEUsError.ssh_error)
            else:
                dut_scp = SCPClient(ssh.get_transport())
                try:
                    dut_scp.put(files)
                except Exception as error:
                    with self.db as db:
                        db.log_event('Warning' if attempt < attempts-1
                                     else 'Error',
                                     'DUT' if not self.aux else 'AUX',
                                     'SCP error', db.log_exception)
                    print(colored(
                        self.serial.port+': Error sending file(s) (attempt ' +
                        str(attempt+1)+'/'+str(attempts)+'): '+str(error),
                        'red'))
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
                    with self.db as db:
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
                ssh.connect(self.ip_address, port=self.scp_port,
                            username='root', pkey=self.rsakey, timeout=30,
                            allow_agent=False, look_for_keys=False)
            except Exception as error:
                with self.db as db:
                    db.log_event('Warning' if attempt < attempts-1 else 'Error',
                                 'DUT' if not self.aux else 'AUX', 'SSH error',
                                 db.log_exception)
                print(colored(
                    self.serial.port+': Error receiving file (attempt ' +
                    str(attempt+1)+'/'+str(attempts)+'): '+str(error), 'red'))
                if attempt < attempts-1:
                    sleep(30)
                else:
                    raise DrSEUsError(DrSEUsError.ssh_error)
            else:
                dut_scp = SCPClient(ssh.get_transport())
                try:
                    dut_scp.get(file_, local_path=local_path)
                except Exception as error:
                    with self.db as db:
                        db.log_event('Warning' if attempt < attempts-1
                                     else 'Error',
                                     'DUT' if not self.aux else 'AUX',
                                     'SCP error', db.log_exception)
                    print(colored(
                        self.serial.port+': Error receiving file (attempt ' +
                        str(attempt+1)+'/'+str(attempts)+'): '+str(error),
                        'red'))
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
                    with self.db as db:
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
            try:
                char = self.serial.read().decode('utf-8', 'replace')
            except SerialException:
                char = ''
                errors += 1
                with self.db as db:
                    db.log_event('Error', 'DUT' if not self.aux else 'AUX',
                                 'Read error', db.log_exception)
            else:
                if not char:
                    hanging = True
                    with self.db as db:
                        db.log_event('Error', 'DUT' if not self.aux else 'AUX',
                                     'Read timeout', db.log_trace)
                    if not continuous:
                        break
            if self.db.result:
                self.db.result['dut_output' if not self.aux
                               else 'aux_output'] += char
            else:
                self.db.campaign['dut_output' if not self.aux
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
                    with self.db as db:
                        db.log_event('Warning' if boot else 'Error',
                                     'DUT' if not self.aux else 'AUX',
                                     category, event_buff)
                    event_buff_logged += event_buff
            if not continuous and errors > 10:
                break
            if not boot and buff and buff[-1] == '\n':
                with self.db as db:
                    if self.db.result:
                        db.update('result')
                    else:
                        db.update('campaign')
        if self.serial.timeout != self.options.timeout:
            try:
                self.serial.timeout = self.options.timeout
            except:
                with self.db as db:
                    db.log_event('Error', 'DUT' if not self.aux else 'AUX',
                                 'Error resetting timeout', db.log_exception)
                self.close()
                self.open()
        if self.options.debug:
            print()
        if 'drseus_detected_errors:' in buff:
            for line in buff.split('\n'):
                if 'drseus_detected_errors:' in line:
                    if self.db.result['detected_errors'] is None:
                        self.db.result['detected_errors'] = 0
                    # TODO: use regular expression
                    self.db.result['detected_errors'] += \
                        int(line.replace('drseus_detected_errors:', ''))
        with self.db as db:
            if self.db.result:
                db.update('result')
            else:
                db.update('campaign')
        if errors and not boot:
            for message, category in self.error_messages:
                if message in buff:
                    raise DrSEUsError(category)
        if hanging:
            raise DrSEUsError(DrSEUsError.hanging)
        if boot:
            with self.db as db:
                db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                             'Booted')
        return buff

    def command(self, command=None):
        with self.db as db:
            event = db.log_event('Information',
                                 'DUT' if not self.aux else 'AUX', 'Command',
                                 command, success=False)
        if command:
            self.write(command+'\n')
        else:
            self.write('\n')
        buff = self.read_until()
        with self.db as db:
            db.log_event_success(event)
        return buff

    def do_login(self, change_prompt=False):
        self.read_until(boot=True)
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
        if self.db.campaign['simics']:
            self.command('ip addr add '+self.ip_address+'/24 dev eth0')
            self.command('ip link set eth0 up')
            self.command('ip addr show')
            self.ip_address = '127.0.0.1'
        if self.ip_address is None:
            attempts = 10
            for attempt in range(attempts):
                for line in self.command('ip addr show').split('\n'):
                    line = line.strip().split()
                    if len(line) > 0 and line[0] == 'inet':
                        addr = line[1].split('/')[0]
                        if addr != '127.0.0.1':
                            self.ip_address = addr
                            break
                else:
                    if attempt < attempts-1:
                        sleep(5)
                    else:
                        raise DrSEUsError('Error finding device ip address')
                if self.ip_address is not None:
                    break
        with self.db as db:
            db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                         'Logged in')
