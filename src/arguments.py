from argparse import ArgumentParser, REMAINDER
from getpass import getuser, getpass
from platform import system

parser = ArgumentParser(
    description='The Dynamic Robust Single Event Upset Simulator '
                'was created by Ed Carlisle IV',
    fromfile_prefix_chars='@',
    epilog='Create a new campaign with sample configuration: '
           '"%(prog)s @conf/new/p2020". '
           'Then run injections with sample configuration: '
           '"%(prog)s @conf/p2020 inject".')
# parser.convert_arg_line_to_args = lambda line: line.split()
parser.add_argument(
    '-c', '--campaign_id',
    type=int,
    metavar='ID',
    default=0,
    help='campaign to use, defaults to last campaign created')
parser.add_argument(
    '-d', '--description',
    metavar='DESCRIPTION',
    dest='campaign_description',
    help='specify campaign to use by description')
parser.add_argument(
    '--timeout',
    type=int,
    metavar='SECONDS',
    default=300,
    help='device read timeout [default=300]')
parser.add_argument(
    '--attempts',
    type=int,
    metavar='ATTEMPTS',
    default=10,
    help='attempts for retrying actions such as file transfer [default=10]')
parser.add_argument(
    '--reset_ip',
    action='store_true',
    help='forget DUT/AUX IP addresses between resets if using automatic '
         'discovery')
parser.add_argument(
    '--no_rsa',
    action='store_false',
    dest='rsa',
    help='use username/password for SCP authentication instead of RSA key')
parser.add_argument(
    '--socket',
    action='store_true',
    help='retrieve files using "scripts/socket_file_server.py"')
parser.add_argument(
    '--vxworks',
    action='store_true',
    dest='vxworks',
    help='device runs vxworks instead of linux')
parser.add_argument(
    '--error_msg',
    nargs='+',
    dest='error_messages',
    metavar='MSG',
    default=[],
    help='error messages to check for in device console output')
parser.add_argument(
    '--log_error_msg',
    nargs='+',
    dest='log_error_messages',
    metavar='MSG',
    default=[],
    help='error messages to check for in log file')

dut_settings = parser.add_argument_group('DUT settings')
dut_settings.add_argument(
    '--serial',
    metavar='PORT',
    dest='dut_serial_port',
    help='serial port (overridden by Simics)')
dut_settings.add_argument(
    '--dev',
    metavar='SERIAL',
    dest='dut_dev_serial',
    help='UART device serial number')
dut_settings.add_argument(
    '--baud',
    type=int,
    metavar='RATE',
    dest='dut_baud_rate',
    default=115200,
    help='baud rate [default=115200]')
dut_settings.add_argument(
    '--no_rtscts',
    action='store_false',
    dest='dut_rtscts',
    help='disable hardware flow control (RTS/CTS) for serial port '
         '(required for pynq)')
dut_settings.add_argument(
    '--ip',
    metavar='ADDRESS',
    dest='dut_ip_address',
    help='IP address, automatically discover if not specified')
dut_settings.add_argument(
    '--set_ip',
    action='store_true',
    dest='dut_set_ip',
    help='manually set IP address on device')
dut_settings.add_argument(
    '--scp',
    type=int,
    metavar='PORT',
    dest='dut_scp_port',
    default=22,
    help='SCP port [default=22] (overridden by Simics)')
dut_settings.add_argument(
    '--prompt',
    metavar='PROMPT',
    dest='dut_prompt',
    help='console prompt (overridden by Simics)')
dut_settings.add_argument(
    '--user',
    metavar='USERNAME',
    dest='dut_username',
    default='root',
    help='username [default=root]')
dut_settings.add_argument(
    '--pass',
    metavar='PASSWORD',
    dest='dut_password',
    default='',
    help='password')
dut_settings.add_argument(
    '--uboot',
    metavar='COMMAND',
    dest='dut_uboot',
    default='',
    help='u-boot command')
dut_settings.add_argument(
    '--login',
    metavar='COMMAND',
    dest='dut_login',
    default='',
    help='post-login command')
dut_settings.add_argument(
    '--persistent',
    nargs='+',
    metavar='EXECUTABLE',
    dest='dut_persistent_executables',
    default=[],
    help='executable(s) to run in the background')

aux_settings = parser.add_argument_group('AUX settings')
aux_settings.add_argument(
    '--aux_serial',
    metavar='PORT',
    dest='aux_serial_port',
    help='serial port (overridden by Simics)')
aux_settings.add_argument(
    '--aux_dev',
    metavar='SERIAL',
    dest='aux_dev_serial',
    help='UART device serial number')
