from __future__ import print_function
from datetime import datetime
from django.core.management import execute_from_command_line as django_command
import os
import shutil
import signal
import sys

from fault_injector import fault_injector
from jtag import find_ftdi_serials, find_uart_serials
import simics_config
from sql import sql


def print_zedboard_info():
    ftdis = find_ftdi_serials()
    uarts = find_uart_serials()
    print('Attached ZedBoard Information')
    print('FTDI JTAG device serial numbers: ')
    for serial in ftdis:
        print('\t'+serial)
    print('Cypress UART device serial numbers:')
    for uart, serial in uarts.iteritems():
        print('\t'+uart+': '+serial)


def list_campaigns():
    with sql(row_factory='row') as db:
        db.cursor.execute('SELECT campaign_number, application, architecture, '
                          'use_simics FROM log_campaign')
        campaign_list = db.cursor.fetchall()
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
    with sql(row_factory='row') as db:
        db.cursor.execute('SELECT campaign_number FROM log_campaign '
                          'ORDER BY campaign_number DESC LIMIT 1')
        campaign_data = db.cursor.fetchone()
    if campaign_data is None:
        campaign_number = 0
    else:
        campaign_number = campaign_data['campaign_number']
    return campaign_number


def get_campaign_data(campaign_number):
    with sql(row_factory='row') as db:
        db.cursor.execute('SELECT * FROM log_campaign WHERE campaign_number=?',
                          (campaign_number,))
        campaign_data = db.cursor.fetchone()
    if campaign_data is None:
        raise Exception('could not find campaign number '+str(campaign_number))
    return campaign_data


def backup_database():
    print('backing up database...', end='')
    db_backup = ('campaign-data/' +
                 '-'.join([str(unit).zfill(2)
                           for unit in datetime.now().timetuple()[:6]]) +
                 '.db.sqlite3')
    shutil.copyfile('campaign-data/db.sqlite3', db_backup)
    print('done')


def delete_results(campaign_number):
    backup_database()
    if os.path.exists('campaign-data/'+str(campaign_number)+'/results'):
        shutil.rmtree('campaign-data/'+str(campaign_number)+'/results')
        print('deleted results')
    if os.path.exists('campaign-data/db.sqlite3'):
        with sql() as db:
            db.cursor.execute('DELETE FROM log_simics_memory_diff WHERE '
                              'result_id IN (SELECT id FROM log_result WHERE '
                              'campaign_id=?)', (campaign_number,))
            db.cursor.execute('DELETE FROM log_simics_register_diff WHERE '
                              'result_id IN (SELECT id FROM log_result WHERE '
                              'campaign_id=?)', (campaign_number,))
            db.cursor.execute('DELETE FROM log_injection WHERE '
                              'result_id IN (SELECT id FROM log_result WHERE '
                              'campaign_id=?)', (campaign_number,))
            db.cursor.execute('DELETE FROM log_result WHERE campaign_id=?',
                              (campaign_number,))
            db.connection.commit()
        print('flushed database')
    if os.path.exists('simics-workspace/injected-checkpoints/' +
                      str(campaign_number)):
        shutil.rmtree('simics-workspace/injected-checkpoints/' +
                      str(campaign_number))
        print('deleted injected checkpoints')


def delete_campaign(campaign_number):
    delete_results(campaign_number)
    if os.path.exists('campaign-data/db.sqlite3'):
        with sql() as db:
            db.cursor.execute('DELETE FROM log_campaign '
                              'WHERE campaign_number=?', (campaign_number,))
            db.connection.commit()
        print('deleted campaign from database')
    if os.path.exists('campaign-data/'+str(campaign_number)):
        shutil.rmtree('campaign-data/'+str(campaign_number))
        print('deleted campaign data')
    if os.path.exists('simics-workspace/gold-checkpoints/' +
                      str(campaign_number)):
        shutil.rmtree('simics-workspace/gold-checkpoints/' +
                      str(campaign_number))
        print('deleted gold checkpoints')


def create_campaign(options):
    campaign_number = get_last_campaign() + 1
    if options.architecture == 'p2020':
        if options.dut_serial_port is None:
            options.dut_serial_port = '/dev/ttyUSB1'
        if options.dut_prompt is None:
            options.dut_prompt = 'root@p2020rdb:~#'
    elif options.architecture == 'a9':
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
        initialize_database()
    drseus = fault_injector(campaign_number, options.dut_serial_port,
                            options.aux_serial_port, options.dut_prompt,
                            options.aux_prompt, options.debugger_ip_address,
                            options.architecture, options.use_aux,
                            options.debug, options.use_simics, options.seconds)
    drseus.setup_campaign(options.directory, options.architecture,
                          options.application, options.arguments, options.file,
                          options.files, options.aux_files,
                          options.timing_iterations, aux_application,
                          options.aux_args, options.use_aux_output,
                          options.num_checkpoints, options.kill_dut)
    print('\nsuccessfully setup campaign')


def get_injection_data(campaign_data, result_id):
    with sql(row_factory='row') as db:
        db.cursor.execute('SELECT register,gold_value,injected_value,'
                          'checkpoint_number,bit,target_index,target,'
                          'config_object,config_type,register_index,field '
                          'FROM log_injection INNER JOIN log_result ON '
                          '(log_injection.result_id=log_result.id) '
                          'WHERE log_result.id=?', (result_id,))
        injection_data = db.cursor.fetchall()
    injection_data = sorted(injection_data,
                            key=lambda x: x['checkpoint_number'])
    return injection_data


