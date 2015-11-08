#!/usr/bin/python

from __future__ import print_function
import multiprocessing
import optparse
import os
import shutil
import signal
import sqlite3
import sys

from fault_injector import fault_injector

# TODO: add support for injection of multi-bit upsets
# TODO: add synchronization around injection logging and/or db access
# TODO: add telnet setup for bdi (firmware, configs, etc.)
# TODO: add option for number of times to rerun app for latent fault case
# TODO: change Exception in simics_checkpoints.py to DrSEUsError


def list_campaigns():
    if not os.path.exists('campaign-data/db.sqlite3'):
        raise Exception('could not find campaign data')
    sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    sql.execute('SELECT campaign_number, application, architecture, use_simics '
                'FROM drseus_logging_campaign')
    campaign_list = sql.fetchall()
    sql_db.close()
    print('DrSEUs Campaigns:')
    print('Number\t\tApplication\t\tArchitecture\tSimics')
    for campaign in campaign_list:
        campaign = list(campaign)
        campaign[3] = bool(campaign[3])
        print('\t\t'.join([str(item) for item in campaign]))


def get_last_campaign():
    if (not os.path.exists('campaign-data') or
            not os.path.exists('campaign-data/db.sqlite3')):
        return 0
    sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    sql.execute('SELECT campaign_number FROM drseus_logging_campaign ORDER BY '
                'campaign_number DESC LIMIT 1')
    campaign_data = sql.fetchone()
    if campaign_data is None:
        campaign_number = 0
    else:
        campaign_number = campaign_data['campaign_number']
    sql_db.close()
    return campaign_number


def get_campaign_data(campaign_number):
    if not os.path.exists('campaign-data/db.sqlite3'):
        raise Exception('could not find campaign data')
    sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    sql.execute('SELECT * FROM drseus_logging_campaign WHERE campaign_number=?',
                (campaign_number,))
    campaign_data = sql.fetchone()
    sql_db.close()
    return campaign_data


def get_next_iteration(campaign_number):
    if not os.path.exists('campaign-data/db.sqlite3'):
        raise Exception('could not find campaign data')
    sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    sql.execute('SELECT * FROM drseus_logging_result WHERE '
                'drseus_logging_result.campaign_id = '+str(campaign_number) +
                ' ORDER BY iteration DESC LIMIT 1')
    result_data = sql.fetchone()
    if result_data is None:
        iteration = 0
    else:
        iteration = result_data['iteration']
    sql_db.commit()
    sql_db.close()
    return iteration + 1


def delete_results(campaign_number):
    if os.path.exists('campaign-data/'+str(campaign_number)+'/results'):
        shutil.rmtree('campaign-data/'+str(campaign_number)+'/results')
        print('deleted results')
    if os.path.exists('campaign-data/db.sqlite3'):
        sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
        sql = sql_db.cursor()
        sql.execute('DELETE FROM drseus_logging_simics_register_diff WHERE '
                    'result_id IN (SELECT id FROM drseus_logging_result WHERE '
                    'campaign_id=?)', (campaign_number,))
        sql.execute('DELETE FROM drseus_logging_injection WHERE '
                    'result_id IN (SELECT id FROM drseus_logging_result WHERE '
                    'campaign_id=?)', (campaign_number,))
        sql.execute('DELETE FROM drseus_logging_result WHERE campaign_id=?',
                    (campaign_number,))
        sql_db.commit()
        sql_db.close()
        print('flushed database')
    if os.path.exists('simics-workspace/injected-checkpoints/' +
                      str(campaign_number)):
        shutil.rmtree('simics-workspace/injected-checkpoints/' +
                      str(campaign_number))
        print('deleted injected checkpoints')


