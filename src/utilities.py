from datetime import datetime
from django.core.management import execute_from_command_line as django_command
from django.db import connection
from json import dump, load
from multiprocessing import Process, Value
from os import getcwd, listdir, mkdir, remove, walk
from os.path import abspath, dirname, exists, isdir, join
from pdb import set_trace
from progressbar import ProgressBar
from progressbar.widgets import Bar, Percentage, SimpleProgress, Timer
from shutil import rmtree
from subprocess import call, check_call
from sys import argv, stdout
from tarfile import open as open_tar
from terminaltables import AsciiTable
from traceback import print_exc

from .database import (backup_database, delete_database, get_campaign,
                       new_campaign, restore_database)
from .fault_injector import fault_injector
from .jtag import (find_all_uarts, find_p2020_uarts, find_zedboard_jtag_serials,
                   find_zedboard_uart_serials)
from .jtag.openocd import openocd
from .power_switch import power_switch
from .simics.config import simics_config
from .supervisor import supervisor


def detect_power_switch_devices(options):
    if exists('devices.json'):
        with open('devices.json', 'r') as device_file:
            devices = load(device_file)
    else:
        devices = []
    uarts = [device['uart'] for device in devices]
    with power_switch(options) as ps:
        status = ps.get_status()
        ps.set_outlet('all', 'off', 1)
        ftdi_serials_pre = find_zedboard_jtag_serials()
        uart_serials_pre = find_zedboard_uart_serials().values()
        for outlet in ps.outlets:
            ps.set_outlet(outlet, 'on', 5)
            ftdi_serials = [serial for serial in find_zedboard_jtag_serials()
                            if serial not in ftdi_serials_pre]
            uart_serials = [serial for serial
                            in find_zedboard_uart_serials().values()
                            if serial not in uart_serials_pre]
            ps.set_outlet(outlet, 'off', 1)
            if len(ftdi_serials) > 1 or len(uart_serials) > 1:
                print('too many devices detected on outlet', outlet)
                continue
            if not len(ftdi_serials) or not len(uart_serials):
                print('no devices detected on outlet', outlet)
                continue
            print('found zedboard on outlet', outlet)
            if uart_serials[0] in uarts:
                print('device already in "devices.json"')
            else:
                devices.append({'outlet': outlet,
                                'ftdi': ftdi_serials[0],
                                'uart': uart_serials[0]})
        for outlet in status:
            ps.set_outlet(outlet['outlet'], outlet['status'], 1)
    with open('devices.json', 'w') as device_file:
        dump(devices, device_file, indent=4)
    print('saved device information to "devices.json"')


def detect_devices(options):
    if exists('devices.json'):
        with open('devices.json', 'r') as device_file:
            devices = load(device_file)
    else:
        devices = []
    uarts = [device['uart'] for device in devices]
    while True:
        ftdi_serials = find_zedboard_jtag_serials()
        uart_serials = find_zedboard_uart_serials().values()
        if len(ftdi_serials) > 1 or len(uart_serials) > 1:
            print('too many devices detected, disconnect all but one device')
        elif not len(ftdi_serials) or not len(uart_serials):
            print('no devices detected')
        else:
            print('found zedboard')
            if uart_serials[0] in uarts:
                print('device already in "devices.json"')
            else:
                devices.append({'ftdi': ftdi_serials[0],
                                'uart': uart_serials[0]})
        if input('continue detecting devices? [Y/n]') in ('N', 'n'):
            break
        else:
            input('press enter after connecting next device')
    with open('devices.json', 'w') as device_file:
        dump(devices, device_file, indent=4)
    print('saved device information to "devices.json"')


