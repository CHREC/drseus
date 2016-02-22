from datetime import datetime
from django.core.management import execute_from_command_line as django_command
from io import StringIO
from json import dump
from multiprocessing import Process, Value
from os import environ, getcwd, listdir, makedirs, remove
from os.path import exists
from paramiko import RSAKey
from shutil import copy, copytree, rmtree
from subprocess import check_call
from sys import argv, stdout
from terminaltables import AsciiTable

from database import database
from fault_injector import fault_injector
from jtag import openocd
from power_switch import power_switch
from simics_config import simics_config
from supervisor import supervisor


def detect_power_switch_devices(options):
    if exists('devices.json'):
        if input('continue and overwrite devices.json? [Y/n]') \
                not in ('N', 'n'):
            remove('devices.json')
        else:
            return
    devices = []
    with power_switch(options) as ps:
        status = ps.get_status()
        ps.set_outlet('all', 'off', 1)
        ftdi_serials_pre = openocd.find_ftdi_serials()
        uart_serials_pre = openocd.find_uart_serials().values()
        for outlet in ps.outlets:
            ps.set_outlet(outlet, 'on', 5)
            ftdi_serials = [serial for serial in openocd.find_ftdi_serials()
                            if serial not in ftdi_serials_pre]
            uart_serials = [serial for serial
                            in openocd.find_uart_serials().values()
                            if serial not in uart_serials_pre]
            ps.set_outlet(outlet, 'off', 1)
            if len(ftdi_serials) > 1 or len(uart_serials) > 1:
                print('too many devices detected on outlet', outlet)
                continue
            if not len(ftdi_serials) or not len(uart_serials):
                print('no devices detected on outlet', outlet)
                continue
            print('found zedboard on outlet', outlet)
            devices.append({'outlet': outlet,
                            'ftdi': ftdi_serials[0],
                            'uart': uart_serials[0]})
        for outlet in status:
            ps.set_outlet(outlet['outlet'], outlet['status'], 1)
    with open('devices.json', 'w') as device_file:
        dump(devices, device_file, indent=4)
    print('saved device information to devices.json')


def list_serials(none=None):
    ftdis = openocd.find_ftdi_serials()
    uarts = openocd.find_uart_serials()
    print('FTDI JTAG device serial numbers: ')
    for serial in ftdis:
        print('\t'+serial)
    print('Cypress UART device serial numbers:')
    for uart, serial in uarts.items():
        print('\t'+uart+': '+serial)


def set_outlet(options):
    try:
        options.outlet = int(options.outlet)
    except ValueError:
        with power_switch(options) as ps:
            ps.set_device(options.outlet, options.state, 1)
    else:
        with power_switch(options) as ps:
            ps.set_outlet(options.outlet, options.state, 1)


def list_outlets(options):
    with power_switch(options) as ps:
        ps.print_status()


def list_campaigns(none=None):
    table = AsciiTable([['ID', 'Results', 'Command', 'Arch', 'Simics']],
                       'DrSEUs Campaigns')
    with database(campaign={'id': '*'}) as db:
        campaign_list = db.get_campaign()
        for campaign in campaign_list:
            db.campaign['id'] = campaign['id']
            results = db.get_count('result', 'campaign')
            items = []
            for i, item in enumerate((str(campaign['id']), str(results),
                                      campaign['command'],
                                      campaign['architecture'],
                                      str(bool(campaign['simics'])))):
                if len(item) < table.column_max_width(i):
                    items.append(item)
                else:
                    items.append(item[:table.column_max_width(i)-4]+'...')
            table.table_data.append(items)
    print(table.table)


def get_campaign(campaign_id):
    with database(campaign={'id': campaign_id}) as db:
        campaign = db.get_campaign()
    if campaign is None:
        raise Exception('could not find campaign ID '+str(campaign_id))
    return campaign


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
        with database(campaign={'id': campaign_id}) as db:
            db.delete_results()
        print('flushed database')
        if exists('simics-workspace/injected-checkpoints/'+str(campaign_id)):
            rmtree('simics-workspace/injected-checkpoints/'+str(campaign_id))
            print('deleted injected checkpoints')

    def delete_campaign(campaign_id):
        with database(campaign={'id': campaign_id}) as db:
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
        database().delete_database()
        print('deleted database')


def create_campaign(options):
    if options.directory == 'fiapps':
        if not exists('fiapps'):
            check_call('./setup_apps.sh')
        check_call(['make', options.application], cwd=getcwd()+'/fiapps/')
    else:
        if not exists(options.directory):
            raise Exception('cannot find directory '+options.directory)
    if options.simics and not exists('simics-workspace'):
        check_call('./setup_simics_workspace.sh')
    rsakey_file = StringIO()
    RSAKey.generate(1024).write_private_key(rsakey_file)
    rsakey = rsakey_file.getvalue()
    rsakey_file.close()
    campaign = {
        'architecture': options.architecture,
        'aux': options.aux,
        'aux_command': ((options.aux_application if options.aux_application
                         else options.application) +
                        ((' '+options.aux_arguments) if options.aux_arguments
                         else '')) if options.aux else None,
        'aux_output': '',
        'command': options.application+((' '+options.arguments)
                                        if options.arguments else ''),
        'debugger_output': '',
        'description': options.description,
        'dut_output': '',
        'kill_dut': options.kill_dut,
        'output_file': options.output_file,
        'rsakey': rsakey,
        'simics': options.simics,
        'timestamp': None,
        'use_aux_output': options.aux and options.use_aux_output}
    if options.aux_application is None:
        options.aux_application = options.application
    with database(campaign) as db:
        db.insert('campaign')
    campaign_directory = 'campaign-data/'+str(campaign['id'])
    if exists(campaign_directory):
        raise Exception('directory already exists: '
                        'campaign-data/'+str(campaign['id']))
    else:
        makedirs(campaign_directory)
    options.debug = True
    drseus = fault_injector(campaign, options)
    drseus.setup_campaign()
    print('\nsuccessfully setup campaign')


