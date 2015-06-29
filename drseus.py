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
from supervisor import supervisor
from simics_checkpoints import regenerate_injected_checkpoint

# TODO: re-transfer files (and ssh key) if using initramfs
# TODO: add support for multiple boards (ethernet tests)
# TODO: isolate injections on real device
# TODO: add telnet setup for bdi (firmware, configs, etc.)


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
        sql_db.commit()
        sql_db.close()
        print('flushed database')
    if os.path.exists('simics-workspace/injected-checkpoints'):
        shutil.rmtree('simics-workspace/injected-checkpoints')
        print('deleted injected checkpoints')
    sys.exit()


def setup_drseus(application, options):
    if options.architecture == 'p2020':
        application = 'ppc_fi_'+application
    elif options.architecture == 'arm':
        application = 'arm_fi_'+application
    if not os.path.exists('fiapps'):
        os.system('./setup_apps.sh')
    if not os.path.exists('fiapps/'+application):
        os.system('cd fiapps/; make '+application)
    if options.simics and not os.path.exists('simics-workspace'):
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
                print('deleted injected checkpoints')
    if options.simics:
        if options.architecture == 'p2020':
            drseus = fault_injector(dut_ip_address='10.10.0.100',
                                    architecture=options.architecture,
                                    use_simics=True, use_aux=options.aux)
        elif options.architecture == 'arm':
            drseus = fault_injector(dut_ip_address='10.10.0.100',
                                    architecture=options.architecture,
                                    use_simics=True, use_aux=options.aux)
        else:
            print('invalid architecture:', options.architecture)
            sys.exit()
    else:
        if options.architecture == 'p2020':
            drseus = fault_injector(num_checkpoints=options.num_checkpoints,
                                    use_aux=options.aux)
        elif options.architecture == 'arm':
            drseus = fault_injector(dut_ip_address='10.42.0.30',
                                    dut_serial_port='/dev/ttyACM0',
                                    architecture=options.architecture,
                                    num_checkpoints=options.num_checkpoints,
                                    use_aux=options.aux)
        else:
            print('invalid architecture:', options.architecture)
            sys.exit()
    drseus.setup_campaign('fiapps', application, options.arguments,
                          options.output_file, options.files,
                          options.iterations)
    print('\nsuccessfully setup fault injection campaign:')
    print('\tcopied target application to dut')
    print('\ttimed target application')
    print('\tgot gold output')
    if options.simics:
        print('\tcreated gold checkpoints')


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


def get_simics_campaign_data():
    if not os.path.exists('campaign-data/db.sqlite3'):
        print('could not find campaign data')
        sys.exit()
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    sql.execute('SELECT * FROM drseus_logging_simics_campaign_data')
    simics_campaign_data = sql.fetchone()
    sql_db.close()
    return simics_campaign_data


def get_next_injection_number(campaign_data):
    if not os.path.exists('campaign-data/db.sqlite3'):
        print('could not find campaign data')
        sys.exit()
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    if campaign_data['simics']:
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


def get_injection_data(campaign_data, injection_number):
    if not os.path.exists('campaign-data/db.sqlite3'):
        print('could not find campaign data')
        sys.exit()
    sql_db = sqlite3.connect('campaign-data/db.sqlite3')
    sql_db.row_factory = sqlite3.Row
    sql = sql_db.cursor()
    if campaign_data['simics']:
        sql.execute('SELECT * FROM drseus_logging_simics_injection WHERE ' +
                    'injection_number = (?)', (injection_number, ))
        injection_data = sql.fetchone()
    else:
        sql.execute('SELECT * FROM drseus_logging_hw_injection WHERE ' +
                    'injection_number = (?)', (injection_number, ))
        injection_data = sql.fetchone()
    sql_db.close()
    return injection_data


def perform_injections(campaign_data, injection_counter, options, debug):
    # TODO: check state of dut
    if len(args) > 0:
        if args[0] != campaign_data['application']:
            print('campaign created with different application:',
                  campaign_data['application'])
            sys.exit()
    if options.selected_targets is not None:
        selected_targets = options.selected_targets.split(',')
    else:
        selected_targets = None
    if options.simics and not campaign_data['simics']:
        print('previous campaign was not created with simics')
        sys.exit()
    if campaign_data['architecture'] == 'p2020':
        drseus = fault_injector(use_simics=campaign_data['simics'],
                                new=False, debug=debug)
    elif campaign_data['architecture'] == 'arm':
        drseus = fault_injector(dut_ip_address='10.42.0.30',
                                dut_serial_port='/dev/ttyACM0',
                                architecture='arm',
                                use_simics=campaign_data['simics'],
                                new=False, debug=debug)
    else:
        print('invalid architecture:', campaign_data['architecture'])
        sys.exit()
    drseus.command = campaign_data['command']
    drseus.output_file = campaign_data['output_file']
    if campaign_data['simics']:
        if not os.path.exists('simics-workspace/injected-checkpoints'):
            os.mkdir('simics-workspace/injected-checkpoints')
        simics_campaign_data = get_simics_campaign_data()
        drseus.num_checkpoints = simics_campaign_data['num_checkpoints']
        drseus.cycles_between = simics_campaign_data['cycles_between']
        drseus.board = simics_campaign_data['board']
    else:
        drseus.exec_time = campaign_data['exec_time']
    # try:
    for i in xrange(options.num_injections):
        with injection_counter.get_lock():
            injection_number = injection_counter.value
            injection_counter.value += 1
        drseus.inject_fault(injection_number, selected_targets)
        drseus.monitor_execution(injection_number)
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
    os.system('google-chrome http://localhost:8000')
    os.killpg(os.getpgid(server.pid), signal.SIGKILL)
    sys.exit()

