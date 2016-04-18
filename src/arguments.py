from argparse import ArgumentParser, REMAINDER

parser = ArgumentParser(
    description='The Dynamic Robust Single Event Upset Simulator '
                'was created by Ed Carlisle IV',
    fromfile_prefix_chars='@',
    epilog='Begin by creating a new campaign with "%(prog)s new APPLICATION". '
           'Then run injections with "%(prog)s inject".')
# parser.convert_arg_line_to_args = lambda line: line.split()
parser.add_argument(
    '-C', '--campaign',
    type=int,
    metavar='ID',
    dest='campaign_id',
    default=0,
    help='campaign to use, defaults to last campaign created')
parser.add_argument(
    '-D', '--debug',
    action='store_true',
    help='display device output when performing injections')
parser.add_argument(
    '-T', '--timeout',
    type=int,
    metavar='SECONDS',
    default=300,
    help='device read timeout [default=300]')
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
    '-E', '--error_msg',
    nargs='+',
    dest='error_messages',
    default=[],
    help='error messages to check for in device console output')

dut_settings = parser.add_argument_group('DUT settings')
dut_settings.add_argument(
    '--serial',
    metavar='PORT',
    dest='dut_serial_port',
    help='DUT serial port [p2020 default=/dev/ttyUSB0] '
         '[a9 default=/dev/ttyACM0] (overridden by Simics)')
dut_settings.add_argument(
    '--baud',
    type=int,
    metavar='RATE',
    dest='dut_baud_rate',
    default=115200,
    help='DUT serial port baud rate [default=115200]')
dut_settings.add_argument(
    '--ip',
    metavar='ADDRESS',
    dest='dut_ip_address',
    help='DUT IP address, automatically discover if not specified')
dut_settings.add_argument(
    '--scp',
    type=int,
    metavar='PORT',
    dest='dut_scp_port',
    default=22,
    help='DUT scp port [default=22] (overridden by Simics)')
dut_settings.add_argument(
    '--prompt',
    metavar='PROMPT',
    dest='dut_prompt',
    help='DUT console prompt [p2020 default=root@p2020rdb:~#] '
         '[a9 default=[root@ZED]#] (overridden by Simics)')
dut_settings.add_argument(
    '--user',
    metavar='USERNAME',
    dest='dut_username',
    default='root',
    help='device username [default=root]')
dut_settings.add_argument(
    '--pass',
    metavar='PASSWORD',
    dest='dut_password',
    default='chrec',
    help='device password [default=chrec]')
dut_settings.add_argument(
    '--uboot',
    metavar='COMMAND',
    dest='dut_uboot',
    default='',
    help='DUT u-boot command')
dut_settings.add_argument(
    '--login',
    metavar='COMMAND',
    dest='dut_login',
    default='',
    help='DUT post-login command')

aux_settings = parser.add_argument_group('AUX settings')
aux_settings.add_argument(
    '--aux_serial',
    metavar='PORT',
    dest='aux_serial_port',
    help='AUX serial port [p2020 default=/dev/ttyUSB1] '
         '[a9 default=/dev/ttyACM0] (overridden by Simics)')
aux_settings.add_argument(
    '--aux_baud',
    type=int,
    metavar='RATE',
    dest='aux_baud_rate',
    default=115200,
    help='AUX serial port baud rate [default=115200]')
aux_settings.add_argument(
    '--aux_ip',
    metavar='ADDRESS',
    dest='aux_ip_address',
    help='AUX IP address, automatically discover if not specified')
aux_settings.add_argument(
    '--aux_scp',
    type=int,
    metavar='PORT',
    dest='aux_scp_port',
    default=22,
    help='AUX scp port [default=22] (overridden by Simics)')
aux_settings.add_argument(
    '--aux_prompt',
    metavar='PROMPT',
    dest='aux_prompt',
    help='AUX console prompt [p2020 default=root@p2020rdb:~#] '
         '[a9 default=[root@ZED]#] (overridden by Simics)')
aux_settings.add_argument(
    '--aux_user',
    metavar='USERNAME',
    dest='aux_username',
    default='root',
    help='device username [default=root]')
aux_settings.add_argument(
    '--aux_pass',
    metavar='PASSWORD',
    dest='aux_password',
    default='chrec',
    help='device password [default=chrec]')
aux_settings.add_argument(
    '--aux_uboot',
    metavar='COMMAND',
    dest='aux_uboot',
    default='',
    help='AUX u-boot command')
aux_settings.add_argument(
    '--aux_login',
    metavar='COMMAND',
    dest='aux_login',
    default='',
    help='AUX post-login command')

debugger_settings = parser.add_argument_group('debugger settings')
debugger_settings.add_argument(
    '--jtag_ip',
    metavar='ADDRESS',
    dest='debugger_ip_address',
    default='10.42.0.50',
    help='debugger ip address [default=10.42.0.50] '
         '(ignored by Simics and ZedBoards)')
debugger_settings.add_argument(
    '--no_jtag',
    action='store_false',
    dest='jtag',
    help='do not connect to jtag debugger (ignored by Simics)')
debugger_settings.add_argument(
    '--no_smp',
    action='store_false',
    dest='smp',
    help='do not use SMP mode in openocd (only supported for ZedBoards')

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

power_settings = parser.add_argument_group('web power switch settings')
power_settings.add_argument(
    '--power_ip',
    metavar='ADDRESS',
    dest='power_switch_ip_address',
    default='10.42.0.60',
    help='IP address for web power switch [default=10.42.0.60]')
