from datetime import datetime
from difflib import SequenceMatcher
from ftplib import FTP
from io import StringIO
from os import listdir, makedirs, rename
from os.path import exists, join
from paramiko import AutoAddPolicy, RSAKey, SSHClient
from re import compile as regex
from re import DOTALL, escape
from scp import SCPClient
from serial import Serial
from serial.serialutil import SerialException
from shutil import copy, rmtree
from socket import AF_INET, SOCK_STREAM, socket
from sys import stdout
from termcolor import colored
from time import perf_counter, sleep

from .error import DrSEUsError
from .timeout import timeout, TimeoutException


class dut(object):
    linux_signal_messages = [
        ('drseus_sighandler: SIGSEGV', 'Signal SIGSEGV'),
        ('drseus_sighandler: SIGILL', 'Signal SIGILL'),
        ('drseus_sighandler: SIGBUS', 'Signal SIGBUS'),
        ('drseus_sighandler: SIGFPE', 'Signal SIGFPE'),
        ('drseus_sighandler: SIGABRT', 'Signal SIGABRT'),
        ('drseus_sighandler: SIGIOT', 'Signal SIGIOT'),
        ('drseus_sighandler: SIGTRAP', 'Signal SIGTRAP'),
        ('drseus_sighandler: SIGSYS', 'Signal SIGSYS'),
        ('drseus_sighandler: SIGEMT', 'Signal SIGEMT')
    ]

    vxworks_signal_messages = [
        ('has been deleted due to signal 11', 'Signal SIGSEGV'),
        ('has been deleted due to signal 4', 'Signal SIGILL'),
        ('has been deleted due to signal 10', 'Signal SIGBUS'),
        ('has been deleted due to signal 8', 'Signal SIGFPE'),
        ('has been deleted due to signal 6', 'Signal SIGABRT'),
        ('has been deleted due to signal 5', 'Signal SIGTRAP'),
        ('has been deleted due to signal 34', 'Signal SIGSYS'),
        ('has been deleted due to signal 7', 'Signal SIGEMT'),
        # ('has been deleted due to signal', 'Signal')
    ]

    # define SIGHUP     1    /* hangup */
    # define SIGINT     2    /* interrupt */
    # define SIGQUIT    3    /* quit */
    # define SIGKILL    9    /* kill */
    # define SIGFMT     12   /* STACK FORMAT ERROR (not posix) */
    # define SIGPIPE    13   /* write on a pipe with no one to read it */
    # define SIGALRM    14   /* alarm clock */
    # define SIGTERM    15   /* software termination signal from kill */
    # define SIGCNCL    16   /* pthreads cancellation signal */
    # define SIGSTOP    17   /* sendable stop signal not from tty */
    # define SIGTSTP    18   /* stop signal from tty */
    # define SIGCONT    19   /* continue a stopped process */
    # define SIGCHLD    20   /* to parent on child stop or exit */
    # define SIGTTIN    21   /* to readers pgrp upon background tty read */
    # define SIGTTOU    22   /* like TTIN for output if (tp->t_local&LTOSTOP) */
    # define SIGRES1    23   /* reserved signal number (Not POSIX) */
    # define SIGRES2    24   /* reserved signal number (Not POSIX) */
    # define SIGRES3    25   /* reserved signal number (Not POSIX) */
    # define SIGRES4    26   /* reserved signal number (Not POSIX) */
    # define SIGRES5    27   /* reserved signal number (Not POSIX) */
    # define SIGRES6    28   /* reserved signal number (Not POSIX) */
    # define SIGRES7    29   /* reserved signal number (Not POSIX) */
    # define SIGUSR1    30   /* user defined signal 1 */
    # define SIGUSR2    31   /* user defined signal 2 */
    # define SIGPOLL    32   /* pollable event */
    # define SIGPROF    33   /* profiling timer expired */
    # define SIGURG     35   /* high bandwidth data is available at socket */
    # define SIGVTALRM  36   /* virtual timer expired */
    # define SIGXCPU    37   /* CPU time limit exceeded */
    # define SIGXFSZ    38   /* file size time limit exceeded */
    # define SIGEVTS    39   /* signal event thread send */
    # define SIGEVTD    40   /* signal event thread delete */
    # define SIGRTMIN   48   /* Realtime signal min */
    # define SIGRTMAX   63   /* Realtime signal max */

    error_messages = [
        ('Segmentation fault', 'Segmentation fault'),
        ('Illegal instruction', 'Illegal instruction'),

        # VxWorks
        ('has had a failure and has been deleted', 'Failure'),
        ('Copyright Wind River Systems, Inc.', 'Reboot'),

        ('command not found', 'Invalid command'),
        ('Unknown command', 'Invalid command'),
        ('No such file or directory', 'Missing file on device'),

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
        ('-[ cut here ]-', 'Kernel error'),

        # uboot
        ('Hit any key to stop autoboot:', 'Reboot'),
        ('Booting Linux', 'Reboot'),

        ('can\'t get kernel image', 'Error booting'),
        ('Waiting for PHY auto negotiation to complete......... TIMEOUT !',
         'Error booting')]

    def __init__(self, database, options, aux=False):
        self.db = database
        self.options = options
        self.aux = aux
        self.__start_time = None
        self.__timer_value = 0
        self.ip_address = options.dut_ip_address if not aux \
            else options.aux_ip_address
        self.set_ip = options.dut_set_ip if not aux \
            else options.aux_set_ip
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
        for message in reversed(self.vxworks_signal_messages if options.vxworks
                                else self.linux_signal_messages):
            self.error_messages.insert(0, message)
        for message in reversed(options.error_messages):
            self.error_messages.insert(0, (message, message))
        self.open()

    def __str__(self):
        return ('Serial Port: {}\n\tTimeout: {} seconds\n\tPrompt: "{}"\n\t'
                'IP Address: {}\n\t{}: {}').format(
                    self.serial.port, self.serial.timeout, self.prompt,
                    self.ip_address,
                    'Socket File Server Ports' if self.options.socket
                    else 'SCP Port', '60123, 60124' if self.options.socket
                    else self.scp_port)

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

    def set_time(self):
        if self.options.vxworks:
            pass
        else:
            self.command('{}date {}'.format(
                'sudo ' if self.username != 'root' else '',
                datetime.now().strftime('%m%d%H%M%Y.%S')))

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
                        char = self.serial.read().decode(
                            'utf-8', 'replace').replace('\x00', '')
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

        def send_socket():
            for file_ in files:
                with socket(AF_INET, SOCK_STREAM) as sock:
                    sock.connect((self.ip_address, 60124))
                    sock.sendall('{}\n'.format(
                        file_.split('/')[-1]).encode('utf-8'))
                with socket(AF_INET, SOCK_STREAM) as sock:
                    sock.connect((self.ip_address, 60124))
                    with open(file_, 'rb') as file_to_send:
                        sock.sendall(file_to_send.read())
            if self.options.debug:
                print(colored('done', 'blue'))
            self.db.log_event(
                'Information', 'DUT' if not self.aux else 'AUX',
                'Sent files using socket file server', ', '.join(files))

        def send_ftp():
            for attempt in range(attempts):
                try:
                    with timeout(30):
                        ftp = FTP(self.ip_address, timeout=30)
                        ftp.login(self.username, self.password)
                        ftp.cwd('/ram0')
                        for file_ in files:
                            with open(file_, 'rb') as file_to_send:
                                ftp.storbinary(
                                    'STOR {}'.format(file_.split('/')[-1]),
                                    file_to_send)
                        ftp.quit()
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as error:
                    self.__attempt_exception(
                        attempt, attempts, error, 'FTP error',
                        'Error sending file(s)')
                else:
                    if self.options.debug:
                        print(colored('done', 'blue'))
                    self.db.log_event(
                        'Information', 'DUT' if not self.aux else 'AUX',
                        'Sent files using FTP', ', '.join(files))

        def send_scp():
            ssh = SSHClient()
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            for attempt in range(attempts):
                try:
                    with timeout(30):
                        if self.options.rsa:
                            ssh.connect(self.ip_address, port=self.scp_port,
                                        username=self.username,
                                        pkey=self.rsakey, allow_agent=False,
                                        look_for_keys=False)
                        else:
                            ssh.connect(self.ip_address, port=self.scp_port,
                                        username=self.username,
                                        password=self.password,
                                        allow_agent=False, look_for_keys=False)
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
                                'Sent files using SCP', ', '.join(files))
                            break

        # def send_files(self, files=None, attempts=10):
        rename_gold = False
        if not files:
            files = []
            location = 'campaign-data/{}/{}-files'.format(
                self.db.campaign.id, 'aux' if self.aux else 'dut')
            if exists(location):
                for item in listdir(location):
                    files.append(join(location, item))
            else:
                if self.aux:
                    campaign_files = self.options.aux_files
                else:
                    campaign_files = self.options.files
                for file_ in campaign_files:
                    files.append(join(self.options.directory, file_))
                makedirs(location)
                if files:
                    if self.options.debug:
                        print(colored('copying {} campaign file(s)...'.format(
                            'AUX' if self.aux else 'DUT'), 'blue'), end='')
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
        elif not isinstance(files, list):
            files = [files]
        if not files:
            return
        if self.options.debug:
            print(colored('sending {} file(s)...'.format(
                'AUX' if self.aux else 'DUT'), 'blue'), end='')
            stdout.flush()
        if self.options.socket:
            send_socket()
        elif self.options.vxworks:
            send_ftp()
        else:
            send_scp()
        if rename_gold:
            self.command('mv {0} gold_{0}'.format(self.db.campaign.output_file))

    def get_file(self, file_, local_path='', delete=False, attempts=10,
                 quiet=False):

        def get_socket():
            for attempt in range(attempts):
                try:
                    with timeout(60), \
                            open('{}.tmp'.format(file_path), 'wb') \
                            as file_to_receive, \
                            socket(AF_INET, SOCK_STREAM) as sock:
                        sock.connect((self.ip_address, 60123))
                        sock.sendall('{}{}\n'.format(
                            file_, ' -r' if delete else '').encode('utf-8'))
                        data = sock.recv(4096)
                        while data:
                            file_to_receive.write(data)
                            data = sock.recv(4096)
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as error:
                    self.__attempt_exception(
                        attempt, attempts, error, 'Socket file server error',
                        'Error receiving file')
                else:
                    if exists('{}.tmp'.format(file_path)):
                        rename('{}.tmp'.format(file_path), file_path)
                    if self.options.debug and not quiet:
                        print(colored('done', 'blue'))
                    self.db.log_event(
                        'Information', 'DUT' if not self.aux else 'AUX',
                        'Received file using socket file server', file_)
                    return file_path

        def get_ftp():
            for attempt in range(attempts):
                try:
                    with timeout(60):
                        ftp = FTP(self.ip_address, timeout=30)
                        ftp.login(self.username, self.password)
                        ftp.cwd('/ram0')
                        with open(file_path, 'wb') as file_to_receive:
                            ftp.retrbinary(
                                'RETR {}'.format(file_.split('/')[-1]),
                                lambda data: file_to_receive.write(data))
                        ftp.quit()
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except Exception as error:
                    self.__attempt_exception(
                        attempt, attempts, error, 'FTP error',
                        'Error receiving file')
                else:
                    if self.options.debug and not quiet:
                        print(colored('done', 'blue'))
                    self.db.log_event(
                        'Information', 'DUT' if not self.aux else 'AUX',
                        'Received file using FTP', file_)
                    return file_path

        def get_scp():
            ssh = SSHClient()
            ssh.set_missing_host_key_policy(AutoAddPolicy())
            for attempt in range(attempts):
                try:
                    with timeout(60):
                        if self.options.rsa:
                            ssh.connect(self.ip_address, port=self.scp_port,
                                        username=self.username,
                                        pkey=self.rsakey, allow_agent=False,
                                        look_for_keys=False)
                        else:
                            ssh.connect(self.ip_address, port=self.scp_port,
                                        username=self.username,
                                        password=self.password,
                                        allow_agent=False, look_for_keys=False)
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
                            if exists(file_path):
                                if self.options.debug and not quiet:
                                    print(colored('done', 'blue'))
                                self.db.log_event(
                                    'Information',
                                    'DUT' if not self.aux else 'AUX',
                                    'Received file using SCP', file_)
                                return file_path
                            else:
                                self.db.log_event(
                                    'Warning' if attempt < attempts-1
                                    else 'Error',
                                    'DUT' if not self.aux else 'AUX',
                                    'Received file not found', file_path)
                                print(colored(
                                    '{}: Error receiving file (attempt {}/{}): '
                                    'received file not found'.format(
                                        self.serial.port, attempt+1, attempts),
                                    'red'))
                                if attempt < attempts-1:
                                    sleep(30)
                                else:
                                    raise DrSEUsError('Received file not found')

    # def get_file(self, file_, local_path='', delete=False, attempts=10):
        if self.options.debug and not quiet:
            print(colored('getting file from {}...'.format(
                'AUX' if self.aux else 'DUT'), 'blue'), end='')
            stdout.flush()
        file_path = join(local_path, file_.split('/')[-1])
        if self.options.socket:
            get_socket()
        elif self.options.vxworks:
            get_ftp()
        else:
            get_scp()
        return file_path

    def write(self, string):
        self.serial.write(bytes(string, encoding='utf-8'))
        self.start_timer()

    def read_until(self, string=None, continuous=False, boot=False, flush=True):
        start_time = perf_counter()
        if string is None:
            if boot and self.options.vxworks:
                string = '->'
            else:
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
                    char = self.serial.read().decode(
                        'utf-8', 'replace').replace('\x00', '')
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
                self.write('\n')
                sleep(1)
                self.write('{}\n'.format(self.uboot_command))
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
            elif buff.endswith('[sudo] password for {}: '.format(
                    self.username)):
                self.write('{}\n'.format(self.password))
            elif buff.endswith('can\'t get kernel image'):
                self.write('reset\n')
                self.db.log_event(
                    'Information', 'DUT' if not self.aux else 'AUX', 'Command',
                    'reset')
                errors += 1
            for message, category in self.error_messages:
                if buff.endswith(message):
                    if category == 'Missing file on device' and buff.endswith(
                            "hwclock: can't open '/dev/misc/rtc': "
                            "No such file or directory"):
                        continue
                    if boot:
                        if category == 'Reboot':
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
            if not continuous and errors and \
                    perf_counter() - start_time > self.options.timeout:
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
                if not (boot and category in ('Error booting', 'Reboot')) and \
                        message in buff.replace(
                            "hwclock: can't open '/dev/misc/rtc': "
                            "No such file or directory", ''):
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
        if self.options.vxworks:
            self.command('cmd', flush=flush)
        elif change_prompt:
            self.write('export PS1=\"DrSEUs# \"\n')
            self.read_until('export PS1=\"DrSEUs# \"')
            self.prompt = 'DrSEUs# '
            self.read_until()
        if self.login_command:
            self.command(self.login_command, flush=flush)
        self.set_time()
        if self.options.rsa and not self.options.vxworks:
            self.command('mkdir ~/.ssh', flush=flush)
            self.command('touch ~/.ssh/authorized_keys', flush=flush)
            self.command('echo "ssh-rsa {}" > ~/.ssh/authorized_keys'.format(
                self.rsakey.get_base64()), flush=flush)
        if self.set_ip or self.db.campaign.simics and not self.options.vxworks:
            self.command('ip addr add {}/24 dev eth0'.format(self.ip_address),
                         flush=flush)
            self.command('ip link set eth0 up', flush=flush)
            self.command('ip addr show', flush=flush)
            if self.db.campaign.simics:
                self.ip_address = '127.0.0.1'
        if self.ip_address is None:
            attempts = 10
            for attempt in range(attempts):
                for line in self.command('ifconfig -a' if self.options.vxworks
                                         else 'ip addr show',
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
        if self.options.socket or len(
                self.options.aux_persistent_executables if self.aux
                else self.options.dut_persistent_executables):
            process_list = self.command('ps a')[0]
        if self.options.socket:
            if 'socket_file_server.py' not in self.command('ls -l')[0]:
                self.options.socket = False
                self.send_files('scripts/socket_file_server.py')
                self.options.socket = True
                self.command('./socket_file_server.py &')
                sleep(1)
            elif 'socket_file_server.py' not in process_list:
                self.command('./socket_file_server.py &')
                sleep(1)
        self.send_files()
        for persistent_executable in self.options.aux_persistent_executables \
                if self.aux else self.options.dut_persistent_executables:
            if persistent_executable not in process_list:
                self.command('sudo ./{} &'.format(persistent_executable))

    def check_output(self):
        local_diff = \
            hasattr(self.options, 'local_diff') and self.options.local_diff
        try:
            directory_listing = self.command('ls -l')[0]
        except DrSEUsError as error:
            self.db.result.outcome_category = 'Post execution error'
            self.db.result.outcome = error.type
            return
        if local_diff:
            directory_listing = directory_listing.replace(
                'gold_{}'.format(self.db.campaign.output_file), '')
        if self.db.campaign.output_file not in directory_listing:
            self.db.result.outcome_category = 'Execution error'
            self.db.result.outcome = 'Missing output file'
            return
        if local_diff:
            command = 'diff gold_{0} {0}'.format(self.db.campaign.output_file)
            try:
                buff = self.command(command)[0].replace('\r\n', '\n')
            except DrSEUsError as error:
                self.db.result.outcome_category = 'Post execution error'
                self.db.result.outcome = error.type
                return
            buff = buff.replace('{}\n'.format(command), '')
            buff = buff.replace(self.prompt, '')
            if buff != '':
                self.db.result.data_diff = 0
            else:
                self.db.result.data_diff = 1.0
        if not local_diff or self.db.result.data_diff != 1.0:
            result_folder = 'campaign-data/{}/results/{}'.format(
                self.db.campaign.id, self.db.result.id)
            if not exists(result_folder):
                makedirs(result_folder)
            try:
                self.get_file(self.db.campaign.output_file, result_folder)
            except DrSEUsError as error:
                self.db.result.outcome_category = 'File transfer error'
                self.db.result.outcome = error.type
                if not listdir(result_folder):
                    rmtree(result_folder)
                return
            with open(
                    'campaign-data/{}/gold/{}'.format(
                        self.db.campaign.id, self.db.campaign.output_file),
                    'rb') as solution:
                solutionContents = solution.read()
            with open(join(result_folder, self.db.campaign.output_file),
                      'rb') as result:
                resultContents = result.read()
            self.db.result.data_diff = SequenceMatcher(
                None, solutionContents, resultContents).quick_ratio()
        if self.db.result.data_diff == 1.0:
            if not local_diff:
                rmtree(result_folder)
            if self.db.result.detected_errors:
                self.db.result.outcome_category = 'Data error'
                self.db.result.outcome = 'Corrected data error'
        else:
            self.db.result.outcome_category = 'Data error'
            if self.db.result.detected_errors:
                self.db.result.outcome = 'Detected data error'
            else:
                self.db.result.outcome = 'Silent data error'
        try:
            self.command('rm {}'.format(self.db.campaign.output_file))
        except DrSEUsError as error:
            self.db.result.outcome_category = 'Post execution error'
            self.db.result.outcome = error.type

    def get_logs(self, latent_iteration, background=False):
        result_folder = 'campaign-data/{}/results/{}'.format(
            self.db.campaign.id, self.db.result.id)
        if latent_iteration:
            result_folder += '/latent/{}'.format(latent_iteration)
        if not exists(result_folder):
                makedirs(result_folder)
        for log_file in self.db.campaign.aux_log_files if self.aux \
                else self.db.campaign.log_files:
            try:
                file_path = self.get_file(
                    log_file, result_folder,
                    delete=not background and not log_file.startswith('/'),
                    quiet=background)
            except DrSEUsError:
                if not listdir(result_folder):
                    rmtree(result_folder)
                return
            else:
                if self.db.result.outcome == 'In progress' and \
                        self.options.log_error_messages:
                    with open(file_path, 'r') as log:
                        log_contents = log.read()
                    for message in self.options.log_error_messages:
                        if message in log_contents:
                            self.db.result.outcome_category = 'Log error'
                            self.db.result.outcome = message
                            break
            if not log_file.startswith('/') and not background and \
                    not self.options.socket:
                try:
                    self.command('rm {}'.format(log_file))
                except DrSEUsError as error:
                    self.db.result.outcome_category = 'Post execution error'
                    self.db.result.outcome = error.type
