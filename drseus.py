#!/usr/bin/python

from __future__ import print_function
import multiprocessing
import optparse
import os
import shutil
from signal import SIGINT
from subprocess import Popen
import sqlite3

from fault_injector import fault_injector

# TODO: add telnet setup for bdi (firmware, configs, etc.)
# TODO: implement persistent fault detection
# TODO: add option for number of times to rerun app for latent fault case
# TODO: reimplement checkpoint regeneration with multiple injections
# TODO: fix saving iteration as result_id (won't work with multiple campaigns)


def list_campaigns():
    if not os.path.exists('campaign-data/db.sqlite3'):
        raise Exception('could not find campaign data')
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    sql.execute('SELECT campaign_number, application, architecture, use_simics '
                'FROM drseus_logging_campaign')
    campaign_list = sql.fetchall()
    sql_db.close()
    print('DrSEUS Campaigns:')
    print('Number\t\tApplication\t\tArchitecture\tSimics')
    for campaign in campaign_list:
        campaign = list(campaign)
        campaign[3] = bool(campaign[3])
        print('\t\t'.join([str(item) for item in campaign]))


def get_last_campaign():
    if not os.path.exists('campaign-data') or \
            not os.path.exists('campaign-data/db.sqlite3'):
        return 0
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
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
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
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
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
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
    # delete incomple injections
    sql.execute('DELETE FROM drseus_logging_injection WHERE result_id IN '
                '(SELECT id FROM drseus_logging_result WHERE outcome=?)',
                ('In progress',))
    sql.execute('DELETE FROM drseus_logging_result WHERE outcome=?',
                ('In progress',))
    sql_db.commit()
    sql_db.close()
    return iteration + 1


def delete_results(campaign_number):
    if os.path.exists('campaign-data/'+str(campaign_number)+'/results'):
        shutil.rmtree('campaign-data/'+str(campaign_number)+'/results')
        print('deleted results')
    if os.path.exists('campaign-data/db.sqlite3'):
        sql_db = sqlite3.connect('campaign-data/db.sqlite3')
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
        sql_db = sqlite3.connect('campaign-data/db.sqlite3')
        sql = sql_db.cursor()
        sql.execute('DELETE FROM drseus_logging_campaign WHERE campaign_id=?',
                    (campaign_number,))
        sql_db.commit()
        sql_db.close()
        print('deleted campaign from database')
    if os.path.exists('simics-workspace/gold-checkpoints/' +
                      str(campaign_number)):
        shutil.rmtree('simics-workspace/gold-checkpoints/' +
                      str(campaign_number))
        print('deleted gold checkpoints')


def new_campaign(application, options):
    campaign_number = get_last_campaign() + 1
    if options.architecture == 'p2020':
        dut_ip_address = '10.42.0.21'
        dut_serial_port = '/dev/ttyUSB1'
        application = 'ppc_fi_'+application
        if options.aux_app:
            aux_application = 'ppc_fi_'+options.aux_app
        else:
            aux_application = application
    elif options.architecture == 'a9':
        dut_ip_address = '10.42.0.30'
        dut_serial_port = '/dev/ttyACM0'
        application = 'arm_fi_'+application
        if options.aux_app:
            aux_application = 'arm_fi_'+options.aux_app
        else:
            aux_application = application
    else:
        raise Exception('invalid architecture: '+options.architecture)
    if options.directory == 'fiapps':
        if not os.path.exists('fiapps'):
            os.system('./setup_apps.sh')
        if not os.path.exists('fiapps/'+application):
            os.system('cd fiapps/; make '+application)
    else:
        if not os.path.exits(options.directory):
            raise Exception('cannot find directory '+options.directory)
    if options.use_simics and not os.path.exists('simics-workspace'):
        os.system('./setup_simics.sh')
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
    drseus = fault_injector(campaign_number, dut_ip_address, '10.42.0.20',
                            dut_serial_port, '/dev/ttyUSB0', '10.42.0.50',
                            options.architecture, options.use_aux, True,
                            options.debug, options.use_simics, options.seconds)
    drseus.setup_campaign(options.directory, options.architecture, application,
                          options.arguments, options.file, options.files,
                          options.aux_files, options.iterations,
                          aux_application, options.aux_args,
                          options.use_aux_output, options.num_checkpoints)
    print('\nsuccessfully setup campaign')