power_settings.add_argument(
    '--power_user',
    metavar='USER',
    dest='power_switch_username',
    default='admin',
    help='username for web power switch [default=admin]')
power_settings.add_argument(
    '--power_pass',
    metavar='PASS',
    dest='power_switch_password',
    default='chrec',
    help='password for web power switch [default=chrec]')
power_settings.add_argument(
    '--no_power',
    action='store_false',
    dest='power',
    help='do not use web power switch to power cycle devices')

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
    'application',
    metavar='APPLICATION',
    help='application to run on device')
new_campaign.add_argument(
    '-D', '--descr',
    metavar='DESCRIPTION',
    dest='description',
    help='campaign description')
new_campaign.add_argument(
    '-A', '--arch',
    metavar='ARCHITECTURE',
    choices=['a9', 'p2020'],
    dest='architecture',
    default='p2020',
    help='target architecture [default=p2020]')
new_campaign.add_argument(
    '-t', '--timing',
    type=int,
    dest='iterations',
    default=5,
    help='number of timing iterations to run [default=5]')
new_campaign.add_argument(
    '-a', '--args',
    nargs='+',
    metavar='ARGUMENT',
    dest='arguments',
    help='arguments for application')
new_campaign.add_argument(
    '-d', '--dir',
    dest='directory',
    default='fiapps',
    help='directory to look for files [default=fiapps]')
new_campaign.add_argument(
    '-f', '--files',
    nargs='+',
    metavar='FILE',
    help='files to copy to device')
new_campaign.add_argument(
    '-o', '--output',
    dest='output_file',
    default='result.dat',
    help='target application output file [default=result.dat]')
new_campaign.add_argument(
    '-x', '--aux',
    action='store_true',
    help='use auxiliary device during testing')
new_campaign.add_argument(
    '-y', '--aux_app',
    metavar='APPLICATION',
    dest='aux_application',
    help='target application for auxiliary device')
new_campaign.add_argument(
    '-z', '--aux_args',
    nargs='+',
    metavar='ARGUMENT',
    dest='aux_arguments',
    help='arguments for auxiliary application')
new_campaign.add_argument(
    '-F', '--aux_files',
    nargs='+',
    metavar='FILE',
    help='files to copy to auxiliary device')
new_campaign.add_argument(
    '-O', '--aux_output',
    action='store_true',
    dest='aux_output_file',
    help='use output file from auxiliary device')
new_campaign.add_argument(
    '-k', '--kill_dut',
    action='store_true',
    help='send ctrl-c to DUT after auxiliary device completes execution')
new_campaign.add_argument('-s', '--simics', action='store_true',
                          dest='simics', help='use Simics simulator')
new_simics_campaign = new_campaign.add_argument_group(
    'Simics campaigns', 'Additional options for Simics campaigns only')
new_simics_campaign.add_argument(
    '-c', '--checkpoints',
    type=int,
    metavar='CHECKPOINTS',
    default=50,
    help='number of gold checkpoints to target for creation '
         '(actual number of checkpoints may be different) [default=50]')
new_campaign.set_defaults(func='create_campaign')

inject = subparsers.add_parser(
    'inject', aliases=['i'],
    help='perform fault injections on a campaign',
    description='perform fault injections on a campaign')
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
    '-I', '--indices',
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
    '-p', '--processes',
    type=int,
    default=1,
    help='number of injections to perform in parallel '
         '(only supported for ZedBoards and Simics)')
inject_simics = inject.add_argument_group(
    'Simics campaigns', 'Additional options for Simics campaigns only')
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
    '-l', '--local_diff',
    action='store_true',
    help='perform output file diff on device and do not retrieve output file')
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
# supervise.add_argument(
#     '-c', '--capture',
#     action='store_true',
#     help='run remote packet capture')
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
    help='detect devices attached to web power switch',
    description='detect devices attached to web power switch')
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
    'delete',
    choices=['results', 'campaign', 'all', 'r', 'c', 'a'],
    help='delete {results, r} for the selected campaign, '
         'delete selected {campaign, c} and its results, '
         'or delete {all, a} campaigns and results')
delete.add_argument(
    '-U', '--no_del_user',
    action='store_false',
    dest='delete_user',
    help='do not delete database user (drseus) when deleting {all, a}')
delete.set_defaults(func='delete')

# merge = subparsers.add_parser(
#     'merge', aliases=['m'],
#     help='merge campaigns',
#     description='merge campaigns')
# merge.add_argument(
#     'directory',
#     metavar='DIRECTORY',
#     help='merge campaigns from external DIRECTORY into the local directory')
# merge.set_defaults(func='merge_campaigns')

openocd = subparsers.add_parser(
    'openocd', aliases=['o'],
    help='launch openocd for DUT (only supported for ZedBoards)',
    description='launch openocd for DUT (only supported for ZedBoards)')
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
    '-d', '--db',
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
    help='delete database backups and injected checkpoints',
    description='delete database backups and injected checkpoints')
clean.add_argument(
    '-p', '--power_log',
    action='store_true',
    help='delete power switch log')
clean.set_defaults(func='clean')

serials = subparsers.add_parser(
    'serials', aliases=['sn'],
    help='print serial numbers for currently connected devices',
    description='print serial numbers for currently connected devices')
serials.set_defaults(func='list_serials')

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


def get_options():
    options = parser.parse_args()
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
    return options