def load_campaign(campaign_data, options):
    if campaign_data['architecture'] == 'p2020':
        if options.dut_serial_port is None:
            options.dut_serial_port = '/dev/ttyUSB1'
        if options.dut_prompt is None:
            options.dut_prompt = 'root@p2020rdb:~#'
    elif campaign_data['architecture'] == 'a9':
        if options.dut_serial_port is None:
            options.dut_serial_port = '/dev/ttyACM0'
        if options.dut_prompt is None:
            options.dut_prompt = '[root@ZED]#'
    drseus = fault_injector(campaign_data['campaign_number'],
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


def perform_injections(campaign_data, iteration_counter, options,
                       interactive=False):
    drseus = load_campaign(campaign_data, options)

    def interrupt_handler(signum, frame):
        drseus.log_result('Interrupted', 'Incomplete')
        if os.path.exists('campaign-data/results/' +
                          str(campaign_data['campaign_number'])+'/' +
                          str(drseus.result_id)):
            shutil.rmtree('campaign-data/results/' +
                          str(campaign_data['campaign_number'])+'/' +
                          str(drseus.result_id))
        if not drseus.use_simics:
            try:
                drseus.debugger.continue_dut()
            except:
                pass
        try:
            drseus.debugger.close()
        except:
            pass
        if drseus.use_simics:
            if os.path.exists('simics-workspace/injected-checkpoints/' +
                              str(campaign_data['campaign_number'])+'/' +
                              str(drseus.result_id)):
                shutil.rmtree('simics-workspace/injected-checkpoints/' +
                              str(campaign_data['campaign_number'])+'/' +
                              str(drseus.result_id))
        if not interactive:
            sys.exit()
    signal.signal(signal.SIGINT, interrupt_handler)

    if options.selected_targets is not None:
        selected_targets = options.selected_targets.split(',')
    else:
        selected_targets = None
    drseus.inject_and_monitor(iteration_counter, options.num_injections,
                              selected_targets, campaign_data['output_file'],
                              campaign_data['use_aux_output'],
                              options.compare_all)


def initialize_database():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "log.settings")
    django_command([sys.argv[0], 'migrate', '--run-syncdb'])


def view_logs(args):
    try:
        port = int(args[0])
    except:
        port = 8000
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "log.settings")
    django_command([sys.argv[0], 'runserver', str(port)])


def update_checkpoint_dependencies(campaign_number):
    for checkpoint in os.listdir('simics-workspace/gold-checkpoints/' +
                                 str(campaign_number)):
        config = simics_config.read_configuration(
            'simics-workspace/gold-checkpoints/' +
            str(campaign_number)+'/'+checkpoint)
        os.rename('simics-workspace/gold-checkpoints/' +
                  str(campaign_number)+'/'+checkpoint+'/config',
                  'simics-workspace/gold-checkpoints/' +
                  str(campaign_number)+'/'+checkpoint+'/config.bak')
        paths = simics_config.get_attr(config, 'sim', 'checkpoint_path')
        new_paths = []
        for path in paths:
            path_list = path.split('/')
            path_list = path_list[path_list.index('simics-workspace'):]
            path_list[-2] = str(campaign_number)
            new_paths.append('\"'+os.getcwd()+'/'+'/'.join(path_list))
        simics_config.set_attr(config, 'sim', 'checkpoint_path',
                               new_paths)
        simics_config.write_configuration(
            config, 'simics-workspace/gold-checkpoints/' +
            str(campaign_number)+'/'+checkpoint, False)


def merge_campaigns(merge_directory):
    last_campaign_number = get_last_campaign()
    backup_database()
    with sql(row_factory='row') as db, \
        sql(database=merge_directory+'/campaign-data/db.sqlite3',
            row_factory='dict') as db_new:
        db_new.cursor.execute('SELECT * FROM log_campaign')
        new_campaigns = db_new.cursor.fetchall()
        for new_campaign in new_campaigns:
            print('merging campaign: \"'+merge_directory+'/' +
                  new_campaign['command']+'\"')
            old_campaign_number = new_campaign['campaign_number']
            new_campaign['campaign_number'] += last_campaign_number
            if os.path.exists(merge_directory+'/campaign-data/' +
                              str(old_campaign_number)):
                print('\tcopying campaign data...', end='')
                shutil.copytree(merge_directory+'/campaign-data/' +
                                str(old_campaign_number),
                                'campaign-data/' +
                                str(new_campaign['campaign_number']))
                print('done')
            if os.path.exists(merge_directory+'/simics-workspace/'
                              'gold-checkpoints/'+str(old_campaign_number)):
                print('\tcopying gold checkpoints...', end='')
                shutil.copytree(merge_directory+'/simics-workspace/'
                                'gold-checkpoints/'+str(old_campaign_number),
                                'simics-workspace/gold-checkpoints/' +
                                str(new_campaign['campaign_number']))
                print('done')
                print('\tupdating checkpoint dependency paths...', end='')
                sys.stdout.flush()
                update_checkpoint_dependencies(new_campaign['campaign_number'])
                print('done')
            print('\tcopying results...', end='')
            db.insert_dict('campaign', new_campaign)
            db_new.cursor.execute('SELECT * FROM log_result WHERE '
                                  'campaign_id=?', (old_campaign_number,))
            new_results = db_new.cursor.fetchall()
            for new_result in new_results:
                old_result_id = new_result['id']
                new_result['campaign_id'] += last_campaign_number
                del new_result['id']
                db.insert_dict('result', new_result)
                new_result_id = sql.lastrowid
                for table in ['injection', 'simics_register_diff',
                              'simics_memory_diff']:
                    db_new.cursor.execute('SELECT * FROM log_'+table+' '
                                          'WHERE result_id=?', (old_result_id,))
                    new_result_items = db_new.cursor.fetchall()
                    for new_result_item in new_result_items:
                        new_result_item['result_id'] = new_result_id
                        del new_result_item['id']
                        db.insert_dict(table, new_result_item)
            print('done')
