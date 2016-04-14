from bdb import BdbQuit
from datetime import datetime
from django.core.management import execute_from_command_line as django_command
from io import StringIO
from json import dump
from multiprocessing import Process, Value
from os import getcwd, listdir, mkdir, remove
from os.path import exists, isdir, join
from paramiko import RSAKey
from pdb import set_trace
from progressbar import ProgressBar
from progressbar.widgets import Bar, Percentage, SimpleProgress, Timer
# from shutil import copy, copytree, rmtree
from shutil import rmtree
from subprocess import check_call
from sys import argv, stdout
from tarfile import open as open_tar
from terminaltables import AsciiTable
from traceback import print_exc

from .database import database
from .fault_injector import fault_injector
from .jtag import openocd
from .log import initialize_django
from .power_switch import power_switch
from .simics.config import simics_config
from .supervisor import supervisor


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


def list_campaigns(options):
    options.campaign_id = '*'
    db = database(options)
    table = AsciiTable([['ID', 'Results', 'Command', 'Arch', 'Simics']],
                       'DrSEUs Campaigns')
    with db:
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


def get_campaign(options):
    with database(options) as db:
        campaign = db.get_campaign()
    if campaign is None:
        raise Exception('could not find campaign ID '+str(options.campaign_id))
    return campaign


def delete(options):
    try:
        db = database(options)
    except:
        db = None
    if options.delete in ('results', 'r'):
        print('deleting results for campaign', options.campaign_id)
        if exists('campaign-data/'+str(options.campaign_id)+'/results'):
            rmtree('campaign-data/'+str(options.campaign_id)+'/results')
            print('deleted results')
        if exists('simics-workspace/injected-checkpoints/' +
                  str(options.campaign_id)):
            rmtree('simics-workspace/injected-checkpoints/' +
                   str(options.campaign_id))
            print('deleted injected checkpoints')
        if db:
            with db:
                db.delete_results()
            print('flushed database')
    elif options.delete in ('campaign', 'c'):
        print('deleting campaign', options.campaign_id)
        if exists('campaign-data/'+str(options.campaign_id)):
            rmtree('campaign-data/'+str(options.campaign_id))
            print('deleted campaign data')
        if exists('simics-workspace/gold-checkpoints/' +
                  str(options.campaign_id)):
            rmtree('simics-workspace/gold-checkpoints/' +
                   str(options.campaign_id))
            print('deleted gold checkpoints')
        if exists('simics-workspace/injected-checkpoints/' +
                  str(options.campaign_id)):
            rmtree('simics-workspace/injected-checkpoints/' +
                   str(options.campaign_id))
            print('deleted injected checkpoints')
        if db:
            with db:
                db.delete_campaign()
                print('deleted campaign '+str(options.campaign_id) +
                      ' from database')
    elif options.delete in ('all', 'a'):
        print('deleting all campaigns, files, and database')
        if exists('simics-workspace/gold-checkpoints'):
            rmtree('simics-workspace/gold-checkpoints')
            print('deleted gold checkpoints')
        if exists('simics-workspace/injected-checkpoints'):
            rmtree('simics-workspace/injected-checkpoints')
            print('deleted injected checkpoints')
        if exists('campaign-data'):
            rmtree('campaign-data')
            print('deleted campaign data')
        if db:
            db.delete_database(options.delete_user)
            print('deleted database')
        if exists('log/migrations'):
            rmtree('log/migrations')
            print('deleted django migrations')