aux_settings.add_argument(
    '--aux_baud',
    type=int,
    metavar='RATE',
    dest='aux_baud_rate',
    default=115200,
    help='baud rate [default=115200]')
aux_settings.add_argument(
    '--aux_no_rtscts',
    action='store_false',
    dest='aux_rtscts',
    help='disable hardware flow control (RTS/CTS) for serial port')
aux_settings.add_argument(
    '--aux_ip',
    metavar='ADDRESS',
    dest='aux_ip_address',
    help='IP address, automatically discover if not specified')
aux_settings.add_argument(
    '--aux_set_ip',
    action='store_true',
    dest='aux_set_ip',
    help='manually set IP address on device')
aux_settings.add_argument(
    '--aux_scp',
    type=int,
    metavar='PORT',
    dest='aux_scp_port',
    default=22,
    help='SCP port [default=22] (overridden by Simics)')
aux_settings.add_argument(
    '--aux_readonly',
    action='store_true',
    dest='aux_readonly',
    help='auxiliary device is read only')
aux_settings.add_argument(
    '--aux_prompt',
    metavar='PROMPT',
    dest='aux_prompt',
    help='console prompt (overridden by Simics)')
aux_settings.add_argument(
    '--aux_user',
    metavar='USERNAME',
    dest='aux_username',
    default='root',
    help='username [default=root]')
aux_settings.add_argument(
    '--aux_pass',
    metavar='PASSWORD',
    dest='aux_password',
    default='',
    help='password')
aux_settings.add_argument(
    '--aux_uboot',
    metavar='COMMAND',
    dest='aux_uboot',
    default='',
    help='u-boot command')
aux_settings.add_argument(
    '--aux_login',
    metavar='COMMAND',
    dest='aux_login',
    default='',
    help='post-login command')
aux_settings.add_argument(
    '--aux_persistent',
    nargs='+',
    metavar='EXECUTABLE',
    dest='aux_persistent_executables',
    default=[],
    help='executable(s) to run in the background')

debugger_settings = parser.add_argument_group('debugger settings')
debugger_settings.add_argument(
    '--jtag_ip',
    metavar='ADDRESS',
    dest='debugger_ip_address',
    help='debugger ip address (ignored by Simics and openocd)')
debugger_settings.add_argument(
    '--no_jtag',
    action='store_false',
    dest='jtag',
    help='do not connect to jtag debugger (ignored by Simics)')
debugger_settings.add_argument(
    '--no_smp',
    action='store_false',
    dest='smp',
    help='do not use SMP mode in openocd')

database_settings = parser.add_argument_group('PostgreSQL settings')
database_settings.add_argument(
    '--db_host',
    metavar='HOSTNAME',
    default='localhost',
    help='server IP address [default=localhost]')
database_settings.add_argument(
    '--db_port',
    type=int,
    metavar='PORT',
    default=5432,
    help='server port [default=5432]')
database_settings.add_argument(
    '--db_name',
    metavar='NAME',
    default='drseus',
    help='database name [default=drseus]')
database_settings.add_argument(
    '--db_user',
    metavar='USERNAME',
    default='drseus',
    help='username [default=drseus]')
database_settings.add_argument(
    '--db_pass',
    metavar='PASSWORD',
    dest='db_password',
    default='drseus',
    help='password [default=drseus]')
database_settings.add_argument(
    '--db_ask',
    action='store_true',
    help='prompt for password')
database_settings.add_argument(
    '--db_su',
    metavar='USERNAME',
    dest='db_superuser',
    default='postgres',
    help='superuser username [default=postgres]')
database_settings.add_argument(
    '--db_su_pass',
    metavar='PASSWORD',
    dest='db_superuser_password',
    help='password (omit for identity authentication)')
database_settings.add_argument(
    '--db_su_ask',
    action='store_true',
    help='prompt for superuser password')

sqlite_settings = parser.add_argument_group('SQLite settings')
sqlite_settings.add_argument(
    '--sqlite',
    action='store_false',
    dest='db_postgresql',
    help='use SQLite instead of PostgreSQL')
sqlite_settings.add_argument(
    '--db_file',
    metavar='FILE',
    default='campaign-data/db.sqlite',
    help='database file [default=campaign-data/db.sqlite]')

power_settings = parser.add_argument_group('web power switch settings')
power_settings.add_argument(
    '--power_ip',
    metavar='ADDRESS',
    dest='power_switch_ip_address',
    default='192.168.0.60',
    help='IP address')
