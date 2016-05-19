from datetime import datetime
from io import StringIO
from os import listdir, makedirs
from os.path import exists, join
from paramiko import AutoAddPolicy, RSAKey, SSHClient
from re import compile as regex
from re import DOTALL, escape
from scp import SCPClient
from serial import Serial
from serial.serialutil import SerialException
from shutil import copy
from sys import stdout
from termcolor import colored
from time import perf_counter, sleep

from .error import DrSEUsError
from .timeout import timeout, TimeoutException


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

        ('Segmentation fault', 'Segmentation fault'),
        ('Illegal instruction', 'Illegal instruction'),

        ('command not found', 'Invalid command'),
        ('Unknown command', 'Invalid command'),
        ('No such file or directory', 'Missing file'),

        ('detected stalls on CPU', 'Stall detected'),
        ('detected stall on CPU', 'Stall detected'),

        ('panic', 'Kernel error'),
        ('Oops', 'Kernel error'),
        ('Call Trace:', 'Kernel error'),
        ('malloc(), memory corruption', 'Kernel error'),
        ('malloc(): memory corruption', 'Kernel error'),
        ('Bad swap file entry', 'Kernel error'),
        ('Unable to handle kernel paging request', 'Kernel error'),
        ('Alignment trap', 'Kernel error'),
        ('Unhandled fault', 'Kernel error'),
        ('unhandled signal', 'Kernel error'),
        ('free(), invalid next size', 'Kernel error'),
        ('double free or corruption', 'Kernel error'),
        ('Rebooting in', 'Kernel error'),
        ('????????', 'Kernel error'),
        ('Backtrace:', 'Kernel error'),
        ('Exception stack', 'Kernel error'),

        ('Hit any key to stop autoboot:', 'Reboot'),
        ('Booting Linux', 'Reboot'),

        ('can\'t get kernel image', 'Error booting')]

    def __init__(self, database, options, aux=False):
        self.db = database
        self.options = options
        self.aux = aux
        self.__start_time = None
        self.__timer_value = 0
        self.ip_address = options.dut_ip_address if not aux \
            else options.aux_ip_address
        self.scp_port = options.dut_scp_port if not aux \
            else options.aux_scp_port
        self.prompt = '{} '.format(
            options.dut_prompt if not aux or not options.aux_prompt
            else options.aux_prompt)
        self.username = options.dut_username if not aux \
            else options.aux_username
        self.password = options.dut_password if not aux \
            else options.aux_password
        rsakey_file = StringIO(database.campaign.rsakey)
        self.rsakey = RSAKey.from_private_key(rsakey_file)
        rsakey_file.close()
        self.uboot_command = options.dut_uboot if not aux \
            else options.aux_uboot
        self.login_command = options.dut_login if not aux \
            else options.aux_login
        for message in reversed(options.error_messages):
            self.error_messages.insert(0, (message, message))
        self.open()

    def __str__(self):
        return ('Serial Port: {}\n\tTimeout: {} seconds\n\tPrompt: "{}"\n\t'
                'IP Address: {}\n\tSCP Port: {}').format(
                    self.serial.port, self.serial.timeout, self.prompt,
                    self.ip_address, self.scp_port)

    def start_timer(self):
        self.__start_time = perf_counter()

    def stop_timer(self):
        if self.__start_time is not None:
            self.__timer_value += perf_counter() - self.__start_time
            self.__start_time = None

    def reset_timer(self):
        self.__start_time = None
        self.__timer_value = 0

    def get_timer_value(self):
        return self.__timer_value

    def open(self, attempts=10):
        serial_port = (self.options.dut_serial_port if not self.aux
                       else self.options.aux_serial_port)
        baud_rate = (self.options.dut_baud_rate if not self.aux
                     else self.options.aux_baud_rate)
        rtscts = (self.options.dut_rtscts if not self.aux
                  else self.options.aux_rtscts)
        self.serial = Serial(port=None, baudrate=baud_rate,
                             timeout=self.options.timeout, rtscts=rtscts)
        if self.db.campaign.simics:
            # workaround for pyserial 3
            self.serial._dsrdtr = True
        self.serial.port = serial_port
        for attempt in range(attempts):
            try:
                self.serial.open()
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as error:
                self.db.log_event(
                    'Warning' if attempt < attempts-1 else 'Error',
                    'DUT' if not self.aux else 'AUX',
                    'Error opening serial port', self.db.log_exception)
                print(colored(
                    'Error opening serial port {} (attempt {}/{}): {}'.format(
                        serial_port, attempt+1, attempts, error), 'red'))
                if attempt < attempts-1:
                    sleep(30)
                else:
                    raise DrSEUsError('Error opening serial port')
            else:
                break
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        self.db.log_event(
            'Information', 'DUT' if not self.aux else 'AUX',
            'Connected to serial port', serial_port)

    def close(self):
        self.flush()
        self.serial.close()
        self.db.log_event(
            'Information', 'DUT' if not self.aux else 'AUX',
            'Closed serial port')

    def flush(self, check_errors=False):
        try:
            self.serial.reset_output_buffer()
            buff = None
            try:
                in_bytes = self.serial.in_waiting
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except:
                self.serial.reset_input_buffer()
            else:
                if in_bytes:
                    buff = ''
                    for b in range(in_bytes):
                        char = self.serial.read().decode('utf-8', 'replace')
                        buff += char
                        if self.options.debug:
                            print(
                                colored(char,
                                        'green' if not self.aux else 'cyan'),
                                end='')
                    if self.options.debug:
                        stdout.flush()
                    if self.db.result is None:
                        if self.aux:
                            self.db.campaign.aux_output += buff
                        else:
                            self.db.campaign.dut_output += buff
                        self.db.campaign.save()
                    else:
                        if self.aux:
                            self.db.result.aux_output += buff
                        else:
                            self.db.result.dut_output += buff
                        self.db.result.save()

                    if check_errors:
                        for message, category in self.error_messages:
                            if message in buff:
                                raise DrSEUsError(category)
            self.db.log_event(
                'Information', 'DUT' if not self.aux else 'AUX',
                'Flushed serial buffers', buff)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            self.db.log_event(
                'Error', 'DUT' if not self.aux else 'AUX',
                'Error flushing serial buffers', self.db.log_exception)

    def reset_ip(self):
        if self.options.reset_ip and (
            (not self.aux and self.options.dut_ip_address is None) or
                (self.aux and self.options.aux_ip_address is None)):
            self.ip_address = None

    def __attempt_exception(self, attempt, attempts, error, error_type, message,
                            close_items=[]):
        self.db.log_event(
            'Warning' if attempt < attempts-1 else 'Error',
            'DUT' if not self.aux else 'AUX', error_type, self.db.log_exception)
        print(colored('{}: {} (attempt {}/{}): {}'.format(
            self.serial.port, message, attempt+1, attempts, error), 'red'))
        for item in close_items:
            item.close()
        if attempt < attempts-1:
            sleep(30)
        else:
            raise DrSEUsError(error_type)

    def send_files(self, files=None, attempts=10):
        rename_gold = False
        if not files:
            files = []
            location = 'campaign-data/{}/{}-files'.format(
                self.db.campaign.id, 'aux' if self.aux else 'dut')
            if exists(location):
                for item in listdir(location):
                    files.append('{}/{}'.format(location, item))
            else:
                if self.options.application_file:
                    files.append('{}/{}'.format(
                        self.options.directory,
                        self.options.aux_application if self.aux
                        else self.options.application))
                if self.options.files:
                    for file_ in self.options.files:
                        files.append('{}/{}'.format(
                            self.options.directory, file_))
                makedirs(location)
                if self.options.debug:
                    print(colored('copying campaign file(s)...', 'blue'),
                          end='')
                    stdout.flush()
                for file_ in files:
                    copy(file_, location)
                if self.options.debug:
                    print(colored('done', 'blue'))
            if hasattr(self.options, 'local_diff') and \
                    self.options.local_diff and self.db.campaign.output_file:
                files.append('campaign-data/{}/gold/{}'.format(
                    self.db.campaign.id, self.db.campaign.output_file))
                rename_gold = True
        if not files:
            return
        if self.options.debug:
            print(colored('sending file(s)...', 'blue'), end='')
            stdout.flush()
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        for attempt in range(attempts):
            try:
                with timeout(30):
                    if self.options.rsa:
                        ssh.connect(self.ip_address, port=self.scp_port,
                                    username=self.username, pkey=self.rsakey,
                                    allow_agent=False, look_for_keys=False)
                    else:
                        ssh.connect(self.ip_address, port=self.scp_port,
                                    username=self.username,
                                    password=self.password, allow_agent=False,
                                    look_for_keys=False)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as error:
                self.__attempt_exception(
                    attempt, attempts, error, 'SSH error',
                    'Error sending file(s)')
            else:
                try:
                    with timeout(30):
                        dut_scp = SCPClient(ssh.get_transport())
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as error:
                    self.__attempt_exception(
                        attempt, attempts, error, 'SCP error',
                        'Error sending file(s)', [ssh])
                else:
                    try:
                        with timeout(300):
                            dut_scp.put(files)
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
                    except Exception as error:
                        self.__attempt_exception(
                            attempt, attempts, error, 'SCP error',
                            'Error sending file(s)', [dut_scp, ssh])
                    else:
                        dut_scp.close()
                        ssh.close()
                        if self.options.debug:
                            print(colored('done', 'blue'))
                        self.db.log_event(
                            'Information', 'DUT' if not self.aux else 'AUX',
                            'Sent files', ', '.join(files))
                        break
        if rename_gold:
            self.command('mv {0} gold_{0}'.format(self.db.campaign.output_file))

    def get_file(self, file_, local_path='', attempts=10):
        if self.options.debug:
            print(colored('getting file...', 'blue'), end='')
            stdout.flush()
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        for attempt in range(attempts):
            try:
                with timeout(60):
                    if self.options.rsa:
                        ssh.connect(self.ip_address, port=self.scp_port,
                                    username=self.username, pkey=self.rsakey,
                                    allow_agent=False, look_for_keys=False)
                    else:
                        ssh.connect(self.ip_address, port=self.scp_port,
                                    username=self.username,
                                    password=self.password, allow_agent=False,
                                    look_for_keys=False)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as error:
                self.__attempt_exception(
                    attempt, attempts, error, 'SSH error',
                    'Error receiving file')
            else:
                try:
                    with timeout(60):
                        dut_scp = SCPClient(ssh.get_transport())
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as error:
                    self.__attempt_exception(
                        attempt, attempts, error, 'SCP error',
                        'Error receiving file', [ssh])
                else:
                    try:
                        with timeout(300):
                            dut_scp.get(file_, local_path=local_path)
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
                    except Exception as error:
                        self.__attempt_exception(
                            attempt, attempts, error, 'SCP error',
                            'Error receiving file', [dut_scp, ssh])
                    else:
                        dut_scp.close()
                        ssh.close()
                        file_path = join(local_path, file_.split('/')[-1])
                        if exists(file_path):
                            if self.options.debug:
                                print(colored('done', 'blue'))
                            self.db.log_event(
                                'Information', 'DUT' if not self.aux else 'AUX',
                                'Received file', file_)
                            return file_path
                        else:
                            self.db.log_event(
                                'Warning' if attempt < attempts-1 else 'Error',
                                'DUT' if not self.aux else 'AUX',
                                'Missing file', local_path)
                            print(colored(
                                '{}: Error receiving file (attempt {}/{}): '
                                'missing file'.format(
                                    self.serial.port, attempt+1, attempts),
                                'red'))
                            if attempt < attempts-1:
                                sleep(30)
                            else:
                                raise DrSEUsError('Missing file')

    def write(self, string):
        self.serial.write(bytes(string, encoding='utf-8'))
        self.start_timer()

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
                with timeout(self.options.timeout+5):
                    char = self.serial.read().decode('utf-8', 'replace')
            except SerialException:
                errors += 1
                self.db.log_event(
                    'Error', 'DUT' if not self.aux else 'AUX', 'Read error',
                    self.db.log_exception)
                self.close()
                self.open()
                continue
            except TimeoutException:
                char = ''
            if not char:
                hanging = True
                self.db.log_event(
                    'Error', 'DUT' if not self.aux else 'AUX', 'Read timeout',
                    self.db.log_trace)
                if continuous:
                    continue
                else:
                    break
            if self.db.result is None:
                if self.aux:
                    self.db.campaign.aux_output += char
                else:
                    self.db.campaign.dut_output += char
            else:
                if self.aux:
                    self.db.result.aux_output += char
                else:
                    self.db.result.dut_output += char
            if self.options.debug:
                print(colored(char, 'green' if not self.aux else 'cyan'),
                      end='')
                if flush:
                    stdout.flush()
            buff += char
            if not continuous and buff.endswith(string):
                returned = True
                break
            elif buff.endswith('autoboot: ') and self.uboot_command:
                self.write('\n{}\n'.format(self.uboot_command))
                self.db.log_event(
                    'Information', 'DUT' if not self.aux else 'AUX', 'Command',
                    self.uboot_command)
            elif buff.endswith('login: '):
                self.write('{}\n'.format(self.username))
                self.db.log_event(
                    'Information', 'DUT' if not self.aux else 'AUX',
                    'Logged in', self.username)
                if not boot:
                    errors += 1
            elif buff.endswith('Password: '):
                self.write('{}\n'.format(self.password))
            elif buff.endswith('can\'t get kernel image'):
                self.write('reset\n')
                self.db.log_event(
                    'Information', 'DUT' if not self.aux else 'AUX', 'Command',
                    'reset')
                errors += 1
            for message, category in self.error_messages:
                if buff.endswith(message):
                    if boot:
                        if category in ('Reboot', 'Missing file'):
                            continue
                    elif not continuous:
                        self.serial.timeout = 30
                        errors += 1
                    event_buff = buff.replace(event_buff_logged, '')
                    self.db.log_event(
                        'Warning' if boot else 'Error',
                        'DUT' if not self.aux else 'AUX', category, event_buff)
                    event_buff_logged += event_buff
            if not continuous and errors > 10:
                break
            if not boot and buff and buff.endswith('\n'):
                if self.db.result is None:
                    self.db.campaign.save()
                else:
                    self.db.result.save()
        self.stop_timer()
        if self.serial.timeout != self.options.timeout:
            try:
                self.serial.timeout = self.options.timeout
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except:
                self.db.log_event(
                    'Error', 'DUT' if not self.aux else 'AUX',
                    'Error resetting timeout', self.db.log_exception)
                self.close()
                self.open()
        if self.options.debug:
            print()
        if 'drseus_detected_errors:' in buff:
            for line in buff.split('\n'):
                if 'drseus_detected_errors:' in line:
                    if self.db.result.detected_errors is None:
                        self.db.result.detected_errors = 0
                    # TODO: use regular expression
                    self.db.result.detected_errors += \
                        int(line.replace('drseus_detected_errors:', ''))
        if self.db.result is None:
            self.db.campaign.save()
        else:
            self.db.result.save()
        if errors:
            for message, category in self.error_messages:
                if not (boot and category in ('Error booting', 'Reboot',
                                              'Missing file')) and \
                        message in buff:
                    raise DrSEUsError(category, returned=returned)
        if hanging:
            raise DrSEUsError('Hanging', returned=returned)
        if boot:
            self.db.log_event(
                'Information', 'DUT' if not self.aux else 'AUX', 'Booted')
        return buff, returned

    def command(self, command='', flush=True, attempts=5):
        event = self.db.log_event(
            'Information', 'DUT' if not self.aux else 'AUX', 'Command',
            command, success=False)
        for attempt in range(attempts):
            self.write('{}\n'.format(command))
            buff, returned = self.read_until(flush=flush)
            if command and command not in buff and not regex(  # sorry not sorry
                    escape('_____'.join(command)).replace('_____', '.*'),
                    DOTALL).search(buff):
                if attempt < attempts-1:
                    self.db.log_event(
                        'Warning', 'DUT' if not self.aux else 'AUX',
                        'Command error', buff)
                    sleep(5)
                else:
                    raise DrSEUsError('{} Command error'.format(
                        'DUT' if not self.aux else 'AUX'), returned=returned)
            else:
                event.success = True
                event.timestamp = datetime.now()
                event.save()
                break
        return buff, returned

    def do_login(self, change_prompt=False, flush=True):
        try:
            self.serial.timeout = 60
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            self.db.log_event(
                'Error', 'DUT' if not self.aux else 'AUX',
                'Error setting timeout', self.db.log_exception)
            self.close()
            self.open()
        self.read_until(boot=True, flush=flush)
        if change_prompt:
            self.write('export PS1=\"DrSEUs# \"\n')
            self.read_until('export PS1=\"DrSEUs# \"')
            self.prompt = 'DrSEUs# '
            self.read_until()
        if self.login_command:
            self.command(self.login_command, flush=flush)
        if self.options.rsa:
            self.command('mkdir ~/.ssh', flush=flush)
            self.command('touch ~/.ssh/authorized_keys', flush=flush)
            self.command('echo "ssh-rsa {}" > ~/.ssh/authorized_keys'.format(
                self.rsakey.get_base64()), flush=flush)
        if self.db.campaign.simics:
            self.command('ip addr add {}/24 dev eth0'.format(self.ip_address),
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
        self.send_files()

    def local_diff(self):
        command = 'diff gold_{0} {0}'.format(self.db.campaign.output_file)
        buff = self.command(command)[0].replace('\r\n', '\n')
        buff = buff.replace('{}\n'.format(command), '')
        buff = buff.replace(self.prompt, '')
        if buff != '':
            return False
        else:
            return True