# def get_injection_data(campaign_data, injection_number):
#     if not os.path.exists('campaign-data/db.sqlite3'):
#         raise Exception('could not find campaign data')
#     sql_db = sqlite3.connect('campaign-data/db.sqlite3')
#     sql_db.row_factory = sqlite3.Row
#     sql = sql_db.cursor()
#     sql.execute('SELECT * FROM drseus_logging_injection WHERE ' +
#                 'injection_number = (?)', (injection_number, ))
#     injection_data = sql.fetchone()
#     sql_db.close()
#     return injection_data


def load_campaign(campaign_data, options):
    if campaign_data['architecture'] == 'p2020':
        dut_ip_address = '10.42.0.21'
        dut_serial_port = '/dev/ttyUSB1'
    elif campaign_data['architecture'] == 'a9':
        dut_ip_address = '10.42.0.30'
        dut_serial_port = '/dev/ttyACM0'
    drseus = fault_injector(campaign_data['campaign_number'], dut_ip_address,
                            '10.42.0.20', dut_serial_port, '/dev/ttyUSB0',
                            '10.42.0.50', campaign_data['architecture'],
                            campaign_data['use_aux'], False, options.debug,
                            campaign_data['use_simics'], options.seconds)
    drseus.command = campaign_data['command']
    drseus.aux_command = campaign_data['aux_command']
    drseus.num_checkpoints = campaign_data['num_checkpoints']
    drseus.cycles_between = campaign_data['cycles_between']
    drseus.exec_time = campaign_data['exec_time']
    return drseus


def perform_injections(campaign_data, iteration_counter, options):
    drseus = load_campaign(campaign_data, options)
    if options.selected_targets is not None:
        selected_targets = options.selected_targets.split(',')
    else:
        selected_targets = None
    # try:
    drseus.inject_and_monitor(iteration_counter, options.num_iterations,
                              options.num_injections, selected_targets,
                              campaign_data['output_file'],
                              campaign_data['use_aux_output'],
                              options.compare_all)
    # except KeyboardInterrupt:
    #     shutil.rmtree('campaign-data/results/'+str(iteration))
    #     if drseus.simics:
    #         try:
    #             shutil.rmtree('simics-workspace/' +
    #                           drseus.debugger.injected_checkpoint)
    #         except:
    #             pass
    #     else:
    #         drseus.debugger.continue_dut()
    #     drseus.close()


def view_logs():
    server = Popen([os.getcwd()+'/django-logging/manage.py', 'runserver'],
                   cwd=os.getcwd()+'/django-logging/')
    if os.system('which google-chrome'):
        os.system('firefox http://localhost:8000')
    else:
        os.system('google-chrome http://localhost:8000')
    try:
        os.killpg(os.getpgid(server.pid), SIGINT)
    except KeyboardInterrupt:
        pass

parser = optparse.OptionParser('drseus.py {application} {options}')

parser.add_option('-N', '--campaign', action='store', type='int', dest='number',
                  default=0, help='campaign number to use, defaults to '
                                  'last campaign created')
parser.add_option('-g', '--debug', action='store_false', dest='debug',
                  default=True,
                  help='display device output')
parser.add_option('-T', '--timeout', action='store', type='int',
                  dest='seconds', default=300,
                  help='device read timeout in seconds [default=300]')

mode_group = optparse.OptionGroup(parser, 'DrSEUS Modes', 'Not specifying one '
                                  'of these will create a new campaign')
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
mode_group.add_option('-i', '--inject', action='store_true', dest='inject',
                      default=False,
                      help='perform fault injections on an existing campaign')
mode_group.add_option('-S', '--supervise', action='store_true',
                      dest='supervise', default=False,
                      help='do not inject faults, only supervise devices')

mode_group.add_option('-l', '--log', action='store_true',
                      dest='view_logs', default=False,
                      help='open logs in browser')
parser.add_option_group(mode_group)

