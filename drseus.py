#!/usr/bin/python

from __future__ import print_function
import multiprocessing
import optparse
import os
import shutil
import signal
import sys

from supervisor import supervisor
import utilities

# TODO: replace iteration numbers with result_ids
# TODO: check for extra campaign data files (higher campaign number)
# TODO: add mode to redo injection iteration
# TODO: add fallback to power cycle when resetting dut
# TODO: add support for injection of multi-bit upsets
# TODO: add option for number of times to rerun app for latent fault case
# TODO: change Exception in simics_checkpoints.py to DrSEUsError
# TODO: update simics_checkpoints to use simics_config

parser = optparse.OptionParser('drseus.py {mode} {options}')

parser.add_option('-N', '--campaign', action='store', type='int',
                  dest='campaign_number', default=0,
                  help='campaign number to use, defaults to last campaign '
                       'created')
parser.add_option('-g', '--debug', action='store_true', dest='debug',
                  default=False,
                  help='display device output for parallel injections')
parser.add_option('-T', '--timeout', action='store', type='int',
                  dest='seconds', default=300,
                  help='device read timeout in seconds [default=300]')
parser.add_option('--dut_serial', action='store', type='str',
                  dest='dut_serial_port', default=None,
                  help='dut serial port [p2020 default=/dev/ttyUSB1]           '
                       '[a9 default=/dev/ttyACM0] (overridden by simics)')
parser.add_option('--dut_prompt', action='store', type='str',
                  dest='dut_prompt', default=None,
                  help='dut console prompt [p2020 default=root@p2020rdb:~#]    '
                       '[a9 default=[root@ZED]#] (overridden by simics)')
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
                      help='start the log server, optionally specify server '
                           'port [default=8000]')
mode_group.add_option('-Z', '--zedboard_info', action='store_true',
                      dest='zedboards', default=False,
                      help='print information about attached ZedBoards')
mode_group.add_option('-b', '--list_campaigns', action='store_true',
                      dest='list', help='list campaigns')
mode_group.add_option('-d', '--delete_results', action='store_true',
                      dest='delete_results', default=False,
                      help='delete results for a campaign')
mode_group.add_option('-e', '--delete_campaign', action='store_true',
                      dest='delete_campaign', default=False,
                      help='delete campaign (results and campaign information)')
mode_group.add_option('-D', '--delete_all', action='store_true',
                      dest='delete_all', default=False,
                      help='delete results and/or injected checkpoints for all '
                           'campaigns')
mode_group.add_option('-M', '--merge', action='store', type='str',
                      dest='merge_directory', default=None,
                      help='merge campaigns from external DIRECTORY into the '
                           'local directory')
parser.add_option_group(mode_group)

simics_mode_group = optparse.OptionGroup(parser, 'DrSEUs Modes (Simics only)',
                                         'These modes are only available for '
                                         'Simics campaigns')
simics_mode_group.add_option('-r', '--regenerate', action='store', type='int',
                             dest='iteration', default=0,
                             help='regenerate a campaign iteration and '
                                  'launch in Simics')
simics_mode_group.add_option('-u', '--update', action='store_true',
                             dest='dependencies', default=False,
                             help='update gold checkpoint dependency paths')
parser.add_option_group(simics_mode_group)

new_group = optparse.OptionGroup(parser, 'New Campaign Options',
                                 'Use these to create a new campaign, they will'
                                 ' be saved')
new_group.add_option('-s', '--simics', action='store_true', dest='use_simics',
                     default=False, help='use simics simulator')
new_group.add_option('-A', '--arch', action='store',  choices=['a9', 'p2020'],
                     dest='architecture', default='p2020',
                     help='target architecture [default=p2020]')
new_group.add_option('-m', '--timing', action='store', type='int',
                     dest='iterations', default=5,
                     help='number of timing iterations to run [default=5]')
new_group.add_option('-a', '--args', action='store', type='str',
                     dest='arguments', default='',
                     help='arguments for application')
new_group.add_option('-L', '--directory', action='store', type='str',
                     dest='directory', default='fiapps',
                     help='directory to look for files [default=fiapps]')
new_group.add_option('-f', '--files', action='store', type='str', dest='files',
                     default='',
                     help='comma-separated list of files to copy to device')
new_group.add_option('-o', '--output', action='store', type='str',
                     dest='file', default='result.dat',
                     help='target application output file [default=result.dat]')
new_group.add_option('-x', '--aux', action='store_true', dest='use_aux',
                     default=False, help='use second device during testing')
new_group.add_option('-y', '--aux_app', action='store',
                     type='str', dest='aux_app', default='',
                     help='target application for auxiliary device')
new_group.add_option('-z', '--aux_args', action='store', type='str',
                     dest='aux_args', default='',
                     help='arguments for auxiliary application')