def list_devices(none=None, only_uart=False):
    zedboard_jtags = find_zedboard_jtag_serials() if not only_uart else []
    if zedboard_jtags:
        print('ZedBoard JTAG serial numbers: ')
        for serial in zedboard_jtags:
            print('\t{}'.format(serial))
    zedboard_uarts = find_zedboard_uart_serials()
    if zedboard_uarts:
        print('ZedBoard UART serial numbers:')
        for uart, serial in sorted(zedboard_uarts.items()):
            print('\t{}: {}'.format(uart, serial))
    p2020_uarts = find_p2020_uarts()
    if p2020_uarts:
        print('P2020 UART devices:')
        for serial in p2020_uarts:
            print('\t{}'.format(serial))
    other_uarts = [uart for uart in find_all_uarts()
                   if uart not in zedboard_uarts and uart not in p2020_uarts]
    if other_uarts:
        print('Other UART devices:')
        for serial in other_uarts:
            print('\t{}'.format(serial))


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
    table = AsciiTable([['ID', 'Results', 'Command', 'Arch', 'Simics']],
                       'DrSEUs Campaigns')
    try:
        campaigns = list(get_campaign('all'))
    except:
        print('error connecting to database, try creating a new campaign first')
        return
    for campaign in campaigns:
        results = campaign.result_set.count()
        items = []
        for i, item in enumerate((campaign.id, results, campaign.command,
                                  campaign.architecture, campaign.simics)):
            if not isinstance(item, str):
                item = str(item)
            if len(item) < table.column_max_width(i):
                items.append(item)
            else:
                items.append('{}...'.format(
                    item[:table.column_max_width(i)-4]))
        table.table_data.append(items)
    print(table.table)


def delete(options):
    try:
        campaign = get_campaign(options)
    except:
        campaign = None
    if options.selection in ('results', 'r'):
        if input('are you sure you want to delete all results for campaign {}?'
                 ' [y/N]: '.format(options.campaign_id)) not in \
                ['y', 'Y', 'yes']:
            return
        if exists('campaign-data/{}/results'.format(options.campaign_id)):
            rmtree('campaign-data/{}/results'.format(options.campaign_id))
            print('deleted results')
        if exists('simics-workspace/injected-checkpoints/{}'.format(
                options.campaign_id)):
            rmtree('simics-workspace/injected-checkpoints/{}'.format(
                options.campaign_id))
            print('deleted injected checkpoints')
        if campaign is not None:
            campaign.result_set.all().delete()
            print('deleted campaign {} results from database'.format(
                options.campaign_id))
    elif options.selection in ('campaign', 'c'):
        if input('are you sure you want to delete campaign {}? [y/N]: '.format(
                options.campaign_id)) not in ['y', 'Y', 'yes']:
            return
        if exists('campaign-data/{}'.format(options.campaign_id)):
            rmtree('campaign-data/{}'.format(options.campaign_id))
            print('deleted campaign data')
        if exists('simics-workspace/gold-checkpoints/{}'.format(
                options.campaign_id)):
            rmtree('simics-workspace/gold-checkpoints/{}'.format(
                options.campaign_id))
            print('deleted gold checkpoints')
        if exists('simics-workspace/injected-checkpoints/{}'.format(
                options.campaign_id)):
            rmtree('simics-workspace/injected-checkpoints/{}'.format(
                options.campaign_id))
            print('deleted injected checkpoints')
        if campaign is not None:
            campaign.delete()
            print('deleted campaign {} from database'.format(
                options.campaign_id))
    elif options.selection in ('all', 'a'):
        if input('are you sure you want to delete all campaigns, files, and '
                 'database? [y/N]: ') not in ['y', 'Y', 'yes']:
            return
        if exists('simics-workspace/gold-checkpoints'):
            rmtree('simics-workspace/gold-checkpoints')
            print('deleted gold checkpoints')
        if exists('simics-workspace/injected-checkpoints'):
            rmtree('simics-workspace/injected-checkpoints')
            print('deleted injected checkpoints')
        if exists('campaign-data'):
            rmtree('campaign-data')
            print('deleted campaign data')
        delete_database(options)
        print('deleted database')
        if exists('log/migrations'):
            rmtree('log/migrations')
            print('deleted django migrations')


