#!/usr/bin/python

from __future__ import print_function
import multiprocessing
import os
import shutil
import signal
import sys

from jtag import openocd
from options import arguments, options, parser
from supervisor import supervisor
import utilities

# TODO: add boot commands option
# TODO: fix inconsistent reloading when editing outcomes on result table page
# TODO: add modes to backup database and delete backups
# TODO: check for extra campaign data files (higher campaign number)
# TODO: add mode to redo injection iteration
# TODO: add fallback to power cycle when resetting dut
# TODO: add support for injection of multi-bit upsets
# TODO: add option for number of times to rerun app for latent fault case
# TODO: change Exception in simics_checkpoints.py to DrSEUsError
# TODO: update simics_checkpoints to use simics_config

modes = 0
for mode in (options.application, options.inject, options.supervise,
             options.view_logs, options.zedboards, options.list,
             options.delete_results, options.delete_campaign,
             options.delete_all, options.merge_directory, options.result_id,
             options.dependencies, options.openocd):
    if mode:
        modes += 1
if modes == 0:
    parser.error('please specify a mode (list options with --help)')
elif modes > 1:
    parser.error('only one mode can be used at a time')
if options.view_logs:
    if len(arguments) > 1:
        parser.error('extra arguments: '+' '.join(arguments[1:]))
else:
    if len(arguments) > 0:
        parser.error('extra arguments: '+' '.join(arguments))

if options.application:
    options.debug = True
    utilities.create_campaign(options)
elif options.inject:
    if not options.campaign_number:
        options.campaign_number = utilities.get_last_campaign()
    campaign_data = utilities.get_campaign_data(options.campaign_number)
    if campaign_data['use_simics']:
        if not os.path.exists('simics-workspace/injected-checkpoints/' +
                              str(options.campaign_number)):
            os.makedirs('simics-workspace/injected-checkpoints/' +
                        str(options.campaign_number))
    if not os.path.exists('campaign-data/'+str(options.campaign_number) +
                          '/results'):
        os.makedirs('campaign-data/'+str(options.campaign_number)+'/results')
    iteration_counter = multiprocessing.Value('L', options.injection_iterations)
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
                args=(campaign_data, iteration_counter, options)
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
        utilities.perform_injections(campaign_data, iteration_counter, options)
elif options.supervise:
    supervisor(options).cmdloop()
elif options.view_logs:
    utilities.view_logs(arguments)
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
elif options.result_id:
    if not options.campaign_number:
        options.campaign_number = utilities.get_last_campaign()
    campaign_data = utilities.get_campaign_data(options.campaign_number)
    if not campaign_data['use_simics']:
        raise Exception('This feature is only available for Simics campaigns')
    drseus = utilities.load_campaign(campaign_data, options)
    injection_data = utilities.get_injection_data(campaign_data,
                                                  options.result_id)
    checkpoint = drseus.debugger.regenerate_checkpoints(options.result_id,
                                                        drseus.cycles_between,
                                                        injection_data)
    drseus.debugger.launch_simics_gui(checkpoint)
    shutil.rmtree('simics-workspace/injected-checkpoints/' +
                  str(campaign_data['campaign_number'])+'/' +
                  str(options.result_id))
elif options.dependencies:
    print('updating gold checkpoint path dependencies...', end='')
    sys.stdout.flush()
    for campaign in os.listdir('simics-workspace/gold-checkpoints'):
        utilities.update_checkpoint_dependencies(campaign)
    print('done')
elif options.openocd:
    if options.dut_serial_port is None:
        options.dut_serial_port = '/dev/ttyACM0'
    debugger = openocd(None, None, options.dut_serial_port, None, None, None,
                       None, None, None, None, standalone=True)
    print('Launched '+str(debugger))
    debugger.openocd.wait()
