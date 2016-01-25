from datetime import datetime
from django.core.management import execute_from_command_line as django_command
from io import StringIO
from multiprocessing import Process, Value
from os import environ, getcwd, listdir, mkdir, remove
from os.path import exists
from paramiko import RSAKey
from shutil import copy, copytree, rmtree
from subprocess import check_call
from sys import stdout

from database import database
from fault_injector import fault_injector
from jtag import find_ftdi_serials, find_uart_serials, openocd
from simics_config import simics_config
from supervisor import supervisor


def print_zedboard_info(none=None):
    ftdis = find_ftdi_serials()
    uarts = find_uart_serials()
    print('Attached ZedBoard Information')
    print('FTDI JTAG device serial numbers: ')
    for serial in ftdis:
        print('\t'+serial)
    print('Cypress UART device serial numbers:')
    for uart, serial in uarts.items():
        print('\t'+uart+': '+serial)


def list_campaigns(none=None):
    with database(campaign_data={'id': '*'}) as db:
        campaign_list = db.get_campaign_data()
    print('DrSEUs Campaigns:')
    print('ID\tArchitecture\tSimics\tCommand')
    for campaign in campaign_list:
        print(str(campaign['id'])+'\t'+campaign['architecture']+'\t\t' +
              str(bool(campaign['use_simics']))+'\t'+campaign['command'])


def get_campaign_data(campaign_id):
    with database(campaign_data={'id': campaign_id}) as db:
        campaign_data = db.get_campaign_data()
    if campaign_data is None:
        raise Exception('could not find campaign ID '+str(campaign_id))
    return campaign_data


def backup_database(none=None):
    if exists('campaign-data/db.sqlite3'):
        print('backing up database...', end='')
        db_backup = ('campaign-data/' +
                     '-'.join([str(unit).zfill(2)
                               for unit in datetime.now().timetuple()[:6]]) +
                     '.db.sqlite3')
        copy('campaign-data/db.sqlite3', db_backup)
        print('done')


def clean(none=None):
    if exists('campaign-data/'):
        deleted_backup = False
        for item in listdir('campaign-data/'):
            if '.db.sqlite3' in item:
                remove('campaign-data/'+item)
                deleted_backup = True
        if deleted_backup:
            print('deleted database backup(s)')
    if exists('simics-workspace/injected-checkpoints'):
        rmtree('simics-workspace/injected-checkpoints')
        print('deleted injected checkpoints')


def delete(options):

    def delete_results(campaign_id):
        backup_database()
        if exists('campaign-data/'+str(campaign_id)+'/results'):
            rmtree('campaign-data/'+str(campaign_id)+'/results')
            print('deleted results')
        if exists('campaign-data/db.sqlite3'):
            with database(campaign_data={'id': campaign_id}) as db:
                db.delete_results()
            print('flushed database')
        if exists('simics-workspace/injected-checkpoints/'+str(campaign_id)):
            rmtree('simics-workspace/injected-checkpoints/'+str(campaign_id))
            print('deleted injected checkpoints')

    def delete_campaign(campaign_id):
        if exists('campaign-data/db.sqlite3'):
            with database(campaign_data={'id': campaign_id}) as db:
                db.delete_campaign()
            print('deleted campaign '+str(campaign_id)+' from database')
        if exists('campaign-data/'+str(campaign_id)):
            rmtree('campaign-data/'+str(campaign_id))
            print('deleted campaign data')
        if exists('simics-workspace/gold-checkpoints/'+str(campaign_id)):
            rmtree('simics-workspace/gold-checkpoints/'+str(campaign_id))
            print('deleted gold checkpoints')
        if exists('simics-workspace/injected-checkpoints/'+str(campaign_id)):
            rmtree('simics-workspace/injected-checkpoints/'+str(campaign_id))
            print('deleted injected checkpoints')

# def delete(options):
    if options.delete in ('results', 'r'):
        delete_results(options.campaign_id)
    elif options.delete in ('campaign', 'c'):
        delete_campaign(options.campaign_id)
    elif options.delete in ('all', 'a'):
        if exists('simics-workspace/gold-checkpoints'):
            rmtree('simics-workspace/gold-checkpoints')
            print('deleted gold checkpoints')
        if exists('simics-workspace/injected-checkpoints'):
            rmtree('simics-workspace/injected-checkpoints')
            print('deleted injected checkpoints')
        if exists('campaign-data'):
            rmtree('campaign-data')
            print('deleted campaign data')


def create_campaign(options):
    if options.directory == 'fiapps':
        if not exists('fiapps'):
            check_call('./setup_apps.sh')
        check_call(['make', options.application], cwd=getcwd()+'/fiapps/')
    else:
        if not exists(options.directory):
            raise Exception('cannot find directory '+options.directory)
    if options.use_simics and not exists('simics-workspace'):
        check_call('./setup_simics_workspace.sh')
    if not exists('campaign-data/db.sqlite3'):
        if not exists(('campaign-data')):
            mkdir('campaign-data')
        environ.setdefault("DJANGO_SETTINGS_MODULE", "log.settings")
        django_command(['drseus', 'migrate', '--run-syncdb'])
    rsakey_file = StringIO()
    RSAKey.generate(1024).write_private_key(rsakey_file)
    rsakey = rsakey_file.getvalue()
    rsakey_file.close()
    campaign_data = {
        'application': options.application,
        'architecture': options.architecture,
        'aux_command': ((options.aux_application if options.aux_application
                         else options.application) +
                        ((' '+options.aux_arguments) if options.aux_arguments
                         else '')) if options.use_aux else None,
        'aux_output': '',
        'command': options.application+((' '+options.arguments)
                                        if options.arguments else ''),
        'debugger_output': '',
        'description': options.description,
        'dut_output': '',
        'kill_dut': options.kill_dut,
        'output_file': options.file,
        'rsakey': rsakey,
        'timestamp': None,
        'use_aux': options.use_aux,
        'use_aux_output': options.use_aux and options.use_aux_output,
        'use_simics': options.use_simics}
    if options.aux_application is None:
        options.aux_application = options.application
    with database(campaign_data) as db:
        db.insert_dict('campaign')
        campaign_data['id'] = db.cursor.lastrowid
    campaign_directory = 'campaign-data/'+str(campaign_data['id'])
    if exists(campaign_directory):
        raise Exception('directory already exists: '
                        'campaign-data/'+str(campaign_data['id']))
    else:
        mkdir(campaign_directory)
    options.debug = True
    drseus = fault_injector(campaign_data, options)
    drseus.setup_campaign()
    print('\nsuccessfully setup campaign')