parser = optparse.OptionParser('drseus.py {application} {options}')

# general options
parser.add_option('-d', '--delete', action='store_true', dest='clean',
                  default=False,
                  help='delete results and/or injected checkpoints')
parser.add_option('-i', '--inject', action='store_true', dest='inject',
                  default=False,
                  help='perform fault injections on an existing campaign')

# new campaign options
parser.add_option('-m', '--timing', action='store', type='int',
                  dest='iterations', default=5,
                  help='number of timing iterations of application ' +
                       'to run [default=5]')
parser.add_option('-o', '--output', action='store', type='str',
                  dest='output_file', default='result.dat',
                  help='target application output file [default=result.dat]')
parser.add_option('-a', '--arguments', action='store', type='str',
                  dest='arguments', default='',
                  help='arguments for application')
parser.add_option('-f', '--files', action='store', type='str', dest='files',
                  default='',
                  help='comma-seperated list of files to copy to device')
parser.add_option('-r', '--architecture', action='store', type='str',
                  dest='architecture', default='p2020',
                  help='target architecture [default=p2020]')
parser.add_option('-s', '--simics', action='store_true', dest='simics',
                  default=False, help='use simics simulator')
parser.add_option('-x', '--auxiliary', action='store_true', dest='aux',
                  default=False, help='use second device during testing')
parser.add_option('-y', '--auxiliary_application', action='store', type='str',
                  dest='aux_app', default=None,
                  help='target application for auxiliary device ' +
                  '[default={application}]')
parser.add_option('-z', '--auxiliary_arguments', action='store', type='str',
                  dest='aux_args', default=None,
                  help='arguments for auxiliary application')

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
parser.add_option('-q', '--all', action='store_true', dest='compare_all',
                  default=False,
                  help='compare all checkpoints, only last by default')
parser.add_option('-g', '--regenerate_checkpoint', action='store', type='int',
                  dest='regenerate_checkpoint', default=-1,
                  help='regenerate an injected checkpoint and launch in Simics')

# log options
parser.add_option('-l', '--view_logs', action='store_true',
                  dest='view_logs', default=False,
                  help='open logs in browser')

options, args = parser.parse_args()

# clean campaign (results and injected checkpoints)
if options.clean:
    delete_results()

elif options.view_logs:
    view_logs()

# perform fault injections
elif options.inject:
    campaign_data = get_campaign_data()
    starting_injection = get_next_injection_number(campaign_data)
    injection_counter = multiprocessing.Value('I', starting_injection)
    if campaign_data['simics'] and options.num_processes > 1:
        debug = False
        processes = []
        for i in xrange(options.num_processes):
            process = multiprocessing.Process(target=perform_injections,
                                              args=(campaign_data,
                                                    injection_counter,
                                                    options, debug))
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

elif options.regenerate_checkpoint >= 0:
    campaign_data = get_campaign_data()
    if not campaign_data['simics']:
        print('This feature is only available for Simics campaigns')
        sys.exit()
    simics_campaign_data = get_simics_campaign_data()
    injection_data = get_injection_data(campaign_data,
                                        options.regenerate_checkpoint)
    checkpoint = regenerate_injected_checkpoint(simics_campaign_data['board'],
                                                injection_data)
    # launch checkpoint
    dut_board = 'DUT_'+simics_campaign_data['board']
    if campaign_data['architecture'] == 'p2020':
        serial_port = 'serial[0]'
    else:
        serial_port = 'serial0'
    simics_commands = ('read-configuration '+checkpoint+';' +
                       'new-text-console-comp text_console0;' +
                       'disconnect '+dut_board+'.console0.serial ' +
                       dut_board+'.'+serial_port+';' +
                       'connect text_console0.serial ' +
                       dut_board+'.'+serial_port+';' +
                       'connect-real-network-port-in ssh ' +
                       'ethernet_switch0 target-ip=10.10.0.100')
    os.system('cd simics-workspace; ./simics-gui -e \"'+simics_commands+'\"')
    shutil.rmtree('simics-workspace/'+checkpoint)
    if not os.listdir('simics-workspace/temp'):
        os.rmdir('simics-workspace/temp')


# setup supervisor
elif options.aux:
    if len(args) < 1:
        parser.error('please specify an application')
    application = 'ppc_fi_'+args[0]
    if options.aux_app is None:
        aux_application = 'ppc_fi_'+args[0]
    else:
        aux_application = 'ppc_fi_'+options.aux_app
    if not os.path.exists('fiapps/'+application):
        os.system('cd fiapps/; make '+application)
    drseus = supervisor(architecture=options.architecture,
                        use_simics=options.simics)
    drseus.setup_campaign('ppc_fi_'+args[0], options.arguments,
                          aux_application, options.arguments if
                          options.aux_args is None else options.aux_args)
    drseus.monitor_execution()
    drseus.exit()
# ./drseus.py socket_echo -a "65222" -s \
#             -x -y socket_send_recv -z "10.10.0.100 65222 -i 10" -s

# setup fault injection campaign
else:
    if len(args) < 1:
        parser.error('please specify an application')
    setup_drseus(args[0], options)
