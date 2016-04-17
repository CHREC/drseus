from getpass import getuser, getpass
from platform import system
from signal import SIGINT
from subprocess import check_output, Popen
from time import sleep

from .arguments import get_options
from . import utilities

# TODO: consider generating event filter choices only once at startup
# TODO: update chart colors
# TODO: only send files if needed
# TODO: use regular expressions in telnet expect in jtag
# TODO: use formatting strings
# TODO: add mode to redo injection iteration
# TODO: add support for injection of multi-bit upsets


def run():
    options = get_options()

    postgresql = None
    if system() == 'Darwin':
        if options.db_superuser == 'postgres':
            options.db_superuser = getuser()
        for line in check_output(['ps'], universal_newlines=True).split('\n'):
            if line and line.split()[3] == 'postgres':
                break
        else:
            postgresql = Popen(['postgres', '-D', '/usr/local/var/postgres'])
            sleep(0.1)

    if options.db_ask:
        options.db_password = getpass(prompt='PostgreSQL password:')
    if options.db_su_ask:
        options.db_superuser_password = \
            getpass(prompt='PostgreSQL superuser password:')

    if options.command == 'new':
        if options.arguments:
            options.arguments = ' '.join(options.arguments)
        if options.aux_arguments:
            options.aux_arguments = ' '.join(options.aux_arguments)
    elif options.command in ('inject', 'supervise', 'delete', 'regenerate',
                             'openocd'):
        if not (options.command == 'delete' and options.delete in ('a', 'all')):
            if not options.campaign_id:
                options.campaign_id = \
                    utilities.get_campaign(options)['id']
            if options.command != 'regenerate':
                options.architecture = \
                    utilities.get_campaign(options)['architecture']

    if options.command in ('new', 'inject', 'supervise', 'openocd'):
        if options.architecture == 'p2020':
            if options.dut_serial_port is None:
                options.dut_serial_port = '/dev/ttyUSB0'
            if options.dut_prompt is None:
                options.dut_prompt = 'root@p2020rdb:~#'
            if options.aux_serial_port is None:
                options.aux_serial_port = '/dev/ttyUSB1'
            if options.aux_prompt is None:
                options.aux_prompt = 'root@p2020rdb:~#'
        elif options.architecture == 'a9':
            if options.dut_serial_port is None:
                options.dut_serial_port = '/dev/ttyACM0'
            if options.dut_prompt is None:
                options.dut_prompt = '[root@ZED]#'
            if options.aux_serial_port is None:
                options.aux_serial_port = '/dev/ttyACM1'
            if options.aux_prompt is None:
                options.aux_prompt = '[root@ZED]#'

    getattr(utilities, options.func)(options)

    if postgresql is not None:
        postgresql.send_signal(SIGINT)
        postgresql.wait(timeout=30)