def delete_campaign(campaign_number):
    delete_results(campaign_number)
    if os.path.exists('campaign-data/db.sqlite3'):
        sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
        sql = sql_db.cursor()
        sql.execute('DELETE FROM drseus_logging_campaign '
                    'WHERE campaign_number=?',
                    (campaign_number,))
        sql_db.commit()
        sql_db.close()
        print('deleted campaign from database')
    if os.path.exists('campaign-data/'+str(campaign_number)):
        shutil.rmtree('campaign-data/'+str(campaign_number))
        print('deleted campaign data')
    if os.path.exists('simics-workspace/gold-checkpoints/' +
                      str(campaign_number)):
        shutil.rmtree('simics-workspace/gold-checkpoints/' +
                      str(campaign_number))
        print('deleted gold checkpoints')


def new_campaign(options):
    campaign_number = get_last_campaign() + 1
    if options.architecture == 'p2020':
        if options.dut_ip_address is None:
            options.dut_ip_address = '10.42.0.21'
        if options.dut_serial_port is None:
            options.dut_serial_port = '/dev/ttyUSB1'
        if options.dut_prompt is None:
            options.dut_prompt = 'root@p2020rdb:~#'
    elif options.architecture == 'a9':
        if options.dut_ip_address is None:
            options.dut_ip_address = '10.42.0.30'
        if options.dut_serial_port is None:
            options.dut_serial_port = '/dev/ttyACM0'
        if options.dut_prompt is None:
            options.dut_prompt = '[root@ZED]#'
    else:
        raise Exception('invalid architecture: '+options.architecture)
    if options.aux_app:
        aux_application = options.aux_app
    else:
        aux_application = options.application
    if options.directory == 'fiapps':
        if not os.path.exists('fiapps'):
            os.system('./setup_apps.sh')
        if not os.path.exists('fiapps/'+options.application):
            os.system('cd fiapps/; make '+options.application)
    else:
        if not os.path.exits(options.directory):
            raise Exception('cannot find directory '+options.directory)
    if options.use_simics and not os.path.exists('simics-workspace'):
        os.system('./setup_simics_workspace.sh')
    if os.path.exists('campaign-data/'+str(campaign_number)):
        campaign_files = os.listdir('campaign-data/'+str(campaign_number))
        if 'results' in campaign_files:
            campaign_files.remove('results')
        if campaign_files:
            print('previous campaign data exists, continuing will delete it')
            if raw_input('continue? [Y/n]: ') in ['n', 'N', 'no', 'No', 'NO']:
                return
            else:
                shutil.rmtree('campaign-data/'+str(campaign_number))
                print('deleted campaign '+str(campaign_number)+' data')
                if os.path.exists('simics-workspace/gold-checkpoints/' +
                                  str(campaign_number)):
                    shutil.rmtree('simics-workspace/gold-checkpoints/' +
                                  str(campaign_number))
                    print('deleted gold checkpoints')
                if os.path.exists('simics-workspace/injected-checkpoints/' +
                                  str(campaign_number)):
                    shutil.rmtree('simics-workspace/injected-checkpoints/' +
                                  str(campaign_number))
    if not os.path.exists('campaign-data/'+str(campaign_number)):
        os.makedirs('campaign-data/'+str(campaign_number))
    if not os.path.exists('campaign-data/db.sqlite3'):
        os.system('./django-logging/manage.py migrate')
    drseus = fault_injector(campaign_number, options.dut_ip_address,
                            options.aux_ip_address, options.dut_serial_port,
                            options.aux_serial_port, options.dut_prompt,
                            options.aux_prompt, options.debugger_ip_address,
                            options.architecture, options.use_aux,
                            options.debug, options.use_simics, options.seconds)
    drseus.setup_campaign(options.directory, options.architecture,
                          options.application, options.arguments, options.file,
                          options.files, options.aux_files, options.iterations,
                          aux_application, options.aux_args,
                          options.use_aux_output, options.num_checkpoints,
                          options.kill_dut)
    print('\nsuccessfully setup campaign')


