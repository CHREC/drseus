#!/usr/bin/python

from __future__ import print_function
import sys
import optparse
import shutil
import os
import subprocess
import signal
import sqlite3
import multiprocessing

from fault_injector import fault_injector

# TODO: add support for checking console for data error
#       append to dut.error_messages
# TODO: add telnet setup for bdi (firmware, configs, etc.)
# TODO: add multirpocessing queue to aux_process to get output


def delete_results():
    if os.path.exists('campaign-data/results'):
        shutil.rmtree('campaign-data/results')
        print('deleted results')
    if os.path.exists('campaign-data/db.sqlite3'):
        sql_db = sqlite3.connect('campaign-data/db.sqlite3')
        sql = sql_db.cursor()
        sql.execute('DELETE FROM drseus_logging_hw_injection')
        sql.execute('DELETE FROM drseus_logging_hw_result')
        sql.execute('DELETE FROM drseus_logging_simics_injection')
        sql.execute('DELETE FROM drseus_logging_simics_register_diff')
        sql.execute('DELETE FROM drseus_logging_simics_result')
        sql.execute('DELETE FROM drseus_logging_supervisor_result')
        sql_db.commit()
        sql_db.close()
        print('flushed database')
    if os.path.exists('simics-workspace/injected-checkpoints'):
        shutil.rmtree('simics-workspace/injected-checkpoints')
        print('deleted injected checkpoints')
    sys.exit()


def setup_campaign(application, options):
    if options.architecture == 'p2020':
        dut_ip_address = '10.42.0.21'
        dut_serial_port = '/dev/ttyUSB1'
        application = 'ppc_fi_'+application
        if options.aux_app is None:
            aux_application = 'ppc_fi_'+application
        else:
            aux_application = 'ppc_fi_'+options.aux_app
    elif options.architecture == 'arm':
        dut_ip_address = '10.42.0.30'
        dut_serial_port = '/dev/ttyACM0'
        application = 'arm_fi_'+application
        if options.aux_app is None:
            aux_application = 'arm_fi_'+application
        else:
            aux_application = 'arm_fi_'+options.aux_app
    else:
        print('invalid architecture:', options.architecture)
        sys.exit()
    if options.file_location == 'fiapps':
        if not os.path.exists('fiapps'):
            os.system('./setup_apps.sh')
        if not os.path.exists('fiapps/'+application):
            os.system('cd fiapps/; make '+application)
    else:
        if not os.path.exits(options.file_location):
            print('cannot find', options.file_location)
            sys.exit()
    if options.use_simics and not os.path.exists('simics-workspace'):
        os.system('./setup_simics.sh')
    if os.path.exists('campaign-data') and os.listdir('campaign-data'):
        print('previous campaign data exists, continuing will delete it')
        if raw_input('continue? [Y/n]: ') in ['n', 'N', 'no', 'No', 'NO']:
            sys.exit()
        else:
            shutil.rmtree('campaign-data')
            print('deleted campaign data')
            if os.path.exists('campaign-data/db.sqlite3'):
                os.remove('campaign-data/db.sqlite3')
                print('deleted database')
            if os.path.exists('simics-workspace/gold-checkpoints'):
                shutil.rmtree('simics-workspace/gold-checkpoints')
                print('deleted gold checkpoints')
            if os.path.exists('simics-workspace/injected-checkpoints'):
                shutil.rmtree('simics-workspace/injected-checkpoints')
    drseus = fault_injector(dut_ip_address, '10.42.0.20', dut_serial_port,
                            '/dev/ttyUSB0', '10.42.0.50', options.architecture,
                            options.use_aux, True, options.debug,
                            options.use_simics)
    drseus.setup_campaign(options.file_location, options.architecture,
                          application, options.arguments, options.output_file,
                          options.files, options.aux_files, options.iterations,
                          aux_application, options.aux_args,
                          options.use_aux_output, options.num_checkpoints)
    print('\nsuccessfully setup campaign')


def get_campaign_data():
    if not os.path.exists('campaign-data/db.sqlite3'):
        print('could not find campaign data')
        sys.exit()
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    sql.execute('select * from drseus_logging_campaign_data')
    campaign_data = sql.fetchone()
    sql_db.close()
    return campaign_data


def get_next_injection_number(campaign_data):
    if not os.path.exists('campaign-data/db.sqlite3'):
        print('could not find campaign data')
        sys.exit()
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    if campaign_data['use_simics']:
        sql.execute('SELECT * FROM drseus_logging_simics_injection ORDER BY ' +
                    'injection_number DESC LIMIT 1')
        injection_data = sql.fetchone()
    else:
        sql.execute('SELECT * FROM drseus_logging_hw_injection ORDER BY ' +
                    'injection_number DESC LIMIT 1')
        injection_data = sql.fetchone()
    if injection_data is None:
        injection_number = 0
    else:
        injection_number = injection_data['injection_number'] + 1
    sql_db.close()
    return injection_number