power_settings.add_argument(
    '--power_user',
    metavar='USER',
    dest='power_switch_username',
    default='admin',
    help='username [default=admin]')
power_settings.add_argument(
    '--power_pass',
    metavar='PASS',
    dest='power_switch_password',
    default='chrec',
    help='password [default=chrec]')

subparsers = parser.add_subparsers(
    title='commands',
    description='Run "%(prog)s COMMAND -h" for additional help',
    metavar='COMMAND',
    dest='command')

new_campaign = subparsers.add_parser(
    'new', aliases=['n'],
    help='create a new campaign',
    description='create a new campaign')
new_campaign.add_argument(
    '-c', '--cmd',
    metavar='COMMAND',
    dest='dut_command',
    default='',
    help='command to run on device')
new_campaign.add_argument(
    '--delay',
    metavar='DELAY',
    type=float,
    help='time (in seconds) to sleep before retrieving output and log files '
         '(only used for campaigns without a command)')
new_campaign.add_argument(
    '-D', '--descr',
    metavar='DESCRIPTION',
    dest='description',
    help='campaign description')
new_campaign.add_argument(
    '-r', '--arch',
    metavar='ARCHITECTURE',
    dest='architecture',
    required=True,
    help='target architecture')
new_campaign.add_argument(
    '-t', '--timing',
    type=int,
    dest='iterations',
    default=5,
    help='number of timing iterations to run [default=5]')
new_campaign.add_argument(
    '-d', '--dir',
    dest='directory',
    default='fiapps',
    help='directory to look for files [default=fiapps]')
new_campaign.add_argument(
    '-f', '--files',
    nargs='+',
    metavar='FILE',
    default=[],
    help='file(s) to copy to device')
new_campaign.add_argument(
    '-o', '--output_file',
    help='output file to retrieve from DUT')
new_campaign.add_argument(
    '-l', '--log_files',
    nargs='+',
    default=[],
    help='log file(s) to retrieve from DUT')
new_aux_campaign = new_campaign.add_argument_group(
    'AUX campaigns',
    'Additional options for campaigns using an AUX device')
new_aux_campaign.add_argument(
    '-x', '--aux_dev',
    action='store_true',
    dest='aux',
    help='use auxiliary device during testing')
new_aux_campaign.add_argument(
    '-C', '--aux_cmd',
    metavar='COMMAND',
    dest='aux_command',
    default='',
    help='command to run on auxiliary device')
new_aux_campaign.add_argument(
    '-F', '--aux_files',
    nargs='+',
    metavar='FILE',
    default=[],
    help='files to copy to auxiliary device')
new_aux_campaign.add_argument(
    '-O', '--aux_output',
    action='store_true',
    dest='aux_output_file',
    help='retrieve output file from AUX instead of DUT')
new_aux_campaign.add_argument(
    '-L', '--aux_log_files',
    nargs='+',
    default=[],
    help='log file(s) to retrieve from AUX')
new_aux_campaign.add_argument(
    '-k', '--kill_dut',
    action='store_true',
    help='send ctrl-c to DUT after AUX completes execution')
new_aux_campaign.add_argument(
    '-K', '--kill_aux',
    action='store_true',
    help='send ctrl-c to AUX after DUT completes execution')
new_simics_campaign = new_campaign.add_argument_group(
    'Simics campaigns',
    'Additional options for Simics campaigns only')
new_simics_campaign.add_argument(
    '-s', '--simics',
    action='store_true',
    help='use Simics simulation')
new_simics_campaign.add_argument(
    '--caches',
    action='store_true',
    help='use cache models')
new_simics_campaign.add_argument(
    '--ckpts',
    type=int,
    metavar='CHECKPOINTS',
    dest='checkpoints',
    default=1000,
    help='number of gold checkpoints to target for creation '
         '(actual number of checkpoints may be different) [default=1000]')
new_campaign.set_defaults(func='create_campaign')

inject = subparsers.add_parser(
    'inject', aliases=['i'],
    help='perform fault injections on a campaign',
    description='perform fault injections on a campaign '
                '(interrupt with ctrl-c)')
inject.add_argument(
    '-d', '--debug',
    action='store_true',
    help='display device output and injection information')
inject.add_argument(
    '-n', '--iterations',
    type=int,
    help='number of iterations to perform [default=infinite]')
inject.add_argument(
    '-i', '--injections',
    type=int,
    dest='injections',
    default=1,
    help='number of injections per iteration [default=1]')
inject.add_argument(
    '-t', '--targets',
    nargs='+',
    metavar='TARGET',
    dest='selected_targets',
    help='selected targets for injection (case insensitive)')
