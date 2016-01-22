#!/usr/bin/env python3
from argparse import ArgumentParser

import utilities

# TODO: add option for device password
# TODO: add options for custom error messages
# TODO: use formatting strings
# TODO: add ip address override
# TODO: remove output image buttons if not needed from log viewer result page
# TODO: move rsakey back into campaign_data/db
# TODO: add boot commands option
# TODO: add modes to backup database and delete backups
# TODO: add mode to redo injection iteration
# TODO: add fallback to power cycle when resetting dut
# TODO: add support for injection of multi-bit upsets
# TODO: add option for number of times to rerun app for latent fault case
# TODO: change Exception in simics.py to DrSEUsError

parser = ArgumentParser(
    description='The Dynamic Robust Single Event Upset Simulator '
                'was created by Ed Carlisle IV',
    epilog='Begin by creating a new campaign with "%(prog)s new APPLICATION". '
           'Then run injections with "%(prog)s inject".')
parser.add_argument('-C', '--campaign', action='store', type=int, metavar='ID',
                    dest='campaign_id', default=0,
                    help='campaign to use, defaults to last campaign created')
parser.add_argument('-D', '--debug', action='store_true', dest='debug',
                    help='display device output for parallel injections')
parser.add_argument('-T', '--timeout', action='store', type=int,
                    metavar='SECONDS', dest='timeout', default=300,
                    help='device read timeout [default=300]')
parser.add_argument('--serial', action='store', metavar='PORT',
                    dest='dut_serial_port',
                    help='DUT serial port [p2020 default=/dev/ttyUSB1] '
                         '[a9 default=/dev/ttyACM0] (overridden by Simics)')
parser.add_argument('--baud', action='store', type=int, metavar='RATE',
                    dest='dut_baud_rate', default=115200,
                    help='DUT serial port baud rate [default=115200]')
parser.add_argument('--scp', action='store', type=int, metavar='PORT',
                    dest='dut_scp_port', default=22,
                    help='DUT scp port [default=22] (overridden by Simics)')
parser.add_argument('--prompt', action='store', metavar='PROMPT',
                    dest='dut_prompt',
                    help='DUT console prompt [p2020 default=root@p2020rdb:~#] '
                         '[a9 default=[root@ZED]#] (overridden by Simics)')
parser.add_argument('--user', action='store', dest='username', default='root',
                    help='device username')
parser.add_argument('--pass', action='store', dest='password', default='chrec',
                    help='device password')
parser.add_argument('--uboot', action='store', metavar='COMMAND',
                    dest='dut_uboot', default='', help='DUT u-boot command')
parser.add_argument('--aux_serial', action='store', metavar='PORT',
                    dest='aux_serial_port',
                    help='AUX serial port [p2020 default=/dev/ttyUSB1] '
                         '[a9 default=/dev/ttyACM0] (overridden by Simics)')
parser.add_argument('--aux_baud', action='store', type=int, metavar='RATE',
                    dest='aux_baud_rate', default=115200,
                    help='AUX serial port baud rate [default=115200]')
parser.add_argument('--aux_scp', action='store', type=int, metavar='PORT',
                    dest='aux_scp_port', default=22,
                    help='AUX scp port [default=22] (overridden by Simics)')
parser.add_argument('--aux_prompt', action='store', metavar='PROMPT',
                    dest='aux_prompt',
                    help='AUX console prompt [p2020 default=root@p2020rdb:~#] '
                         '[a9 default=[root@ZED]#] (overridden by Simics)')
parser.add_argument('--aux_uboot', action='store', metavar='COMMAND',
                    dest='aux_uboot', default='', help='AUX u-boot command')
parser.add_argument('--debugger_ip', action='store', metavar='ADDRESS',
                    dest='debugger_ip_address', default='10.42.0.50',
                    help='debugger ip address [default=10.42.0.50] '
                         '(ignored by Simics and ZedBoards)')
parser.add_argument('--no_jtag', action='store_false', dest='jtag',
                    help='do not connect to jtag debugger (ignored by Simics)')