def get_injection_data(campaign_data, iteration):
    if not os.path.exists('campaign-data/db.sqlite3'):
        raise Exception('could not find campaign data')
    sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    sql.execute('SELECT register,gold_value,injected_value,checkpoint_number,'
                'bit,target_index,target,config_object,config_type,'
                'register_index,field FROM drseus_logging_injection '
                'INNER JOIN drseus_logging_result ON '
                '(drseus_logging_injection.result_id=drseus_logging_result.id) '
                'WHERE drseus_logging_result.iteration=? AND '
                'drseus_logging_result.campaign_id=?',
                (iteration, campaign_data['campaign_number']))
    injection_data = sql.fetchall()
    sql_db.close()
    injection_data = sorted(injection_data,
                            key=lambda x: x['checkpoint_number'])
    return injection_data


def load_campaign(campaign_data, options):
    if campaign_data['architecture'] == 'p2020':
        if options.dut_ip_address is None:
            options.dut_ip_address = '10.42.0.21'
        if options.dut_serial_port is None:
            options.dut_serial_port = '/dev/ttyUSB1'
        if options.dut_prompt is None:
            options.dut_prompt = 'root@p2020rdb:~#'
    elif campaign_data['architecture'] == 'a9':
        if options.dut_ip_address is None:
            options.dut_ip_address = '10.42.0.30'
        if options.dut_serial_port is None:
            options.dut_serial_port = '/dev/ttyACM0'
        if options.dut_prompt is None:
            options.dut_prompt = '[root@ZED]#'
    drseus = fault_injector(campaign_data['campaign_number'],
                            options.dut_ip_address, options.aux_ip_address,
                            options.dut_serial_port, options.aux_serial_port,
                            options.dut_prompt, options.aux_prompt,
                            options.debugger_ip_address,
                            campaign_data['architecture'],
                            campaign_data['use_aux'], options.debug,
                            campaign_data['use_simics'], options.seconds)
    drseus.command = campaign_data['command']
    drseus.aux_command = campaign_data['aux_command']
    drseus.num_checkpoints = campaign_data['num_checkpoints']
    drseus.cycles_between = campaign_data['cycles_between']
    drseus.exec_time = campaign_data['exec_time']
    drseus.kill_dut = campaign_data['kill_dut']
    return drseus


def perform_injections(campaign_data, iteration_counter, last_iteration,
                       options):
    drseus = load_campaign(campaign_data, options)

    def interrupt_handler(signum, frame):
        drseus.log_result('Interrupted', 'Incomplete')
        if os.path.exists('campaign-data/results/' +
                          str(campaign_data['campaign_number'])+'/' +
                          str(drseus.iteration)):
            shutil.rmtree('campaign-data/results/' +
                          str(campaign_data['campaign_number'])+'/' +
                          str(drseus.iteration))
        if drseus.use_simics:
            if os.path.exists('simics-workspace/injected-checkpoints/' +
                              str(campaign_data['campaign_number'])+'/' +
                              str(drseus.iteration)):
                shutil.rmtree('simics-workspace/injected-checkpoints/' +
                              str(campaign_data['campaign_number'])+'/' +
                              str(drseus.iteration))
        else:
            drseus.debugger.continue_dut()
        drseus.debugger.close()
        sys.exit()
    signal.signal(signal.SIGINT, interrupt_handler)

    if options.selected_targets is not None:
        selected_targets = options.selected_targets.split(',')
    else:
        selected_targets = None
    drseus.inject_and_monitor(iteration_counter, last_iteration,
                              options.num_injections, selected_targets,
                              campaign_data['output_file'],
                              campaign_data['use_aux_output'],
                              options.compare_all)


def view_logs(args):
    try:
        port = int(args[0])
    except:
        port = 8000
    os.system('cd '+os.getcwd()+'/django-logging; ./manage.py runserver ' +
              str(port))

parser = optparse.OptionParser('drseus.py {mode} {options}')

