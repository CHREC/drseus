from copy import copy
from datetime import datetime
from django.core.management import execute_from_command_line as django_command
from django.db import connection
from json import dump, load
from multiprocessing import Process, Value
from os import getcwd, listdir, mkdir, remove, walk
from os.path import abspath, dirname, exists, isdir, join
from progressbar import ProgressBar
from progressbar.widgets import Bar, Percentage, SimpleProgress, Timer
from shutil import rmtree
from subprocess import call, check_call
from sys import argv, stdout
from tarfile import open as open_tar
from terminaltables import AsciiTable
from time import sleep
from traceback import print_exc

from .database import (backup_database, delete_database, get_campaign,
                       new_campaign, restore_database)
from .fault_injector import fault_injector
from .jtag import find_devices
from .jtag.openocd import openocd
from .power_switch import power_switch
from .simics.config import simics_config
from .supervisor import supervisor


def detect_power_switch_devices(options):
    detect_devices(options, use_power_switch=True)


def detect_devices(options, use_power_switch=False):
    def detect_new_devices(preexisting_devices):
        connected_devices = find_devices()
        if 'uart' in preexisting_devices:
            preexiting_uart_serials = [
                preexisting_devices['uart'][dev]['serial'] for
                dev in preexisting_devices['uart']
                if 'serial' in preexisting_devices['uart'][dev]]
        else:
            preexiting_uart_serials = []
        new_devices = {}
        if 'jtag' in connected_devices:
            for dev in connected_devices['jtag']:
                if 'jtag' not in preexisting_devices or \
                        dev not in preexisting_devices['jtag']:
                    if 'jtag' not in new_devices:
                        new_devices['jtag'] = {}
                    new_devices['jtag'][dev] = connected_devices['jtag'][dev]
        if 'uart' in connected_devices:
            for dev in connected_devices['uart']:
                if 'serial' in connected_devices['uart'][dev] and \
                        connected_devices['uart'][dev]['serial'] not in \
                        preexiting_uart_serials:
                    if 'uart' not in new_devices:
                        new_devices['uart'] = {}
                    new_devices['uart'][dev] = connected_devices['uart'][dev]
        return new_devices

    if exists('devices.json'):
        with open('devices.json', 'r') as device_file:
            devices = load(device_file)
    else:
        devices = []
    if use_power_switch:
        with power_switch(options) as ps:
            status = ps.get_status()
            outlets = iter(ps.outlets)
            ps.set_outlet('all', 'off', 1)
    else:
        input(
            'ensure all devices to assosciate are disconnected and press enter')
    while True:
        preexisting_devices = find_devices()
        if use_power_switch:
            try:
                outlet = next(outlets)
            except:
                break
            else:
                with power_switch(options) as ps:
                    ps.set_outlet(outlet, 'on')
                    new_devices = detect_new_devices(preexisting_devices)
                    ps.set_outlet(outlet, 'off', 1)
        else:
            outlet = None
            input('connect a new device and press enter')
            sleep(5)
            new_devices = detect_new_devices(preexisting_devices)
        if not len(new_devices) or 'uart' not in new_devices:
            print('no devices detected on outlet', outlet)
        else:
            for dev_type in new_devices:
                if len(new_devices[dev_type]) > 1:
                    print('too many devices detected{}'.format(
                        ' on outlet {}'.format(outlet)
                        if use_power_switch else ''))
                    break
            else:
                new_device = new_devices['uart'].popitem()[1]
                new_device['outlet'] = outlet
                if 'serial' not in new_device:
                    print('unsupported device does not have a serial number')
                    continue
                else:
                    new_device['uart'] = new_device.pop('serial')
                if 'jtag' in new_devices:
                    new_device['jtag'] = new_devices['jtag'].popitem()[0]
                devices = [dev for dev in devices if dev['outlet'] != outlet]
                devices = [dev for dev in devices
                           if dev['uart'] != new_device['uart']]
                devices.append(new_device)
                print('added {} device{}'.format(
                    new_device['type'],
                    ' on outlet {}'.format(outlet) if use_power_switch else ''))
        if not use_power_switch and \
                input('continue detecting devices? [Y/n]: ') in ('N', 'n'):
            break
    if use_power_switch:
        for outlet in status:
            ps.set_outlet(outlet['outlet'], outlet['status'], 1)
    with open('devices.json', 'w') as device_file:
        dump(devices, device_file, indent=4)
    print('saved device information to "devices.json"')