def create_campaign(options):
    if options.directory == 'fiapps':
        if not exists('fiapps'):
            check_call(['git', 'clone',
                        'git@gitlab.hcs.ufl.edu:F4/fiapps.git'])
        if options.application_file:
            try:
                check_call(['make', options.application],
                           cwd=join(getcwd(), 'fiapps'))
            except Exception as error:
                if not exists(options.application):
                    raise error
    else:
        if not exists(options.directory):
            raise Exception('cannot find directory {}'.format(
                options.directory))
    if options.simics and not exists('simics-workspace'):
        mkdir('simics-workspace')
        dirs = listdir('/opt/simics/simics-4.8')
        simics_dirs = []
        for simics_dir in dirs:
            if simics_dir.startswith('simics-4.8.'):
                simics_dirs.append((simics_dir, int(simics_dir.split('.')[-1])))
        simics_dirs.sort(key=lambda x: x[1])
        cwd = join(getcwd(), 'simics-workspace')
        check_call('/opt/simics/simics-4.8/{}//bin/workspace-setup'.format(
            simics_dirs[-1][0]), cwd=cwd)
        check_call(['git', 'clone',
                    'git@gitlab.hcs.ufl.edu:F4/simics-p2020rdb'], cwd=cwd)
        check_call(['git', 'clone',
                    'git@gitlab.hcs.ufl.edu:F4/simics-a9x2'], cwd=cwd)
    options.campaign = new_campaign(options)
    if options.aux_application is None:
        options.aux_application = options.application
    campaign_directory = 'campaign-data/{}'.format(options.campaign.id)
    if exists(campaign_directory):
        raise Exception('directory already exists: campaign-data/{}'.format(
            options.campaign.id))
    drseus = fault_injector(options)
    drseus.setup_campaign()
    print('created campaign {}'.format(options.campaign.id))


def inject_campaign(options):
    campaign = get_campaign(options)
    architecture = campaign.architecture
    simics = campaign.simics

    def perform_injections(iteration_counter, switch):
        drseus = fault_injector(options, switch)
        try:
            drseus.inject_campaign(iteration_counter)
        except KeyboardInterrupt:
            drseus.db.log_event(
                'Information', 'User', 'Interrupted', drseus.db.log_exception)
            drseus.debugger.close()
            drseus.db.result.outcome_category = 'Incomplete'
            drseus.db.result.outcome = 'Interrupted'
            drseus.db.log_result(exit=True)
        except:
            print_exc()
            drseus.db.log_event(
                'Error', 'DrSEUs', 'Exception', drseus.db.log_exception)
            drseus.debugger.close()
            drseus.db.result.outcome_category = 'Incomplete'
            drseus.db.result.outcome = 'Uncaught exception'
            drseus.db.log_result(exit=True)
            if options.processes == 1 and options.debug:
                print('dropping into python debugger')
                set_trace()

# def inject_campaign(options):
    if options.iterations is not None:
        iteration_counter = Value('L', options.iterations)
    else:
        iteration_counter = None
    if not simics and architecture == 'a9' \
            and options.power_switch_ip_address:
        switch = power_switch(options)
    else:
        switch = None
    if options.processes > 1 and (simics or
                                  architecture == 'a9'):
        connection.close()
        if not simics and \
                architecture == 'a9':
            uarts = list(find_zedboard_uart_serials().keys())
        processes = []
        for i in range(options.processes):
            if not simics and \
                    architecture == 'a9':
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
    if not campaign.simics:
        raise Exception('this feature is only available for Simics campaigns')
    injections = campaign.result_set.get(id=options.result_id).injection_set
    drseus = fault_injector(options)
    checkpoint = drseus.debugger.regenerate_checkpoints(injections)
    drseus.debugger.launch_simics_gui(checkpoint)
    rmtree('simics-workspace/injected-checkpoints/{}/{}'.format(
        campaign.id, options.result_id))


def view_log(options):
    django_command([argv[0], 'runserver', ('0.0.0.0:' if options.external
                                           else '')+str(options.port)])


def run_django_command(options):
    command = [argv[0]+' '+options.command]
    for item in options.django_command:
        command.append(item)
    django_command(command)


def update_dependencies(*args):

    def update_checkpoint_dependencies(campaign_id):
        for checkpoint in listdir('simics-workspace/gold-checkpoints/{}'.format(
                campaign_id)):
            with simics_config('simics-workspace/gold-checkpoints/{}/{}'.format(
                    campaign_id, checkpoint)) as config:
                paths = config.get(config, 'sim', 'checkpoint_path')
                new_paths = []
                for path in paths:
                    path_list = path.split('/')
                    path_list = path_list[path_list.index('simics-workspace'):]
                    path_list[-2] = str(campaign_id)
                    new_paths.append('"{}/{}'.format(getcwd(),
                                                     '/'.join(path_list)))
                config.set(config, 'sim', 'checkpoint_path', new_paths)
                config.save()

    if exists('simics-workspace/gold-checkpoints'):
        print('updating gold checkpoint path dependencies...', end='')
        stdout.flush()
        for campaign in listdir('simics-workspace/gold-checkpoints'):
            update_checkpoint_dependencies(campaign)
        print('done')