parser.add_option('-N', '--campaign', action='store', type='int',
                  dest='campaign_number', default=0,
                  help='campaign number to use, defaults to last campaign '
                  'created')
parser.add_option('-g', '--debug', action='store_false', dest='debug',
                  default=True,
                  help='display device output')
parser.add_option('-T', '--timeout', action='store', type='int',
                  dest='seconds', default=300,
                  help='device read timeout in seconds [default=300]')
parser.add_option('--dut_ip', action='store', type='str',
                  dest='dut_ip_address', default=None,
                  help='dut ip address [p2020 default=10.42.0.21]              '
                  '[a9 default=10.42.0.30] (overridden by simics)')
parser.add_option('--dut_serial', action='store', type='str',
                  dest='dut_serial_port', default=None,
                  help='dut serial port [p2020 default=/dev/ttyUSB1]           '
                  '[a9 default=/dev/ttyACM0] (overridden by simics)')
parser.add_option('--dut_prompt', action='store', type='str',
                  dest='dut_prompt', default=None,
                  help='dut console prompt [p2020 default=root@p2020rdb:~#]    '
                  '[a9 default=[root@ZED]#] (overridden by simics)')
parser.add_option('--aux_ip', action='store', type='str',
                  dest='aux_ip_address', default='10.42.0.20',
                  help='aux ip address [default=10.42.0.20] '
                  '(overridden by simics)')
parser.add_option('--aux_serial', action='store', type='str',
                  dest='aux_serial_port', default='/dev/ttyUSB0',
                  help='aux serial port [default=/dev/ttyUSB0] '
                  '(overridden by simics)')
parser.add_option('--aux_prompt', action='store', type='str',
                  dest='aux_prompt', default=None,
                  help='aux console prompt [default=root@p2020rdb:~#]  '
                  '(overridden by simics)')
parser.add_option('--debugger_ip', action='store', type='str',
                  dest='debugger_ip_address', default='10.42.0.50',
                  help='debugger ip address [default=10.42.0.50] '
                  '(ignored by simics)')

mode_group = optparse.OptionGroup(parser, 'DrSEUs Modes', 'Specify the desired '
                                  'operating mode')
mode_group.add_option('-b', '--list_campaigns', action='store_true',
                      dest='list', help='list campaigns')
mode_group.add_option('-d', '--delete_results', action='store_true',
                      dest='delete_results', default=False,
                      help='delete results and/or injected checkpoints for a '
                           'campaign')
mode_group.add_option('-e', '--delete_campaign', action='store_true',
                      dest='delete_campaign', default=False,
                      help='delete campaign (results and campaign information)')
mode_group.add_option('-D', '--delete_all', action='store_true',
                      dest='delete_all', default=False,
                      help='delete results and/or injected checkpoints for all '
                           'campaigns')
mode_group.add_option('-c', '--create_campaign', action='store', type='str',
                      dest='application', default=None,
                      help='create a new campaign for the application '
                      'specified')
mode_group.add_option('-i', '--inject', action='store_true', dest='inject',
                      default=False,
                      help='perform fault injections on an existing campaign')
mode_group.add_option('-S', '--supervise', action='store_true',
                      dest='supervise', default=False,
                      help='do not inject faults, only supervise devices')

mode_group.add_option('-l', '--log', action='store_true',
                      dest='view_logs', default=False,
                      help='start the log server')
parser.add_option_group(mode_group)

simics_mode_group = optparse.OptionGroup(parser, 'DrSEUs Modes (Simics only)',
                                         'These modes are only available for '
                                         'Simics campaigns')
simics_mode_group.add_option('-r', '--regenerate', action='store', type='int',
                             dest='iteration', default=-1,
                             help='regenerate a campaign iteration and '
                             'launch in Simics')
parser.add_option_group(simics_mode_group)

new_group = optparse.OptionGroup(parser, 'New Campaign Options',
                                 'Use these to create a new campaign, they will'
                                 ' be saved')