def get_next_iteration():
    if not os.path.exists('campaign-data/db.sqlite3'):
        print('could not find campaign data')
        sys.exit()
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    sql.execute('SELECT * FROM drseus_logging_supervisor_result ORDER BY ' +
                'iteration DESC LIMIT 1')
    supervisor_data = sql.fetchone()
    if supervisor_data is None:
        iteration = 0
    else:
        iteration = supervisor_data['iteration'] + 1
    sql_db.close()
    return iteration


def get_injection_data(campaign_data, injection_number):
    if not os.path.exists('campaign-data/db.sqlite3'):
        print('could not find campaign data')
        sys.exit()
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    if campaign_data['use_simics']:
        sql.execute('SELECT * FROM drseus_logging_simics_injection WHERE ' +
                    'injection_number = (?)', (injection_number, ))
        injection_data = sql.fetchone()
    else:
        sql.execute('SELECT * FROM drseus_logging_hw_injection WHERE ' +
                    'injection_number = (?)', (injection_number, ))
        injection_data = sql.fetchone()
    sql_db.close()
    return injection_data


def load_campaign(campaign_data, options):
    if options.architecture == 'p2020':
        dut_ip_address = '10.42.0.21'
        dut_serial_port = '/dev/ttyUSB1'
    elif options.architecture == 'arm':
        dut_ip_address = '10.42.0.30'
        dut_serial_port = '/dev/ttyACM0'
    else:
        print('invalid architecture:', options.architecture)
        sys.exit()
    drseus = fault_injector(dut_ip_address, '10.42.0.20', dut_serial_port,
                            '/dev/ttyUSB0', '10.42.0.50',
                            campaign_data['architecture'],
                            campaign_data['use_aux'], False, options.debug,
                            campaign_data['use_simics'])
    drseus.command = campaign_data['command']
    drseus.aux_command = campaign_data['aux_command']
    drseus.num_checkpoints = campaign_data['num_checkpoints']
    drseus.cycles_between = campaign_data['cycles_between']
    drseus.exec_time = campaign_data['exec_time']
    return drseus


def perform_injections(campaign_data, injection_counter, options):
    drseus = load_campaign(campaign_data, options)
    if options.selected_targets is not None:
        selected_targets = options.selected_targets.split(',')
    else:
        selected_targets = None
    # try:
    for i in xrange(options.num_injections):
        with injection_counter.get_lock():
            injection_number = injection_counter.value
            injection_counter.value += 1
        drseus.inject_fault(injection_number, selected_targets)
        drseus.monitor_execution(injection_number, campaign_data['output_file'],
                                 campaign_data['use_aux_output'],
                                 options.compare_all)
    drseus.exit()
    # except KeyboardInterrupt:
    #     shutil.rmtree('campaign-data/results/'+str(injection_number))
    #     if drseus.simics:
    #         try:
    #             shutil.rmtree('simics-workspace/' +
    #                           drseus.debugger.injected_checkpoint)
    #         except:
    #             pass
    #     else:
    #         drseus.debugger.continue_dut()
    #     drseus.exit()


def view_logs():
    server = subprocess.Popen([os.getcwd()+'/django-logging/manage.py',
                               'runserver'],
                              cwd=os.getcwd()+'/django-logging/')
    try:
        os.system('google-chrome http://localhost:8000')
    except:
        os.system('firefox http://localhost:8000')
    try:
        os.killpg(os.getpgid(server.pid), signal.SIGINT)
    except KeyboardInterrupt:
        sys.exit()

parser = optparse.OptionParser('drseus.py {application} {options}')

# general options
parser.add_option('-D', '--debug', action='store_false', dest='debug',
                  default=True,
                  help='display device output')
parser.add_option('-d', '--delete', action='store_true', dest='clean',
                  default=False,
                  help='delete results and/or injected checkpoints')
parser.add_option('-i', '--inject', action='store_true', dest='inject',
                  default=False,
                  help='perform fault injections on an existing campaign')
parser.add_option('-S', '--supervise', action='store_true', dest='supervise',
                  default=False,
                  help='do not inject faults, only supervise devices')
parser.add_option('-l', '--view_logs', action='store_true',
                  dest='view_logs', default=False,
                  help='open logs in browser')

# new campaign options
parser.add_option('-I', '--iterations', action='store', type='int',
                  dest='iterations', default=5,
                  help='number of timing iterations of application ' +
                       'to run [default=5]')