def launch_openocd(options):
    debugger = openocd(None, options)
    print('Launched {}\n'.format(debugger))
    try:
        debugger.openocd.wait()
    except KeyboardInterrupt:
        debugger.openocd.kill()


def launch_supervisor(options):
    drseus = supervisor(get_campaign(options), options)
    try:
        drseus.cmdloop()
    except:
        print_exc()
        with drseus.drseus.db as db:
            db.log_event('Error', 'DrSEUs', 'Exception', db.log_exception)
        drseus.drseus.debugger.close()
        drseus.drseus.db.result.update({'outcome_category': 'Incomplete',
                                        'outcome': 'Uncaught exception'})
        with drseus.drseus.db as db:
            db.log_result(exit=True)


def backup(options):

    def traverse_directory(directory, archive=None, progress=None):
        num_items = 0
        for item in listdir(directory):
            if isdir(join(directory, item)):
                num_items += traverse_directory(join(directory, item), archive,
                                                progress)
            else:
                num_items += 1
                if archive is not None:
                    try:
                        archive.add(join(directory, item))
                    except FileNotFoundError:
                        pass
                if progress is not None:
                    progress[0] += 1
                    progress[1].update(progress[0])
        return num_items

# def backup(options):
    if not exists('backups'):
        mkdir('backups')
    if not exists('campaign-data'):
        mkdir('campaign-data')
    sql_backup = 'campaign-data/{}.sql'.format(options.db_name)
    print('dumping database...')
    backup_database(options, sql_backup)
    print('database dumped')
    if options.files:
        backup_name = 'backups/{}_{}'.format(
            '-'.join(['{:02}'.format(unit)
                      for unit in datetime.now().timetuple()[:3]]),
            '-'.join(['{:02}'.format(unit)
                      for unit in datetime.now().timetuple()[3:6]]))
        num_items = 0
        directories = ['campaign-data']
        if exists('simics-workspace/gold-checkpoints'):
            directories.append('simics-workspace/gold-checkpoints')
        print('discovering files to archive')
        for directory in directories:
            num_items += traverse_directory(directory)
        print('archiving files...')
        with open_tar('{}.tar.gz'.format(backup_name), 'w:gz') \
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
            print('restoring database from {}...'.format(item))
            restore_database(options, join('campaign-data', item))
            print('database restored')
            break
    else:
        print('could not find .sql file to restore')


def clean(options):
    found_cache = False
    for root, dirs, files in walk(dirname(abspath(__file__))):
        for dir_ in dirs:
            if dir_ == '__pycache__':
                rmtree(join(root, dir_))
                found_cache = True
            elif dir_ == 'migrations' and (options.all or options.migrations):
                rmtree(join(root, dir_))
                print('deleted django migrations')
        for file_ in files:
            if file_ == 'lextab.py':
                remove(join(root, file_))
                print('deleted lextab.py')
            elif file_ == 'parsetab.py':
                remove(join(root, file_))
                print('deleted parsetab.py')
    if found_cache:
        print('deleted __pycache__ directories')
    if exists('simics-workspace/injected-checkpoints'):
        rmtree('simics-workspace/injected-checkpoints')
        print('deleted injected checkpoints')
    if exists('backups') and (options.all or options.backups):
        rmtree('backups')
        print('deleted backups')
    if exists('power_switch_log.txt') and (options.all or options.power_log):
        remove('power_switch_log.txt')


def launch_minicom(options):
    options.debug = False
    options.jtag = False
    campaign = get_campaign(options)
    drseus = fault_injector(options)
    if campaign.simics:
        checkpoint = 'gold-checkpoints/{}/{}'.format(
            drseus.db.campaign.id, drseus.db.campaign.checkpoints)
        if exists('simics-workspace/{}_merged'.format(checkpoint)):
            drseus.debugger.launch_simics('{}_merged'.format(checkpoint))
        else:
            drseus.debugger.launch_simics(checkpoint)
        drseus.debugger.continue_dut()
    drseus.debugger.dut.close()
    call(['minicom', '-D', options.dut_serial_port])
    drseus.close(log=False)