def inject_campaign(options):
    campaign_data = get_campaign_data(options.campaign_id)

    def perform_injections(iteration_counter):
        drseus = fault_injector(campaign_data, options)
        drseus.inject_campaign(iteration_counter)

# def inject_campaign(options):
    processes = []
    if options.iterations is not None:
        iteration_counter = Value('L', options.iterations)
    else:
        iteration_counter = None
    if options.processes > 1 and (campaign_data['use_simics'] or
                                  campaign_data['architecture'] == 'a9'):
        if not campaign_data['use_simics'] and \
                campaign_data['architecture'] == 'a9':
            zedboards = list(find_uart_serials().keys())
        for i in range(options.processes):
            if not campaign_data['use_simics'] and \
                    campaign_data['architecture'] == 'a9':
                if i < len(zedboards):
                    options.dut_serial_port = zedboards[i]
                else:
                    break
            process = Process(target=perform_injections,
                              args=[iteration_counter])
            processes.append(process)
            process.start()
        for process in processes:
            process.join()
    else:
        options.debug = True
        perform_injections(iteration_counter)


def regenerate(options):
    campaign_data = get_campaign_data(options.campaign_id)
    if not campaign_data['use_simics']:
        raise Exception('This feature is only available for Simics campaigns')
    with database(result_data={'id': options.result_id}) as db:
        injection_data = db.get_result_item_data('injection')
    drseus = fault_injector(campaign_data, options)
    checkpoint = drseus.debugger.regenerate_checkpoints(injection_data)
    drseus.debugger.launch_simics_gui(checkpoint)
    rmtree('simics-workspace/injected-checkpoints/'+str(campaign_data['id']) +
           '/'+str(options.result_id))


def view_logs(options):
    environ.setdefault("DJANGO_SETTINGS_MODULE", "log.settings")
    django_command(['drseus', 'runserver', str(options.port)])


def __update_checkpoint_dependencies(campaign_id):
    for checkpoint in listdir('simics-workspace/gold-checkpoints/' +
                              str(campaign_id)):
        with simics_config('simics-workspace/gold-checkpoints/' +
                           str(campaign_id)+'/'+checkpoint) as config:
            paths = config.get(config, 'sim', 'checkpoint_path')
            new_paths = []
            for path in paths:
                path_list = path.split('/')
                path_list = path_list[path_list.index('simics-workspace'):]
                path_list[-2] = str(campaign_id)
                new_paths.append('\"'+getcwd()+'/'+'/'.join(path_list))
            config.set(config, 'sim', 'checkpoint_path', new_paths)
            config.save()


def update_dependencies(none=None):
    if exists('simics-workspace/gold-checkpoints'):
        print('updating gold checkpoint path dependencies...', end='')
        stdout.flush()
        for campaign in listdir('simics-workspace/gold-checkpoints'):
            __update_checkpoint_dependencies(campaign)
        print('done')


def merge_campaigns(options):
    backup_database()
    with database() as db, database(campaign_data={'id': '*'},
                                    database_file=options.directory +
                                    '/campaign-data/db.sqlite3') as db_new:
        for new_campaign in db_new.get_campaign_data():
            print('merging campaign: \"'+options.directory+'/' +
                  new_campaign['command']+'\"')
            db_new.campaign_data['id'] = new_campaign['id']
            db.insert_dict('campaign', new_campaign)
            if exists(options.directory+'/campaign-data/' +
                      str(db_new.campaign_data['id'])):
                print('\tcopying campaign data...', end='')
                copytree(options.directory+'/campaign-data/' +
                         str(db_new.campaign_data['id']),
                         'campaign-data/'+str(new_campaign['id']))
                print('done')
            if exists(options.directory+'/simics-workspace/gold-checkpoints/' +
                      str(db_new.campaign_data['id'])):
                print('\tcopying gold checkpoints...', end='')
                copytree(options.directory+'/simics-workspace/'
                         'gold-checkpoints/'+str(db_new.campaign_data['id']),
                         'simics-workspace/gold-checkpoints/' +
                         str(new_campaign['id']))
                print('done')
                print('\tupdating checkpoint dependency paths...', end='')
                stdout.flush()
                __update_checkpoint_dependencies(new_campaign['id'])
                print('done')
            print('\tcopying results...', end='')
            for new_result in db_new.get_result_data():
                db_new.result_data['id'] = new_result['id']
                db.insert_dict('result', new_result)
                for table in ['injection', 'simics_register_diff',
                              'simics_memory_diff']:
                    for new_result_item in db_new.get_result_item_data(table):
                        new_result_item['result_id'] = new_result['id']
                        db.insert_dict(table, new_result_item)
            print('done')


def launch_openocd(options):
    debugger = openocd(None, None, options, None)
    print('Launched '+str(debugger))
    debugger.openocd.wait()


def launch_supervisor(options):
    supervisor(get_campaign_data(options.campaign_id), options).cmdloop()