def list_devices(none=None, only_uart=False):
    devices = find_devices()
    for dev_type in sorted(devices.keys()):
        print(dev_type, 'devices:')
        for dev in sorted(devices[dev_type].keys()):
            print('\t{} - {}type: {}'.format(
                dev,
                'serial: {}, '.format(devices[dev_type][dev]['serial'])
                if 'serial' in devices[dev_type][dev] else '',
                devices[dev_type][dev]['type']))


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
                ['y', 'Y', 'yes', 'Yes', 'YES']:
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
        connection.close()
        delete_database(options)
        print('deleted database')
        if exists('src/log/migrations'):
            rmtree('src/log/migrations')
            print('deleted django migrations')


def create_campaign(options):
    if not exists(options.directory):
        raise Exception('cannot find directory {}'.format(
            options.directory))
    for file_ in options.files + options.aux_files:
        # TODO: check for makefile
        try:
            check_call(['make', file_],
                       cwd=join(getcwd(), options.directory))
        except:
            if not exists(join(options.directory, file_)):
                raise Exception('could not find file "{}"'.format(
                    join(options.directory, file_)))
    if options.simics and not exists('simics-workspace'):
        raise Exception('cannot find simics-workspace, '
                        'trying running "scripts/setup_environment.sh"')
    campaign = new_campaign(options)
    options.campaign_id = campaign.id
    campaign_directory = 'campaign-data/{}'.format(campaign.id)
    if exists(campaign_directory):
        raise Exception('directory already exists: {}'.format(
            campaign_directory))
    drseus = fault_injector(options)
    try:
        drseus.setup_campaign()
    except:
        print_exc()
        print('failed to create campaign')
        drseus.db.log_event(
            'Error', 'DrSEUs', 'Exception', drseus.db.log_exception)
        if drseus.db.campaign.simics:
            drseus.debugger.continue_dut()
        drseus.debugger.dut.write('\x03')
        if drseus.db.campaign.aux:
            drseus.debugger.aux.write('\x03')
        drseus.debugger.close()
        return -1
    else:
        print('created campaign {}'.format(campaign.id))


def inject_campaign(options):
    campaign = get_campaign(options)
    architecture = campaign.architecture
    simics = campaign.simics

    def perform_injections(iteration_counter, switch):
        drseus = fault_injector(options, switch)
        drseus.inject_campaign(iteration_counter)

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
            uarts = find_devices()['uart']
            dev_type = uarts[options.dut_serial_port]['type']
            uarts = [dev for dev in uarts
                     if uarts[dev]['type'] == dev_type]
        processes = []
        for i in range(options.processes):
            if not simics and \
                    architecture == 'a9':
                if i < len(uarts):
                    options = copy(options)
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
    injections = campaign.result_set.get(
        id=options.result_id).injection_set.all()
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
    debugger = openocd(None, options, None)
    print('Launched {}\n'.format(debugger))
    try:
        debugger.openocd.wait()
    except KeyboardInterrupt:
        debugger.openocd.kill()


def launch_supervisor(options):
    supervisor(options).cmdloop()


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
                     'operation, continue? [Y/n]: ') in ('n', 'N', 'no', 'No',
                                                         'NO'):
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
            remove(join('campaign-data', item))
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
    capture = 'minicom_capture.{}_{}'.format(
        '-'.join(['{:02}'.format(unit)
                  for unit in datetime.now().timetuple()[:3]]),
        '-'.join(['{:02}'.format(unit)
                  for unit in datetime.now().timetuple()[3:6]]))
    call(['minicom', '-D', options.dut_serial_port,
          '--capturefile={}'.format(capture)])
    if exists(capture):
        with open(capture, 'r') as capture_file:
            drseus.db.result.dut_output += capture_file.read()
            drseus.db.save()
        remove(capture)
        drseus.db.result.outcome_category = 'Minicom capture'
        drseus.db.result.outcome = ''
        drseus.close()
    else:
        drseus.close(log=False)