def create_campaign(options):
    if options.directory == 'fiapps':
        if not exists('fiapps'):
            check_call(['git', 'clone',
                        'git@gitlab.hcs.ufl.edu:F4/fiapps.git'])
        check_call(['make', options.application],
                   cwd=join(getcwd(), 'fiapps'))
    else:
        if not exists(options.directory):
            raise Exception('cannot find directory '+options.directory)
    if options.simics and not exists('simics-workspace'):
        mkdir('simics-workspace')
        dirs = listdir('/opt/simics/simics-4.8')
        simics_dirs = []
        for simics_dir in dirs:
            if simics_dir.startswith('simics-4.8.'):
                simics_dirs.append((simics_dir, int(simics_dir.split('.')[-1])))
        simics_dirs.sort(key=lambda x: x[1])
        check_call('/opt/simics/simics-4.8/'+simics_dirs[-1][0] +
                   '/bin/workspace-setup',
                   cwd=join(getcwd(), 'simics-workspace'))
        check_call(['git', 'clone',
                    'git@gitlab.hcs.ufl.edu:F4/simics-p2020rdb'],
                   cwd=join(getcwd(), 'simics-workspace'))
        check_call(['git', 'clone',
                    'git@gitlab.hcs.ufl.edu:F4/simics-a9x2'],
                   cwd=join(getcwd(), 'simics-workspace'))
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
        'aux_output_file': options.aux and options.aux_output_file,
        'command': options.application+((' '+options.arguments)
                                        if options.arguments else ''),
        'debugger_output': '',
        'description': options.description,
        'dut_output': '',
        'kill_dut': options.kill_dut,
        'output_file': options.output_file,
        'rsakey': rsakey,
        'simics': options.simics,
        'timestamp': None}
    if options.aux_application is None:
        options.aux_application = options.application
    with database(options, initialize=True) as db:
        db.insert('campaign', campaign)
    campaign_directory = 'campaign-data/'+str(campaign['id'])
    if exists(campaign_directory):
        raise Exception('directory already exists: '
                        'campaign-data/'+str(campaign['id']))
    options.debug = True
    drseus = fault_injector(campaign, options)
    drseus.setup_campaign()
    print('campaign created')


def inject_campaign(options):
    campaign = get_campaign(options)

    def perform_injections(iteration_counter, switch):
        drseus = fault_injector(campaign, options, switch)
        try:
            drseus.inject_campaign(iteration_counter)
        except KeyboardInterrupt:
            with drseus.db as db:
                db.log_event('Information', 'User', 'Interrupted',
                             db.log_exception)
            drseus.debugger.close()
            drseus.db.result.update({'outcome_category': 'Incomplete',
                                     'outcome': 'Interrupted'})
            with drseus.db as db:
                db.log_result(False)
        except:
            print_exc()
            with drseus.db as db:
                db.log_event('Error', 'DrSEUs', 'Exception', db.log_exception)
            drseus.debugger.close()
            drseus.db.result.update({'outcome_category': 'Incomplete',
                                     'outcome': 'Uncaught exception'})
            with drseus.db as db:
                db.log_result(False)
            if options.processes == 1 and options.debug:
                print('dropping into python debugger')
                try:
                    set_trace()
                except BdbQuit:
                    pass

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
    campaign = get_campaign(options)
    if not campaign['simics']:
        raise Exception('this feature is only available for Simics campaigns')
    with database(options) as db:
        db.result['id'] = options.result_id
        injections = db.get_item('injection')
    drseus = fault_injector(campaign, options)
    checkpoint = drseus.debugger.regenerate_checkpoints(injections)
    drseus.debugger.launch_simics_gui(checkpoint)
    rmtree('simics-workspace/injected-checkpoints/'+str(campaign['id']) +
           '/'+str(options.result_id))


def view_log(options):
    initialize_django(options)
    django_command([argv[0], 'runserver', ('0.0.0.0:' if options.external
                                           else '')+str(options.port)])


def run_django_command(options):
    initialize_django(options)
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


# def merge_campaigns(options):
#     with database() as db, database(campaign={'id': '*'},
#                                     database_file=options.directory +
#                                     '/campaign-data/db.sqlite3') as db_new:
#         for new_campaign in db_new.get_campaign():
#             print('merging campaign: \"'+options.directory+'/' +
#                   new_campaign['command']+'\"')
#             db_new.campaign['id'] = new_campaign['id']
#             db.insert('campaign', new_campaign)
#             if exists(options.directory+'/campaign-data/' +
#                       str(db_new.campaign['id'])):
#                 print('\tcopying campaign data...', end='')
#                 copytree(options.directory+'/campaign-data/' +
#                          str(db_new.campaign['id']),
#                          'campaign-data/'+str(new_campaign['id']))
#                 print('done')
#             if exists(options.directory +
#                       '/simics-workspace/gold-checkpoints/' +
#                       str(db_new.campaign['id'])):
#                 print('\tcopying gold checkpoints...', end='')
#                 copytree(options.directory+'/simics-workspace/'
#                          'gold-checkpoints/'+str(db_new.campaign['id']),
#                          'simics-workspace/gold-checkpoints/' +
#                          str(new_campaign['id']))
#                 print('done')
#                 print('\tupdating checkpoint dependency paths...', end='')
#                 stdout.flush()
#                 __update_checkpoint_dependencies(new_campaign['id'])
#                 print('done')
#             print('\tcopying results...', end='')
#             for new_result in db_new.get_result():
#                 db_new.result['id'] = new_result['id']
#                 db.insert('result', new_result)
#                 for table in ['injection', 'simics_register_diff',
#                               'simics_memory_diff']:
#                     for new_item in db_new.get_item(table):
#                         new_item['result_id'] = new_result['id']
#                         db.insert(table, new_item)
#             print('done')


