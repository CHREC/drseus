#!/usr/bin/python

from __future__ import print_function
import sys
import optparse
import shutil
import os
import pickle
import subprocess
import signal

from fault_injector import fault_injector
from supervisor import supervisor

# TODO: re-transfer files (and ssh key) if using initramfs
# TODO: add support for multiple boards (ethernet tests) and
#       concurrent simics injections
# TODO: isolate injections on real device
# TODO: add telnet setup for bdi (firmware, configs, etc.)

parser = optparse.OptionParser('drseus.py {application} {options}')

# general options
parser.add_option('-d', '--delete', action='store_true', dest='clean',
                  default=False,
                  help='delete results and/or injected checkpoints')
parser.add_option('-i', '--inject', action='store_true', dest='inject',
                  default=False,
                  help='perform fault injections on an existing campaign')

# new campaign options
parser.add_option('-t', '--timing', action='store', type='int',
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
                  help='additional files to copy to dut (comma-seperated list)')
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

# simics options
parser.add_option('-c', '--checkpoints', action='store', type='int',
                  dest='num_checkpoints', default=50,
                  help='number of gold checkpoints to create [default=50]')

# log options
parser.add_option('-l', '--view_logs', action='store_true',
                  dest='view_logs', default=False,
                  help='open logs in browser')

options, args = parser.parse_args()

# clean campaign (results and injected checkpoints)
if options.clean:
    if os.path.exists('campaign-data/results'):
        shutil.rmtree('campaign-data/results')
        print('deleted results')
    if os.path.exists('django-logging/db.sqlite3'):
        os.remove('django-logging/db.sqlite3')
        print('deleted database')
    if os.path.exists('simics-workspace/injected-checkpoints'):
        shutil.rmtree('simics-workspace/injected-checkpoints')
        print('deleted injected checkpoints')

if options.view_logs:
    server = subprocess.Popen([os.getcwd()+'/django-logging/manage.py',
                               'runserver'],
                              cwd=os.getcwd()+'/django-logging/')
    os.system('google-chrome http://localhost:8000/register-chart/')
    os.killpg(os.getpgid(server.pid), signal.SIGKILL)
    sys.exit()

# setup fault injection campaign
if not options.inject and not options.aux:
    if len(args) < 1:
        if options.clean:
            sys.exit()
        else:
            parser.error('please specify an application')
    if not os.path.exists('fiapps'):
        os.system('./setup_apps.sh')
    if not os.path.exists('fiapps/'+args[0]):
        os.system('cd fiapps/; make '+args[0])
    if options.simics and not os.path.exists('simics-workspace'):
        os.system('./setup_simics.sh')
    if os.path.exists('campaign-data'):
        print('warning: previous campaign data exists, ',
              'continuing will delete it')
        if raw_input('continue? [Y/n]: ') in ['n', 'N', 'no', 'No', 'NO']:
            sys.exit()
        else:
            shutil.rmtree('campaign-data')
            print('deleted campaign data')
            if os.path.exists('django-logging/db.sqlite3'):
                os.remove('django-logging/db.sqlite3')
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
                                    use_simics=True)
        elif options.architecture == 'arm':
            drseus = fault_injector(dut_ip_address='11.11.11.12',
                                    architecture=options.architecture,
                                    use_simics=True)
        else:
            print('invalid architecture:', options.architecture)
            sys.exit()
    else:
        if options.architecture == 'p2020':
            drseus = fault_injector()
        elif options.architecture == 'arm':
            drseus = fault_injector(dut_ip_address='10.42.0.30',
                                    dut_serial_port='/dev/ttyACM0',
                                    architecture=options.architecture)
        else:
            print('invalid architecture:', options.architecture)
            sys.exit()
    drseus.setup_campaign('fiapps', args[0], options.arguments,
                          options.output_file, options.files,
                          options.iterations, options.num_checkpoints)
    print('\nsuccessfully setup fault injection campaign:')
    print('\tcopied target application to dut')
    print('\ttimed target application')
    print('\tgot gold output')
    if options.simics:
        print('\tcreated gold checkpoints')

# perform fault injections
elif options.inject:
    # TODO: check state of dut
    if not os.path.exists('campaign-data'):
        print('could not find previously created campaign')
        sys.exit()
    with open('campaign-data/campaign.pickle', 'r') as campaign_pickle:
        campaign_data = pickle.load(campaign_pickle)
    if len(args) > 0:
        if args[0] != campaign_data['application']:
            print('campaign created with different application:',
                  campaign_data['application'])
            sys.exit()
    if options.simics and not campaign_data['use_simics']:
        print('previous campaign was not created with simics')
        sys.exit()
    if campaign_data['architecture'] == 'p2020':
        drseus = fault_injector(use_simics=campaign_data['use_simics'],
                                new=False)
    elif campaign_data['architecture'] == 'arm':
        drseus = fault_injector(dut_ip_address='10.42.0.30',
                                dut_serial_port='/dev/ttyACM0',
                                architecture='arm',
                                use_simics=campaign_data['use_simics'],
                                new=False)
    # TODO: should not need this
    else:
        print('invalid architecture:', campaign_data['architecture'])
        sys.exit()
    drseus.command = campaign_data['command']
    drseus.output_file = campaign_data['output_file']
    if campaign_data['use_simics']:
        drseus.cycles_between = campaign_data['cycles_between']
    else:
        drseus.exec_time = campaign_data['exec_time']
    if os.path.exists('campaign-data/results'):
        start = len(os.listdir('campaign-data/results'))
    else:
        start = 0
    try:
        for injection_number in xrange(start, start + options.num_injections):
            drseus.inject_fault(injection_number)
            drseus.monitor_execution(injection_number)
            drseus.log_injection(injection_number)
        drseus.exit()
    except KeyboardInterrupt:
        if not drseus.simics:
            drseus.debugger.continue_dut()
        drseus.exit()
        # TODO: delete results folder for injection in progress
        if drseus.simics:
            shutil.rmtree('simics-workspace/' +
                          drseus.debugger.injected_checkpoint)

# setup supervisor
elif options.aux:
    if len(args) < 1:
        if options.clean:
            sys.exit()
        else:
            parser.error('please specify an application')
    drseus = supervisor()
    drseus.setup_campaign('fiapps', args[0], options.arguments,
                          args[0] if options.aux_app is None else
                          options.aux_app,
                          options.arguments if options.aux_args is None else
                          options.aux_args)
    drseus.monitor_execution()
    drseus.exit()
# ./drseus.py ppc_fi_socket_echo -a "65222" -x -y ppc_fi_socket_send_recv -z "10.42.0.21 65222 -i 10"
