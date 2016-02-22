#!/usr/bin/env python3

from argparse import ArgumentParser, REMAINDER

import utilities

# TODO: use postgresql arrays
# TODO: use regular expressions in telnet expect in jtag
# TODO: add unique id to campaign and add capability to merge campaign results
# TODO: add options for custom error messages
# TODO: use formatting strings
# TODO: add mode to redo injection iteration
# TODO: add fallback to power cycle when resetting dut
# TODO: add support for injection of multi-bit upsets

parser = ArgumentParser(
    description='The Dynamic Robust Single Event Upset Simulator '
                'was created by Ed Carlisle IV',
    epilog='Begin by creating a new campaign with "%(prog)s new APPLICATION". '
           'Then run injections with "%(prog)s inject".')
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
         'discover')

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
    dest='dut_username',
    default='root',
    help='device username [default=root]')
dut_settings.add_argument(
    '--pass',
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
    dest='aux_username',
    default='root',
    help='device username [default=root]')
aux_settings.add_argument(
    '--aux_pass',
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
    '--debugger_ip',
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

power_settings = parser.add_argument_group('web power switch settings')
power_settings.add_argument(
    '--power_ip',
    metavar='ADDRESS',
    dest='power_switch_ip_address',
    default='10.42.0.60',
    help='IP address for web power switch [default=10.42.0.60]')
power_settings.add_argument(
    '--power_user',
    metavar='USERNAME',
    dest='power_switch_username',
    default='admin',
    help='username for web power switch [default=admin]')
power_settings.add_argument(
    '--power_pass',
    metavar='PASSWORD',
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
    dest='use_aux_output',
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
new_campaign.set_defaults(func=utilities.create_campaign)

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
    help='list of targets for injection')
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
inject.set_defaults(func=utilities.inject_campaign)

supervise = subparsers.add_parser(
    'supervise', aliases=['s'],
    help='run interactive supervisor',
    description='run interactive supervisor')
supervise.add_argument(
    '-c', '--capture',
    action='store_true',
    help='run remote packet capture')
supervise.set_defaults(func=utilities.launch_supervisor)

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
log_viewer.set_defaults(func=utilities.view_logs)

power = subparsers.add_parser(
    'power', aliases=['p'],
    help='control web power switch',
    description='control web power switch')
power_subparsers = power.add_subparsers(
    title='web power switch commands',
    description='Run "%(prog)s COMMAND -h" to get additional help for '
                'each command',
    metavar='COMMAND', dest='power_command')
detect_devices = power_subparsers.add_parser(
    'detect', aliases=['d', 'D'],
    help='detect devices attached to web power switch',
    description='detect devices attached to web power switch')
detect_devices.set_defaults(func=utilities.detect_power_switch_devices)
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
power_set.set_defaults(func=utilities.set_outlet)
power_list = power_subparsers.add_parser(
    'list', aliases=['l', 'ls'],
    help='list outlet statuses',
    description='list outlet statuses')
power_list.set_defaults(func=utilities.list_outlets)

list_campaigns = subparsers.add_parser(
    'list', aliases=['ls'],
    help='list campaigns',
    description='list campaigns')
list_campaigns.set_defaults(func=utilities.list_campaigns)

delete = subparsers.add_parser(
    'delete', aliases=['d'],
    description='delete results and campaigns',
    help='delete results and campaigns')
delete.add_argument(
    'delete',
    choices=['results', 'campaign', 'all', 'r', 'c', 'a'],
    help='delete {results, r} for the selected campaign, '
         'delete selected {campaign, c} and its results, '
         'or delete {all, a} campaigns and results')
delete.set_defaults(func=utilities.delete)

merge = subparsers.add_parser(
    'merge', aliases=['m'],
    help='merge campaigns',
    description='merge campaigns')
merge.add_argument(
    'directory',
    metavar='DIRECTORY',
    help='merge campaigns from external DIRECTORY into the local directory')
merge.set_defaults(func=utilities.merge_campaigns)

openocd = subparsers.add_parser(
    'openocd', aliases=['o'],
    help='launch openocd for DUT (only supported for ZedBoards)',
    description='launch openocd for DUT (only supported for ZedBoards)')
openocd.set_defaults(func=utilities.launch_openocd)

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
regenerate.set_defaults(func=utilities.regenerate)

update = subparsers.add_parser(
    'update', aliases=['u'],
    help='update gold checkpoint dependency paths '
         '(only supported for Simics campaigns)',
    description='update gold checkpoint dependency paths '
                '(only supported for Simics campaigns)')
update.set_defaults(func=utilities.update_dependencies)

backup = subparsers.add_parser(
    'backup', aliases=['b'],
    help='backup the results database',
    description='backup the results database')
backup.set_defaults(func=utilities.backup_database)

backup = subparsers.add_parser(
    'clean', aliases=['c'],
    help='delete database backups and injected checkpoints',
    description='delete database backups and injected checkpoints')
backup.set_defaults(func=utilities.clean)

serials = subparsers.add_parser(
    'serials', aliases=['sn'],
    help='print serial numbers for currently connect devices',
    description='print serial numbers for currently connect devices')
serials.set_defaults(func=utilities.list_serials)

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
django.set_defaults(func=utilities.run_django_command)

options = parser.parse_args()

if options.command is None:
    parser.error('no command specified, run with -h for help')
if options.command == 'n':
    options.command = 'new'
elif options.command == 'i':
    options.command = 'inject'
elif options.command == 's':
    options.command = 'supervise'
elif options.command == 'o':
    options.command = 'openocd'
elif options.command == 'd':
    options.command = 'delete'
elif options.command == 'r':
    options.command = 'regenerate'

if options.command == 'new':
    if options.arguments:
        options.arguments = ' '.join(options.arguments)
    if options.aux_arguments:
        options.aux_arguments = ' '.join(options.aux_arguments)
elif options.command in ('inject', 'supervise', 'delete', 'regenerate'):
    if not (options.command == 'delete' and options.delete in ('a', 'all')):
        if not options.campaign_id:
            options.campaign_id = \
                utilities.get_campaign(options.campaign_id)['id']
        if options.command != 'regenerate':
            options.architecture = \
                utilities.get_campaign(options.campaign_id)['architecture']

if options.command in ('new', 'inject', 'supervise'):
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

options.func(options)