def launch_openocd(options):
    debugger = openocd(None, options)
    print('Launched '+str(debugger)+'\n')
    try:
        debugger.openocd.wait()
    except KeyboardInterrupt:
        debugger.openocd.kill()


def launch_supervisor(options):
    supervisor(get_campaign(options), options).cmdloop()


def backup(options):

    def traverse_directory(directory, archive=None, progress=None):
        num_items = 0
        for item in listdir(directory):
            if isdir(directory+'/'+item):
                num_items += traverse_directory(directory+'/'+item, archive,
                                                progress)
            else:
                num_items += 1
                if archive is not None:
                    try:
                        archive.add(directory+'/'+item)
                    except FileNotFoundError:
                        pass
                if progress is not None:
                    progress[0] += 1
                    progress[1].update(progress[0])
        return num_items

# def backup(options):
    if not exists('backups'):
        mkdir('backups')
    sql_backup = 'campaign-data/'+options.db_name+'.sql'
    print('dumping database...')
    database(options).backup_database(sql_backup)
    print('database dumped')
    if options.files:
        backup_name = ('backups/' +
                       '-'.join([str(unit).zfill(2)
                                 for unit in datetime.now().timetuple()[:3]]) +
                       '_' +
                       '-'.join([str(unit).zfill(2)
                                 for unit in datetime.now().timetuple()[3:6]]))
        num_items = 0
        directories = ('campaign-data', 'simics-workspace/gold-checkpoints')
        print('discovering files to archive')
        for directory in directories:
            num_items += traverse_directory(directory)
        print('archiving files...')
        with open_tar(backup_name+'.tar.gz', 'w:gz') \
            as backup, ProgressBar(max_value=num_items, widgets=[
                Percentage(), ' (',
                SimpleProgress(format='%(value)d/%(max_value)d'), ') ', Bar(),
                ' ', Timer()]) as progress_bar:
            progress = [0, progress_bar]
            for directory in directories:
                traverse_directory(directory, backup, progress)
        remove(sql_backup)
        print('backup complete')


def restore(options):
    if options.files and options.backup_file is None:
        raise Exception('no backup file specified')
    if options.files:
        if exists('campaign-data') or \
                exists('simics-workspace/gold-checkpoints'):
            if input('existing data will be deleted before restore '
                     'operation, continue? [Y/n]: ') in ('n', 'N'):
                return
            if exists('campaign-data'):
                rmtree('campaign-data')
            if exists('simics-workspace/gold-checkpoints'):
                rmtree('simics-workspace/gold-checkpoints')
        print('restoring files...', end='')
        stdout.flush()
        with open_tar(options.backup_file, 'r:gz') as backup:
            backup.extractall()
        print('done')
    for item in listdir('campaign-data'):
        if '.sql' in item:
            print('restoring database...')
            database(options, initialize=True).restore_database(
                'campaign-data/'+item)
            print('database restored')
            break
    else:
        print('could not find .sql file to restore')


def clean(options):
    if exists('backups'):
        rmtree('backups')
        print('deleted database backup(s)')
    if exists('simics-workspace/injected-checkpoints'):
        rmtree('simics-workspace/injected-checkpoints')
        print('deleted injected checkpoints')
    if options.power_log and exists('power_switch_log.txt'):
        remove('power_switch_log.txt')
