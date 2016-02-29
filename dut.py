from io import StringIO
from os.path import exists, isdir
from paramiko import AutoAddPolicy, RSAKey, SSHClient
from scp import SCPClient
from serial import Serial
from serial.serialutil import SerialException
from sys import stdout
from termcolor import colored
from time import sleep

from error import DrSEUsError
from timeout import timeout


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
        ('Unknown command', 'Invalid command'),
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
        self.username = options.dut_username if not aux \
            else options.aux_username
        self.password = options.dut_password if not aux \
            else options.aux_password
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
        self.serial.reset_output_buffer()
        with self.db as db:
            db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                         'Connected to serial port', serial_port, success=True)

    def close(self):
        self.flush()
        self.serial.close()
        with self.db as db:
            db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                         'Closed serial port', success=True)

    def flush(self):
        try:
            self.serial.reset_output_buffer()
            buff = None
            try:
                in_bytes = self.serial.in_waiting
            except:
                self.serial.reset_input_buffer()
            else:
                if in_bytes:
                    buff = self.serial.read(in_bytes).decode('utf-8', 'replace')
                    if self.db.result:
                        self.db.result['dut_output' if not self.aux
                                       else 'aux_output'] += buff
                        self.db.update('result')
                    else:
                        self.db.campaign['dut_output' if not self.aux
                                         else 'aux_output'] += buff
                        self.db.update('campaign')
                    if self.options.debug and buff:
                        print(colored(buff,
                                      'green' if not self.aux else 'cyan'),
                              end='')
                        stdout.flush()
            with self.db as db:
                db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                             'Flushed serial buffers', buff, success=True)
        except:
            with self.db as db:
                db.log_event('Error', 'DUT' if not self.aux else 'AUX',
                             'Error flushing serial buffers', db.log_exception)

    def reset_ip(self):
        if self.options.reset_ip and (
            (not self.aux and self.options.dut_ip_address is None) or
                (self.aux and self.options.aux_ip_address is None)):
            self.ip_address = None

    def __attempt_exception(self, attempt, attempts, error, error_type, message,
                            close_items=[]):
        with self.db as db:
            db.log_event('Warning' if attempt < attempts-1 else 'Error',
                         'DUT' if not self.aux else 'AUX', error_type,
                         db.log_exception)
        print(colored(self.serial.port+': '+message+' (attempt ' +
                      str(attempt+1)+'/'+str(attempts)+'): '+str(error), 'red'))
        for item in close_items:
            item.close()
        if attempt < attempts-1:
            sleep(30)
        else:
            raise DrSEUsError(error_type)

    def send_files(self, files, attempts=10):
        if self.options.debug:
            print(colored('sending file(s)...', 'blue'), end='')
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        for attempt in range(attempts):
            try:
                with timeout(30):
                    ssh.connect(self.ip_address, port=self.scp_port,
                                username='root', pkey=self.rsakey,
                                allow_agent=False, look_for_keys=False)
            except Exception as error:
                self.__attempt_exception(
                    attempt, attempts, error, 'SSH error',
                    'Error sending file(s)')
            else:
                try:
                    with timeout(30):
                        dut_scp = SCPClient(ssh.get_transport())
                except Exception as error:
                    self.__attempt_exception(
                        attempt, attempts, error, 'SCP error',
                        'Error sending file(s)', [ssh])
                else:
                    try:
                        with timeout(300):
                            dut_scp.put(files)
                    except Exception as error:
                        self.__attempt_exception(
                            attempt, attempts, error, 'SCP error',
                            'Error sending file(s)', [dut_scp, ssh])
                    else:
                        dut_scp.close()
                        ssh.close()
                        if self.options.debug:
                            print(colored('done', 'blue'))
                        with self.db as db:
                            db.log_event('Information',
                                         'DUT' if not self.aux else 'AUX',
                                         'Sent files', ', '.join(files),
                                         success=True)
                        break

    def get_file(self, file_, local_path='', attempts=10):
        if isdir(local_path):
            if local_path[-1] != '/':
                local_path += '/'
            local_path += file_
        if self.options.debug:
            print(colored('getting file...', 'blue'), end='')
            stdout.flush()
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        for attempt in range(attempts):
            try:
                with timeout(60):
                    ssh.connect(self.ip_address, port=self.scp_port,
                                username='root', pkey=self.rsakey,
                                allow_agent=False, look_for_keys=False)
            except Exception as error:
                self.__attempt_exception(
                    attempt, attempts, error, 'SSH error',
                    'Error receiving file')
            else:
                try:
                    with timeout(60):
                        dut_scp = SCPClient(ssh.get_transport())
                except Exception as error:
                    self.__attempt_exception(
                        attempt, attempts, error, 'SCP error',
                        'Error receiving file', [ssh])
                else:
                    try:
                        with timeout(300):
                            dut_scp.get(file_, local_path=local_path)
                    except Exception as error:
                        self.__attempt_exception(
                            attempt, attempts, error, 'SCP error',
                            'Error receiving file', [dut_scp, ssh])
                    else:
                        dut_scp.close()
                        ssh.close()
                        if exists(local_path):
                            if self.options.debug:
                                print(colored('done', 'blue'))
                            with self.db as db:
                                db.log_event('Information',
                                             'DUT' if not self.aux else 'AUX',
                                             'Received file', file_,
                                             success=True)
                            break
                        else:
                            with self.db as db:
                                db.log_event('Warning' if attempt < attempts-1
                                             else 'Error',
                                             'DUT' if not self.aux else 'AUX',
                                             'Missing file', local_path)
                            print(colored(
                                self.serial.port +
                                ': Error receiving file (attempt ' +
                                str(attempt+1)+'/'+str(attempts) +
                                '): missing file', 'red'))
                            if attempt < attempts-1:
                                sleep(30)
                            else:
                                raise DrSEUsError('Missing file')

    def write(self, string):
        self.serial.write(bytes(string, encoding='utf-8'))

    def read_until(self, string=None, continuous=False, boot=False, flush=True):
        if string is None:
            string = self.prompt
        buff = ''
        event_buff = ''
        event_buff_logged = ''
        errors = 0
        hanging = False
        returned = False
        while True:
            try:
                char = self.serial.read().decode('utf-8', 'replace')
            except SerialException:
                char = ''
                errors += 1
                with self.db as db:
                    db.log_event('Error', 'DUT' if not self.aux else 'AUX',
                                 'Read error', db.log_exception)
                self.close()
                self.open()
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
                if flush:
                    stdout.flush()
            buff += char
            if not continuous and buff[-len(string):] == string:
                returned = True
                break
            elif buff[-len('autoboot: '):] == 'autoboot: ' and \
                    self.uboot_command:
                self.write('\n')
                self.write(self.uboot_command+'\n')
                with self.db as db:
                    db.log_event('Information',
                                 'DUT' if not self.aux else 'AUX', 'Command',
                                 self.uboot_command)
            elif buff[-len('login: '):] == 'login: ':
                self.write(self.username+'\n')
                with self.db as db:
                    db.log_event('Information',
                                 'DUT' if not self.aux else 'AUX', 'Logged in',
                                 self.username)
            elif buff[-len('Password: '):] == 'Password: ':
                self.write(self.password+'\n')
            elif buff[-len('can\'t get kernel image'):] == \
                    'can\'t get kernel image':
                self.write('reset\n')
                with self.db as db:
                    db.log_event('Information',
                                 'DUT' if not self.aux else 'AUX', 'Command',
                                 'reset')
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
        if errors:
            for message, category in self.error_messages:
                if not (boot and category in ('Error booting', 'Reboot',
                                              'Missing file')) and \
                        message in buff:
                    raise DrSEUsError(category, returned)
        if hanging:
            raise DrSEUsError('Hanging', returned)
        if boot:
            with self.db as db:
                db.log_event('Information', 'DUT' if not self.aux else 'AUX',
                             'Booted', success=True)
        return buff, returned

    def command(self, command=None, flush=True):
        with self.db as db:
            event = db.log_event('Information',
                                 'DUT' if not self.aux else 'AUX', 'Command',
                                 command, success=False)
        if command:
            self.write(command+'\n')
        else:
            self.write('\n')
        buff, returned = self.read_until(flush=flush)
        with self.db as db:
            db.log_event_success(event)
        return buff, returned

    def do_login(self, change_prompt=False, flush=True):
        self.serial.timeout = 60
        self.read_until(boot=True, flush=flush)
        if change_prompt:
            self.write('export PS1=\"DrSEUs# \"\n')
            self.read_until('export PS1=\"DrSEUs# \"')
            self.prompt = 'DrSEUs# '
            self.read_until()
        if self.login_command:
            self.command(self.login_command, flush=flush)
        self.command('mkdir ~/.ssh', flush=flush)
        self.command('touch ~/.ssh/authorized_keys', flush=flush)
        self.command('echo \"ssh-rsa '+self.rsakey.get_base64() +
                     '\" > ~/.ssh/authorized_keys', flush=flush)
        if self.db.campaign['simics']:
            self.command('ip addr add '+self.ip_address+'/24 dev eth0',
                         flush=flush)
            self.command('ip link set eth0 up', flush=flush)
            self.command('ip addr show', flush=flush)
            self.ip_address = '127.0.0.1'
        if self.ip_address is None:
            attempts = 10
            for attempt in range(attempts):
                for line in self.command('ip addr show',
                                         flush=flush)[0].split('\n'):
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