parser.add_option('-o', '--output', action='store', type='str',
                  dest='output_file', default='result.dat',
                  help='target application output file [default=result.dat]')
parser.add_option('-a', '--arguments', action='store', type='str',
                  dest='arguments', default='',
                  help='arguments for application')
parser.add_option('-L', '--location', action='store', type='str',
                  dest='file_location', default='fiapps',
                  help='location to look for files [default=fiapps]')
parser.add_option('-f', '--files', action='store', type='str', dest='files',
                  default='',
                  help='comma-separated list of files to copy to device')
parser.add_option('-F', '--aux_files', action='store', type='str',
                  dest='aux_files', default='',
                  help='comma-separated list of files to copy to aux device')
parser.add_option('-A', '--architecture', action='store', type='str',
                  dest='architecture', default='p2020',
                  help='target architecture [default=p2020]')
parser.add_option('-s', '--simics', action='store_true', dest='use_simics',
                  default=False, help='use simics simulator')
parser.add_option('-x', '--auxiliary', action='store_true', dest='use_aux',
                  default=False, help='use second device during testing')
parser.add_option('-y', '--auxiliary_application', action='store', type='str',
                  dest='aux_app', default='',
                  help='target application for auxiliary device ' +
                  '[default={application}]')
parser.add_option('-z', '--auxiliary_arguments', action='store', type='str',
                  dest='aux_args', default='',
                  help='arguments for auxiliary application')
parser.add_option('-O', '--aux_output', action='store_true',
                  dest='use_aux_output', default=False,
                  help='check output data from aux instead of dut')

# injection options
parser.add_option('-n', '--num', action='store', type='int',
                  dest='num_injections', default=10,
                  help='number of injections to perform [default=10]')
parser.add_option('-t', '--targets', action='store', type='str',
                  dest='selected_targets', default=None,
                  help='comma-seperated list of targets for injection')

# simics options
parser.add_option('-c', '--checkpoints', action='store', type='int',
                  dest='num_checkpoints', default=50,
                  help='number of gold checkpoints to create [default=50]')
parser.add_option('-p', '--processes', action='store', type='int',
                  dest='num_processes', default=1,
                  help='number of simics injections to perform in parallel')
parser.add_option('-C', '--all', action='store_true', dest='compare_all',
                  default=False,
                  help='compare all checkpoints, only last by default')
parser.add_option('-r', '--regenerate_checkpoint', action='store', type='int',
                  dest='regenerate_checkpoint', default=-1,
                  help='regenerate an injected checkpoint and launch in Simics')

options, args = parser.parse_args()

if options.clean:
    delete_results()

elif options.view_logs:
    view_logs()

elif options.inject:
    campaign_data = get_campaign_data()
    if campaign_data['use_simics']:
        if not os.path.exists('simics-workspace/injected-checkpoints'):
            os.mkdir('simics-workspace/injected-checkpoints')
    starting_injection = get_next_injection_number(campaign_data)
    injection_counter = multiprocessing.Value('I', starting_injection)
    if campaign_data['use_simics'] and options.num_processes > 1:
        options.debug = False
        processes = []
        for i in xrange(options.num_processes):
            process = multiprocessing.Process(target=perform_injections,
                                              args=(campaign_data,
                                                    injection_counter,
                                                    options))
            processes.append(process)
            process.start()
        # try:
        for process in processes:
            process.join()
        # except KeyboardInterrupt:
        #     for process in processes:
        #         process.terminate()
        #         process.join()
    else:
        perform_injections(campaign_data, injection_counter, options)

elif options.supervise:
    campaign_data = get_campaign_data()
    iteration = get_next_iteration()
    drseus = load_campaign(campaign_data, options)
    drseus.supervise(iteration, campaign_data['output_file'],
                     campaign_data['use_aux_output'])
    drseus.exit()

elif options.regenerate_checkpoint >= 0:
    campaign_data = get_campaign_data()
    if not campaign_data['use_simics']:
        print('This feature is only available for Simics campaigns')
        sys.exit()
    drseus = load_campaign(campaign_data, options)
    injection_data = get_injection_data(campaign_data,
                                        options.regenerate_checkpoint)
    checkpoint = drseus.debugger.regenerate_injected_checkpoint(injection_data)
    drseus.debugger.launch_simics_gui(checkpoint)
    shutil.rmtree('simics-workspace/'+checkpoint)
    if not os.listdir('simics-workspace/temp'):
        os.rmdir('simics-workspace/temp')

# setup fault injection campaign
else:
    if len(args) < 1:
        parser.error('please specify an application')
    setup_campaign(args[0], options)