inject.add_argument(
    '-T', '--target_index',
    type=int,
    nargs='+',
    metavar='INDEX',
    dest='selected_target_indices',
    help='selected target indices/cores for injection')
inject.add_argument(
    '-r', '--registers',
    nargs='+',
    metavar='REGISTER',
    dest='selected_registers',
    help='selected registers for injection (case insensitive)')
inject.add_argument(
    '-l', '--latent',
    metavar='ITERATIONS',
    type=int,
    dest='latent_iterations',
    default=1,
    help='execution iterations to perform if latent faults are detected '
         '[default=1]')
inject.add_argument(
    '--log_delay',
    type=float,
    help='periodically retrieve log files from DUT every X seconds')
inject.add_argument(
    '-p', '--processes',
    type=int,
    default=1,
    help='number of injections to perform in parallel '
         '(only supported for openocd and Simics)')
inject_simics = inject.add_argument_group(
    'Simics campaigns',
    'Additional options for Simics campaigns only')
inject_simics.add_argument(
    '-a', '--compare_all',
    action='store_true',
    help='monitor all checkpoints (only last by default), '
         'IMPORTANT: do NOT use with "-p" or "--processes" when using this '
         'option for the first time in a campaign')
inject_simics.add_argument(
    '-x', '--extract',
    action='store_true',
    dest='extract_blocks',
    help='extract diff memory blocks')
inject.set_defaults(func='inject_campaign')

supervise = subparsers.add_parser(
    'supervise', aliases=['s'],
    help='run interactive supervisor',
    description='run interactive supervisor')
supervise.add_argument(
    '--cmd',
    nargs='+',
    metavar='COMMAND',
    dest='command_list',
    help='supervisor commands to queue')
supervise.add_argument(
    '-l', '--local_diff',
    action='store_false',
    help='always retrieve output file to perform diff')
supervise.add_argument(
    '--log_delay',
    type=float,
    help='periodically retrieve log files from DUT every X seconds')
supervise.add_argument(
    '-p', '--power_outlet',
    type=int,
    metavar='OUTLET',
    dest='power_switch_outlet',
    help='web power switch outlet used to power cycle device')
supervise.add_argument(
    '--hist',
    type=int,
    metavar='LINES',
    dest='history_length',
    default=1000,
    help='maximum length for the history file [default=1000]')
supervise.set_defaults(func='launch_supervisor')

log_viewer = subparsers.add_parser(
    'log', aliases=['l'],
    help='start the log web server',
    description='start the log web server')
log_viewer.add_argument(
    '-p', '--port',
    type=int,
    default=8000,
    help='log web server port [default=8000]')
log_viewer.add_argument(
    '-e', '--external',
    action='store_true',
    help='allow connections from external IP addresses')
log_viewer.set_defaults(func='view_log')

detect_devices = subparsers.add_parser(
    'detect', aliases=['d'],
    help='assosciate jtag and uart ports on attached devices',
    description='assosciate jtag and uart ports on attached devices')
detect_devices.set_defaults(func='detect_devices')

power = subparsers.add_parser(
    'power', aliases=['p'],
    help='control web power switch',
    description='control web power switch')
power_subparsers = power.add_subparsers(
    title='web power switch commands',
    description='Run "%(prog)s COMMAND -h" to get additional help for '
                'each command',
    metavar='COMMAND', dest='power_command')
power_detect_devices = power_subparsers.add_parser(
    'detect', aliases=['d'],
    help='detect devices attached to web power switch',
    description='detect devices attached to web power switch')
power_detect_devices.set_defaults(func='detect_power_switch_devices')
power_set = power_subparsers.add_parser(
    'set', aliases=['s'],
    help='set outlet status',
    description='set outlet status')
power_set.add_argument(
    'outlet',
    metavar='OUTLET',
    help='outlet number (or name) to turn on/off')
power_set.add_argument(
    'state',
    metavar='STATE',
    choices=['on', 'off'],
    help='state to set outlet to (on/off)')
power_set.set_defaults(func='set_outlet')
power_list = power_subparsers.add_parser(
    'list', aliases=['ls'],
    help='list outlet statuses',
    description='list outlet statuses')
power_list.set_defaults(func='list_outlets')

list_campaigns = subparsers.add_parser(
    'list', aliases=['ls'],
    help='list campaigns',
    description='list campaigns')
list_campaigns.set_defaults(func='list_campaigns')

delete = subparsers.add_parser(
    'delete', aliases=['del'],
    description='delete results and campaigns',
    help='delete results and campaigns')