new_group.add_option('-m', '--timing', action='store', type='int',
                     dest='iterations', default=5,
                     help='number of timing iterations to run [default=5]')
new_group.add_option('-o', '--output', action='store', type='str',
                     dest='file', default='result.dat',
                     help='target application output file [default=result.dat]')
new_group.add_option('-a', '--args', action='store', type='str',
                     dest='arguments', default='',
                     help='arguments for application')
new_group.add_option('-L', '--directory', action='store', type='str',
                     dest='directory', default='fiapps',
                     help='directory to look for files [default=fiapps]')
new_group.add_option('-f', '--files', action='store', type='str', dest='files',
                     default='',
                     help='comma-separated list of files to copy to device')
new_group.add_option('-F', '--aux_files', action='store', type='str',
                     dest='aux_files', default='',
                     help='comma-separated list of files to copy to aux device')
new_group.add_option('-A', '--arch', action='store',  choices=['a9', 'p2020'],
                     dest='architecture', default='p2020',
                     help='target architecture [default=p2020]')
new_group.add_option('-s', '--simics', action='store_true', dest='use_simics',
                     default=False, help='use simics simulator')
new_group.add_option('-x', '--aux', action='store_true', dest='use_aux',
                     default=False, help='use second device during testing')
new_group.add_option('-y', '--aux_app', action='store',
                     type='str', dest='aux_app', default='',
                     help='target application for auxiliary device')
new_group.add_option('-z', '--aux_args', action='store', type='str',
                     dest='aux_args', default='',
                     help='arguments for auxiliary application')
new_group.add_option('-O', '--aux_output', action='store_true',
                     dest='use_aux_output', default=False,
                     help='get output file from aux instead of dut')
new_group.add_option('-k', '--kill_dut', action='store_true',
                     dest='kill_dut', default=False,
                     help='send ctrl-c to dut after aux completes execution')
parser.add_option_group(new_group)

new_simics_group = optparse.OptionGroup(parser, 'New Campaign Options '
                                        '(Simics only)', 'Use these for new '
                                        'Simics campaigns')
new_simics_group.add_option('-C', '--checkpoints', action='store', type='int',
                            dest='num_checkpoints', default=50,
                            help='number of gold checkpoints to create '
                                 '[default=50]')
parser.add_option_group(new_simics_group)

injection_group = optparse.OptionGroup(parser, 'Injection Options', 'Use these '
                                       'when performing injections '
                                       '(-i or --inject)')
injection_group.add_option('-I', '--injections', action='store', type='int',
                           dest='num_injections', default=1,
                           help='number of injections per execution run '
                                '[default=1]')
injection_group.add_option('-n', '--iterations', action='store', type='int',
                           dest='num_iterations', default=10,
                           help='number of iterations to perform [default=10]')
injection_group.add_option('-t', '--targets', action='store', type='str',
                           dest='selected_targets', default=None,
                           help='comma-seperated list of targets for injection')
parser.add_option_group(injection_group)

simics_injection_group = optparse.OptionGroup(parser, 'Injection Options '
                                              '(Simics only)', 'Use these when '
                                              'performing injections with '
                                              'Simics')
simics_injection_group.add_option('-p', '--procs', action='store',
                                  type='int', dest='num_processes', default=1,
                                  help='number of simics injections to perform '
                                       'in parallel')
simics_injection_group.add_option('-M', '--all', action='store_true',
                                  dest='compare_all', default=False,
                                  help='monitor all checkpoints (only last by '
                                       'default), IMPORTANT: do NOT use with '
                                       '\"-p\" or \"--procs\" when using this '
                                       'option for the first time in a '
                                       'campaign')
parser.add_option_group(simics_injection_group)

supervise_group = optparse.OptionGroup(parser, 'Supervisor Options', 'Use these'
                                       ' options for supervising '
                                       '(-S or --supervise)')