# simics_mode_group = optparse.OptionGroup(parser, 'DrSEUS Modes (Simics only)',
#                                          'These modes are only available for '
#                                          'Simics campaigns')
# simics_mode_group.add_option('-r', '--regenerate', action='store', type='int',
#                              dest='injection', default=-1,
#                              help='regenerate an injected checkpoint and '
#                              'launch in Simics')
# parser.add_option_group(simics_mode_group)

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
new_group.add_option('-L', '--location', action='store', type='str',
                     dest='directory', default='fiapps',
                     help='location to look for files [default=fiapps]')
new_group.add_option('-f', '--files', action='store', type='str', dest='files',
                     default='',
                     help='comma-separated list of files to copy to device')
new_group.add_option('-F', '--aux_files', action='store', type='str',
                     dest='aux_files', default='',
                     help='comma-separated list of files to copy to aux device')
new_group.add_option('-A', '--arch', action='store', type='str',
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
                     help='check output data from aux instead of dut')
parser.add_option_group(new_group)

new_simics_group = optparse.OptionGroup(parser, 'New Campaign Options '
                                        '(Simics only)', 'Use these for new '
                                        'Simics campaigns')
new_simics_group.add_option('-c', '--checkpoints', action='store', type='int',
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
                                       'in parallel (each instance performs '
                                        'NUM_ITERATIONS)')
simics_injection_group.add_option('-M', '--all', action='store_true',
                                  dest='compare_all', default=False,
                                  help='monitorall all checkpoints, only last '
                                       'by default')
parser.add_option_group(simics_injection_group)

supervise_group = optparse.OptionGroup(parser, 'Supervisor Options', 'Use these'
                                       ' options for supervising '
                                       '(-S or --supervise)')
supervise_group.add_option('-R', '--runtime', action='store', type='int',
                           dest='target_seconds', default=30,
                           help='Desired time in seconds to run (calculates '
                                'number of iterations to run) [default=30]')
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
    if not options.number:
        options.number = get_last_campaign()
    delete_campaign(options.number)
elif options.delete_results:
    if not options.number:
        options.number = get_last_campaign()
    delete_results(options.number)
elif options.view_logs:
    view_logs()
elif options.inject:
    if not options.number:
        options.number = get_last_campaign()
    campaign_data = get_campaign_data(options.number)
    if campaign_data['use_simics']:
        if os.path.exists('simics-workspace/injected-checkpoints/' +
                          str(options.number)):
            shutil.rmtree('simics-workspace/injected-checkpoints/' +
                          str(options.number))
        os.makedirs('simics-workspace/injected-checkpoints/' +
                    str(options.number))
    if not os.path.exists('campaign-data/'+str(options.number)+'/results'):
        os.makedirs('campaign-data/'+str(options.number)+'/results')
    starting_iteration = get_next_iteration(options.number)
    iteration_counter = multiprocessing.Value('I', starting_iteration)
    if campaign_data['use_simics'] and options.num_processes > 1:
        options.debug = False
        processes = []
        for i in xrange(options.num_processes):
            process = multiprocessing.Process(target=perform_injections,
                                              args=(campaign_data,
                                                    iteration_counter,
                                                    options))
            processes.append(process)
            process.start()
        try:
            for process in processes:
                process.join()
        except KeyboardInterrupt:
            for process in processes:
                process.terminate()
                process.join()
    else:
        perform_injections(campaign_data, iteration_counter, options)
elif options.supervise:
    if not options.number:
        options.number = get_last_campaign()
    campaign_data = get_campaign_data(options.number)
    iteration = get_next_iteration(options.number)
    drseus = load_campaign(campaign_data, options)
    drseus.supervise(iteration, options.target_seconds,
                     campaign_data['output_file'],
                     campaign_data['use_aux_output'])
# elif options.injection >= 0:
#     campaign_data = get_campaign_data()
#     if not campaign_data['use_simics']:
#         print('This feature is only available for Simics campaigns')
#         return -1
#     drseus = load_campaign(campaign_data, options)
#     injection_data = get_injection_data(campaign_data,
#                                         options.injection)
#     checkpoint = drseus.debugger.regenerate_injected_checkpoint(
#          injection_data)
#     drseus.debugger.launch_simics_gui(checkpoint)
#     shutil.rmtree('simics-workspace/'+checkpoint)
#     if not os.listdir('simics-workspace/temp'):
#         os.rmdir('simics-workspace/temp')
else:
    if len(args) < 1:
        parser.error('please specify a target application')
    new_campaign(args[0], options)