def inject_campaign(options):
    campaign = get_campaign(options.campaign_id)

    def perform_injections(iteration_counter, switch):
        drseus = fault_injector(campaign, options, switch)
        try:
            drseus.inject_campaign(iteration_counter)
        except KeyboardInterrupt:
            with drseus.db as db:
                db.log_event('Information', 'User', 'Interrupted',
                             db.log_exception)
            drseus.debugger.close()
            drseus.db.result['outcome'] = 'Interrupted'
            with drseus.db as db:
                db.log_result(False)
        except:
            with drseus.db as db:
                db.log_event('Error', 'DrSEUs', 'Exception', db.log_exception)
            drseus.debugger.close()
            drseus.db.result['outcome'] = 'Exception'
            with drseus.db as db:
                db.log_result(False)

# def inject_campaign(options):
    if options.iterations is not None:
        iteration_counter = Value('L', options.iterations)
    else:
        iteration_counter = None
    if not campaign['simics'] and campaign['architecture'] == 'a9' \
            and options.power:
        switch = power_switch(options)
    else:
        switch = None
    if options.processes > 1 and (campaign['simics'] or
                                  campaign['architecture'] == 'a9'):
        if not campaign['simics'] and \
                campaign['architecture'] == 'a9':
            uarts = list(openocd.find_uart_serials().keys())
        processes = []
        for i in range(options.processes):
            if not campaign['simics'] and \
                    campaign['architecture'] == 'a9':
                if i < len(uarts):
                    options.dut_serial_port = uarts[i]
                else:
                    break
            process = Process(target=perform_injections,
                              args=[iteration_counter, switch])
            processes.append(process)
            process.start()
        try:
            for process in processes:
                process.join()
        except KeyboardInterrupt:
            for process in processes:
                process.join()
    else:
        perform_injections(iteration_counter, switch)


def regenerate(options):
    campaign = get_campaign(options.campaign_id)
    if not campaign['simics']:
        raise Exception('This feature is only available for Simics campaigns')
    with database() as db:
        db.result['id'] = options.result_id
        injections = db.get_item('injection')
    drseus = fault_injector(campaign, options)
    checkpoint = drseus.debugger.regenerate_checkpoints(injections)
    drseus.debugger.launch_simics_gui(checkpoint)
    rmtree('simics-workspace/injected-checkpoints/'+str(campaign['id']) +
           '/'+str(options.result_id))


def view_logs(options):
    environ.setdefault("DJANGO_SETTINGS_MODULE", "log.settings")
    django_command(['drseus', 'runserver', ('0.0.0.0:' if options.external
                                            else '')+str(options.port)])


def run_django_command(options):
    environ.setdefault("DJANGO_SETTINGS_MODULE", "log.settings")
    command = [argv[0]+' '+options.command]
    for item in options.django_command:
        command.append(item)
    django_command(command)


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
    with database() as db, database(campaign={'id': '*'},
                                    database_file=options.directory +
                                    '/campaign-data/db.sqlite3') as db_new:
        for new_campaign in db_new.get_campaign():
            print('merging campaign: \"'+options.directory+'/' +
                  new_campaign['command']+'\"')
            db_new.campaign['id'] = new_campaign['id']
            db.insert('campaign', new_campaign)
            if exists(options.directory+'/campaign-data/' +
                      str(db_new.campaign['id'])):
                print('\tcopying campaign data...', end='')
                copytree(options.directory+'/campaign-data/' +
                         str(db_new.campaign['id']),
                         'campaign-data/'+str(new_campaign['id']))
                print('done')
            if exists(options.directory+'/simics-workspace/gold-checkpoints/' +
                      str(db_new.campaign['id'])):
                print('\tcopying gold checkpoints...', end='')
                copytree(options.directory+'/simics-workspace/'
                         'gold-checkpoints/'+str(db_new.campaign['id']),
                         'simics-workspace/gold-checkpoints/' +
                         str(new_campaign['id']))
                print('done')
                print('\tupdating checkpoint dependency paths...', end='')
                stdout.flush()
                __update_checkpoint_dependencies(new_campaign['id'])
                print('done')
            print('\tcopying results...', end='')
            for new_result in db_new.get_result():
                db_new.result['id'] = new_result['id']
                db.insert('result', new_result)
                for table in ['injection', 'simics_register_diff',
                              'simics_memory_diff']:
                    for new_item in db_new.get_item(table):
                        new_item['result_id'] = new_result['id']
                        db.insert(table, new_item)
            print('done')


def launch_openocd(options):
    debugger = openocd(None, options)
    print('Launched '+str(debugger))
    debugger.openocd.wait()


def launch_supervisor(options):
    supervisor(get_campaign(options.campaign_id), options).cmdloop()