supervise_group.add_option('-R', '--runtime', action='store', type='int',
                           dest='target_seconds', default=30,
                           help='desired time in seconds to run (calculates '
                                'number of iterations to run) [default=30]')
supervise_group.add_option('-w', '--wireshark', action='store_true',
                           dest='capture', help='run remote packet capture')
parser.add_option_group(supervise_group)
options, args = parser.parse_args()

if options.list:
    list_campaigns()
elif options.delete_all:
    if os.path.exists('simics-workspace/gold-checkpoints'):
        shutil.rmtree('simics-workspace/gold-checkpoints')
        print('deleted gold checkpoints')
    if os.path.exists('simics-workspace/injected-checkpoints'):
        shutil.rmtree('simics-workspace/injected-checkpoints')
        print('deleted injected checkpoints')
    if os.path.exists('campaign-data'):
        shutil.rmtree('campaign-data')
        print('deleted campaign data')
elif options.delete_campaign:
    if not options.campaign_number:
        options.campaign_number = get_last_campaign()
    delete_campaign(options.campaign_number)
elif options.delete_results:
    if not options.campaign_number:
        options.campaign_number = get_last_campaign()
    delete_results(options.campaign_number)
elif options.application is not None:
    new_campaign(options)
elif options.inject:
    if not options.campaign_number:
        options.campaign_number = get_last_campaign()
    campaign_data = get_campaign_data(options.campaign_number)
    starting_iteration = get_next_iteration(options.campaign_number)
    last_iteration = starting_iteration + options.num_iterations
    if campaign_data['use_simics']:
        if os.path.exists('simics-workspace/injected-checkpoints/' +
                          str(options.campaign_number)):
            shutil.rmtree('simics-workspace/injected-checkpoints/' +
                          str(options.campaign_number))
        os.makedirs('simics-workspace/injected-checkpoints/' +
                    str(options.campaign_number))
    if not os.path.exists('campaign-data/'+str(options.campaign_number) +
                          '/results'):
        os.makedirs('campaign-data/'+str(options.campaign_number)+'/results')
    iteration_counter = multiprocessing.Value('I', starting_iteration)
    if campaign_data['use_simics'] and options.num_processes > 1:
        options.debug = False
        processes = []
        for i in xrange(options.num_processes):
            process = multiprocessing.Process(target=perform_injections,
                                              args=(campaign_data,
                                                    iteration_counter,
                                                    last_iteration, options))
            processes.append(process)
            process.start()
        try:
            for process in processes:
                process.join()
        except KeyboardInterrupt:
            for process in processes:
                os.kill(process.pid, signal.SIGINT)
                process.join()
    else:
        perform_injections(campaign_data, iteration_counter, last_iteration,
                           options)
elif options.supervise:
    if not options.campaign_number:
        options.campaign_number = get_last_campaign()
    campaign_data = get_campaign_data(options.campaign_number)
    iteration = get_next_iteration(options.campaign_number)
    drseus = load_campaign(campaign_data, options)
    drseus.supervise(iteration, options.target_seconds,
                     campaign_data['output_file'],
                     campaign_data['use_aux_output'], options.capture)
elif options.view_logs:
    view_logs(args)
elif options.iteration >= 0:
    if not options.campaign_number:
        options.campaign_number = get_last_campaign()
    campaign_data = get_campaign_data(options.campaign_number)
    if not campaign_data['use_simics']:
        raise Exception('This feature is only available for Simics campaigns')
    drseus = load_campaign(campaign_data, options)
    injection_data = get_injection_data(campaign_data, options.iteration)
    checkpoint = drseus.debugger.regenerate_checkpoints(options.iteration,
                                                        drseus.cycles_between,
                                                        injection_data)
    drseus.debugger.launch_simics_gui(checkpoint)
    shutil.rmtree('simics-workspace/injected-checkpoints/' +
                  str(campaign_data['campaign_number'])+'/' +
                  str(options.iteration))
else:
    parser.error('please specify an operating mode (list options with --help)')