subparsers = parser.add_subparsers(
    title='commands',
    description='Run "%(prog)s COMMAND -h" to get additional help for each '
                'command',
    metavar='COMMAND', dest='command')

new_campaign = subparsers.add_parser('new', aliases=['n'],
                                     help='create a new campaign',
                                     description='create a new campaign')
new_campaign.add_argument('application', action='store', metavar='APPLICATION',
                          help='application to run on device')
new_campaign.add_argument('-A', '--arch', action='store',
                          choices=('a9', 'p2020'), dest='architecture',
                          default='p2020',
                          help='target architecture [default=p2020]')
new_campaign.add_argument('-t', '--timing', action='store', type=int,
                          dest='iterations', default=5,
                          help='number of timing iterations to run [default=5]')
new_campaign.add_argument('-a', '--args', action='store', nargs='+',
                          dest='arguments', help='arguments for application')
new_campaign.add_argument('-d', '--dir', action='store', dest='directory',
                          default='fiapps',
                          help='directory to look for files [default=fiapps]')
new_campaign.add_argument('-f', '--files', action='store', nargs='+',
                          metavar='FILE', dest='files',
                          help='files to copy to device')
new_campaign.add_argument('-o', '--output', action='store', dest='file',
                          default='result.dat',
                          help='target application output file '
                               '[default=result.dat]')
new_campaign.add_argument('-x', '--aux', action='store_true', dest='use_aux',
                          help='use auxiliary device during testing')
new_campaign.add_argument('-y', '--aux_app', action='store',
                          metavar='APPLICATION', dest='aux_application',
                          help='target application for auxiliary device')
new_campaign.add_argument('-z', '--aux_args', action='store',
                          metavar='ARGUMENTS', dest='aux_arguments',
                          help='arguments for auxiliary application')
new_campaign.add_argument('-F', '--aux_files', action='store', nargs='+',
                          metavar='FILE', dest='aux_files',
                          help='files to copy to auxiliary device')
new_campaign.add_argument('-O', '--aux_output', action='store_true',
                          dest='use_aux_output',
                          help='use output file from auxiliary device')
new_campaign.add_argument('-k', '--kill_dut', action='store_true',
                          dest='kill_dut',
                          help='send ctrl-c to DUT after auxiliary device '
                               'completes execution')
new_campaign.add_argument('-s', '--simics', action='store_true',
                          dest='use_simics', help='use Simics simulator')
new_simics_campaign = new_campaign.add_argument_group(
    'Simics campaigns', 'Additional options for Simics campaigns only')
new_simics_campaign.add_argument('-c', '--checkpoints', action='store',
                                 type=int, metavar='CHECKPOINTS',
                                 dest='checkpoints', default=50,
                                 help='number of gold checkpoints to target for'
                                      ' creation (actual number of checkpoints '
                                      'may be different) [default=50]')
new_campaign.set_defaults(func=utilities.create_campaign)

inject = subparsers.add_parser('inject', aliases=['i', 'I', 'inj'],
                               help='perform fault injections on a campaign',
                               description='perform fault injections on a '
                                           'campaign')
inject.add_argument('-n', '--iterations', action='store', type=int,
                    dest='iterations',
                    help='number of iterations to perform [default=infinite]')
inject.add_argument('-i', '--injections', action='store', type=int,
                    dest='injections', default=1,
                    help='number of injections per iteration [default=1]')
inject.add_argument('-t', '--targets', action='store', nargs='+',
                    metavar='TARGET', dest='selected_targets',
                    help='list of targets for injection')
inject.add_argument('-p', '--processes', action='store', type=int,
                    dest='processes', default=1,
                    help='number of injections to perform in parallel '
                         '(only supported for ZedBoards and Simics)')
inject_simics = inject.add_argument_group(
    'Simics campaigns', 'Additional options for Simics campaigns only')
inject_simics.add_argument('-a', '--compare_all', action='store_true',
                           dest='compare_all',
                           help='monitor all checkpoints (only last by '
                                'default), IMPORTANT: do NOT use with '
                                '"-p" or "--processes" when using this '
                                'option for the first time in a '
                                'campaign')