new_group.add_option('-F', '--aux_files', action='store', type='str',
                     dest='aux_files', default='',
                     help='comma-separated list of files to copy to aux device')
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
                            help='number of gold checkpoints to target for '
                                 'creation (actual number of checkpoints may '
                                 'be different) [default=50]')
parser.add_option_group(new_simics_group)

injection_group = optparse.OptionGroup(parser, 'Injection Options', 'Use these '
                                       'when performing injections '
                                       '(-i or --inject)')
injection_group.add_option('-n', '--iterations', action='store', type='int',
                           dest='num_iterations', default=10,
                           help='number of iterations to perform [default=10]')
injection_group.add_option('-I', '--injections', action='store', type='int',
                           dest='num_injections', default=1,
                           help='number of injections per execution run '
                                '[default=1]')
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
simics_injection_group.add_option('--compare_all', action='store_true',
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
supervise_group.add_option('-w', '--wireshark', action='store_true',
                           dest='capture', help='run remote packet capture')
parser.add_option_group(supervise_group)
options, args = parser.parse_args()

modes = 0
for mode in (options.application, options.inject, options.supervise,
             options.view_logs, options.zedboards, options.list,
             options.delete_results, options.delete_campaign,
             options.delete_all, options.merge_directory, options.iteration,
             options.dependencies):
    if mode:
        modes += 1
if modes == 0:
    parser.error('please specify a mode (list options with --help)')
elif modes > 1:
    parser.error('only one mode can be used at a time')
if options.view_logs:
    if len(args) > 1:
        parser.error('extra arguments: '+' '.join(args[1:]))
else:
    if len(args) > 0:
        parser.error('extra arguments: '+' '.join(args))

if options.application:
    options.debug = True
    utilities.create_campaign(options)
elif options.inject:
    if not options.campaign_number:
        options.campaign_number = utilities.get_last_campaign()
    campaign_data = utilities.get_campaign_data(options.campaign_number)
    starting_iteration = utilities.get_next_iteration(options.campaign_number)
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
    if options.num_processes > 1 and (campaign_data['use_simics'] or
                                      campaign_data['architecture'] == 'a9'):
        if not campaign_data['use_simics'] and \
                campaign_data['architecture'] == 'a9':
            zedboards = utilities.find_uart_serials().keys()
        processes = []
        for i in xrange(options.num_processes):
            if not campaign_data['use_simics'] and \
                    campaign_data['architecture'] == 'a9':
                if i < len(zedboards):
                    options.dut_serial_port = zedboards[i]
                else:
                    break
            process = multiprocessing.Process(
                target=utilities.perform_injections,
                args=(campaign_data, iteration_counter, last_iteration, options)
            )
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
        options.debug = True
        utilities.perform_injections(campaign_data, iteration_counter,
                                     last_iteration, options)
elif options.supervise:
    options.debug = True
    if not options.campaign_number:
        options.campaign_number = utilities.get_last_campaign()
    campaign_data = utilities.get_campaign_data(options.campaign_number)
    iteration_counter = multiprocessing.Value(
        'I', utilities.get_next_iteration(options.campaign_number))
    drseus = utilities.load_campaign(campaign_data, options)
    supervisor(campaign_data, drseus, options, iteration_counter).main()
elif options.view_logs:
    utilities.view_logs(args)
elif options.zedboards:
    utilities.print_zedboard_info()
elif options.list:
    utilities.list_campaigns()
elif options.delete_results:
    if not options.campaign_number:
        options.campaign_number = utilities.get_last_campaign()
    utilities.delete_results(options.campaign_number)
elif options.delete_campaign:
    if not options.campaign_number:
        options.campaign_number = utilities.get_last_campaign()
    utilities.delete_campaign(options.campaign_number)
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
elif options.merge_directory:
    utilities.merge_campaigns(options.merge_directory)
elif options.iteration:
    if not options.campaign_number:
        options.campaign_number = utilities.get_last_campaign()
    campaign_data = utilities.get_campaign_data(options.campaign_number)
    if not campaign_data['use_simics']:
        raise Exception('This feature is only available for Simics campaigns')
    drseus = utilities.load_campaign(campaign_data, options)
    injection_data = utilities.get_injection_data(campaign_data,
                                                  options.iteration)
    checkpoint = drseus.debugger.regenerate_checkpoints(options.iteration,
                                                        drseus.cycles_between,
                                                        injection_data)
    drseus.debugger.launch_simics_gui(checkpoint)
    shutil.rmtree('simics-workspace/injected-checkpoints/' +
                  str(campaign_data['campaign_number'])+'/' +
                  str(options.iteration))
elif options.dependencies:
    print('updating gold checkpoint path dependencies...', end='')
    sys.stdout.flush()
    for campaign in os.listdir('simics-workspace/gold-checkpoints'):
        utilities.update_checkpoint_dependencies(campaign)
    print('done')