delete.add_argument(
    'selection',
    metavar='SELECTION',
    choices=['results', 'campaign', 'all', 'r', 'c', 'a'],
    help='delete {results, r} for the selected campaign, '
         'delete selected {campaign, c} and its results, '
         'or delete {all, a} campaigns and results')
delete.add_argument(
    '-u', '--no_del_user',
    action='store_false',
    dest='delete_user',
    help='do not delete database user (drseus) when deleting {all, a}')
delete.set_defaults(func='delete')

openocd = subparsers.add_parser(
    'openocd', aliases=['o'],
    help='launch openocd for DUT (only supported for openocd)',
    description='launch openocd for DUT (only supported for openocd)')
openocd.add_argument(
    '-g', '--gdb',
    action='store_true',
    help='enable GDB port')
openocd.set_defaults(func='launch_openocd')

regenerate = subparsers.add_parser(
    'regenerate', aliases=['r'],
    help='regenerate injected state and launch in Simics '
         '(only supported for Simics campaigns)',
    description='regenerate injected state and launch in Simics '
                '(only supported for Simics campaigns)')
regenerate.add_argument(
    'result_id',
    metavar='RESULT_ID',
    help='result to regenerate')
regenerate.set_defaults(func='regenerate')

update = subparsers.add_parser(
    'update', aliases=['u'],
    help='update gold checkpoint dependency paths '
         '(only supported for Simics campaigns)',
    description='update gold checkpoint dependency paths '
                '(only supported for Simics campaigns)')
update.set_defaults(func='update_dependencies')

backup = subparsers.add_parser(
    'backup', aliases=['b'],
    help='backup campaign-data, gold-checkpoints, and database',
    description='backup campaign-data, gold-checkpoints, and database')
backup.add_argument(
    '-d', '--db_only',
    action='store_false',
    dest='files',
    help='dump database only')
backup.set_defaults(func='backup')

restore = subparsers.add_parser(
    'restore', aliases=['R'],
    help='restore campaign-data, gold-checkpoints, and database',
    description='restore campaign-data, gold-checkpoints, and database')
restore.add_argument(
    'backup_file',
    nargs='?',
    metavar='BACKUP_FILE',
    help='backup file to restore')
restore.add_argument(
    '-d', '--db',
    action='store_false',
    dest='files',
    help='restore database dump only')
restore.set_defaults(func='restore')

clean = subparsers.add_parser(
    'clean', aliases=['c'],
    help='clean workspace',
    description='clean workspace')
clean.add_argument(
    '-b', '--backups',
    action='store_true',
    help='delete backups')
clean.add_argument(
    '-m', '--migrations',
    action='store_true',
    help='delete django migrations')
clean.add_argument(
    '-p', '--power_log',
    action='store_true',
    help='delete power switch log')
clean.add_argument(
    '-a', '--all',
    action='store_true',
    help='delete all')
clean.set_defaults(func='clean')

serials = subparsers.add_parser(
    'devices', aliases=['dev'],
    help='print information about currently connected devices',
    description='print information about currently connected devices')
serials.set_defaults(func='list_devices')

django = subparsers.add_parser(
    'django',
    aliases=['dj'],
    help='run a django command',
    description='run a django command')
django.add_argument(
    dest='django_command',
    nargs=REMAINDER,
    metavar='COMMAND',
    help='command to run with django')
django.set_defaults(func='run_django_command')

minicom = subparsers.add_parser(
    'minicom',
    aliases=['m'],
    help='launch DUT in minicom',
    description='launch DUT in minicom')
minicom.set_defaults(func='launch_minicom')


def get_options():
    options = parser.parse_args()
    if not hasattr(options, 'debug'):
        options.debug = True
    if options.command is None:
        parser.error('no command specified, run with "-h" for help')
    if options.command == 'n':
        options.command = 'new'
    elif options.command == 'i':
        options.command = 'inject'
    elif options.command == 's':
        options.command = 'supervise'
    elif options.command == 'o':
        options.command = 'openocd'
    elif options.command == 'del':
        options.command = 'delete'
    elif options.command == 'r':
        options.command = 'regenerate'
    elif options.command == 'p':
        options.command = 'power'
    elif options.command == 'm':
        options.command = 'minicom'
    if system() == 'Darwin' and options.db_superuser == 'postgres':
        options.db_superuser = getuser()
    if options.db_ask:
        options.db_password = getpass(prompt='PostgreSQL password:')
    if options.db_su_ask:
        options.db_superuser_password = \
            getpass(prompt='PostgreSQL superuser password:')
    return options