inject.set_defaults(func=utilities.inject_campaign)

supervise = subparsers.add_parser('supervise', aliases=['s', 'S'],
                                  help='run interactive supervisor',
                                  description='run interactive supervisor')
supervise.add_argument('-w', '--wireshark', action='store_true', dest='capture',
                       help='run remote packet capture')
supervise.set_defaults(func=utilities.launch_supervisor)

log_viewer = subparsers.add_parser('log', aliases=['l'],
                                   help='start the log web server',
                                   description='start the log web server')
log_viewer.add_argument('-p', '--port', action='store', type=int,
                        dest='port', default=8000,
                        help='log web server port [default=8000]')
log_viewer.set_defaults(func=utilities.view_logs)

zedboards = subparsers.add_parser('zedboards', aliases=['z', 'Z'],
                                  help='print information about attached '
                                       'ZedBoards',
                                  description='print information about '
                                              'attached ZedBoards')
zedboards.set_defaults(func=utilities.print_zedboard_info)

list_campaigns = subparsers.add_parser('list', aliases=['L', 'ls'],
                                       help='list campaigns',
                                       description='list campaigns')
list_campaigns.set_defaults(func=utilities.list_campaigns)

delete = subparsers.add_parser('delete', aliases=['d', 'D'],
                               description='delete results and campaigns',
                               help='delete results and campaigns')
delete.add_argument('delete', action='store',
                    choices=('all', 'results', 'campaign'),
                    help='delete {results} for the selected campaign, '
                         'delete selected {campaign} and its results, '
                         'or delete {all} campaigns and results')
delete.set_defaults(func=utilities.delete)

merge = subparsers.add_parser('merge', aliases=['m', 'M'],
                              help='merge campaigns',
                              description='merge campaigns')
merge.add_argument('directory', action='store', metavar='DIRECTORY',
                   help='merge campaigns from external directory into the '
                        'local directory')
merge.set_defaults(func=utilities.merge_campaigns)

openocd = subparsers.add_parser('openocd', aliases=['o', 'O'],
                                help='launch openocd for DUT '
                                     '(only supported for ZedBoards)',
                                description='launch openocd for DUT '
                                            '(only supported for ZedBoards)')
openocd.set_defaults(func=utilities.launch_openocd)

regenerate = subparsers.add_parser('regenerate', aliases=['r', 'R'],
                                   help='regenerate injected state and launch '
                                        'in Simics (only supported for Simics '
                                        'campaigns)',
                                   description='regenerate injected state and '
                                               'launch in Simics (only '
                                               'supported for Simics '
                                               'campaigns)')
regenerate.add_argument('result_id', action='store', metavar='RESULT_ID',
                        help='result to regenerate')
regenerate.set_defaults(func=utilities.regenerate)

update = subparsers.add_parser('update', aliases=['u', 'U'],
                               help='update gold checkpoint dependency paths '
                                    '(only supported for Simics campaigns)',
                               description='update gold checkpoint dependency '
                                           'paths (only supported for Simics '
                                           'campaigns)')
update.set_defaults(func=utilities.update_dependencies)

backup = subparsers.add_parser('backup', aliases=['b', 'B'],
                               help='backup the results database',
                               description='backup the results database')
backup.set_defaults(func=utilities.backup_database)

options = parser.parse_args()
if options.command is None:
    parser.print_help()
else:
    if options.command != 'new':
        if not options.campaign_id:
            options.campaign_id = utilities.get_last_campaign()
        if options.campaign_id:
            options.architecture = \
                utilities.get_campaign_data(options.campaign_id)['architecture']
    if options.command == 'new' or options.campaign_id:
        if options.architecture == 'p2020':
            if options.dut_serial_port is None:
                options.dut_serial_port = '/dev/ttyUSB1'
            if options.dut_prompt is None:
                options.dut_prompt = 'root@p2020rdb:~#'
            if options.aux_serial_port is None:
                options.aux_serial_port = '/dev/ttyUSB0'
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
    if options.command == 'new' and options.arguments:
        options.arguments = ' '.join(options.arguments)
    options.func(options)
