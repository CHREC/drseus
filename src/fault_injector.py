from difflib import SequenceMatcher
from os import listdir, makedirs
from shutil import rmtree
from threading import Thread
from time import perf_counter

from .database import database
from .error import DrSEUsError
from .jtag.bdi import bdi
from .jtag.dummy import dummy
from .jtag.openocd import openocd
from .simics import simics


class fault_injector(object):
    def __init__(self, campaign, options, power_switch=None):
        self.options = options
        self.db = database(options, campaign, options.command != 'new')
        if campaign['simics'] and campaign['architecture'] in ['a9', 'p2020']:
            self.debugger = simics(self.db, options)
        elif options.jtag and campaign['architecture'] == 'a9':
            self.debugger = openocd(self.db, options, power_switch)
        elif options.jtag and campaign['architecture'] == 'p2020':
            self.debugger = bdi(self.db, options)
        else:
            self.debugger = dummy(self.db, options, power_switch)
        if campaign['aux'] and not campaign['simics']:
            self.debugger.aux.write('\x03')
            self.debugger.aux.do_login()

    def __str__(self):
        string = ('DrSEUs Attributes:\n\tDebugger: '+str(self.debugger) +
                  '\n\tDUT:\t'+str(self.debugger.dut).replace('\n\t', '\n\t\t'))
        if self.db.campaign['aux']:
            string += '\n\tAUX:\t'+str(self.debugger.aux).replace('\n\t',
                                                                  '\n\t\t')
        string += ('\n\tCampaign Information:\n\t\tCampaign Number: ' +
                   str(self.db.campaign['id'])+'\n\t\t')

        if self.db.campaign['command']:
            string += ('DUT Command: \"'+self.db.campaign['command']+'\"')
            if self.db.campaign['aux']:
                string += \
                    '\n\t\tAUX Command: \"'+self.db.campaign['aux_command']+'\"'
            string += ('\n\t\t'+'Execution Time: ' +
                       str(self.db.campaign['execution_time'])+' seconds')
            if self.db.campaign['simics']:
                string += ('\n\t\tExecution Cycles: ' +
                           '{:,}'.format(self.db.campaign['cycles']) +
                           ' cycles\n')
        return string

    def close(self, log=True):
        self.debugger.close()
        if log and self.db.result:
            with self.db as db:
                result_items = db.get_count('event')
                result_items += db.get_count('injection')
                result_items += db.get_count('simics_memory_diff')
                result_items += db.get_count('simics_register_diff')
            if log and (self.db.result['dut_output'] or
                        self.db.result['aux_output'] or
                        self.db.result['debugger_output'] or
                        result_items):
                self.db.result['outcome_category'] = 'DrSEUs'
                if self.options.command == 'supervise':
                    self.db.result['outcome'] = 'Supervisor'
                else:
                    self.db.result['outcome'] = 'Exited'
                with self.db as db:
                    db.log_result(
                        supervisor=self.options.command == 'supervise',
                        exit=True)
            else:
                with self.db as db:
                    db.delete_result()

    def setup_campaign(self):
        if self.db.campaign['command'] or self.db.campaign['simics']:
            if self.db.campaign['simics']:
                self.debugger.launch_simics()
            self.debugger.reset_dut()
            self.debugger.time_application()
            if self.db.campaign['output_file']:
                if self.db.campaign['aux_output_file']:
                    self.debugger.aux.get_file(
                        self.db.campaign['output_file'],
                        'campaign-data/'+str(self.db.campaign['id'])+'/gold_' +
                        self.db.campaign['output_file'])
                    self.debugger.aux.command('rm ' +
                                              self.db.campaign['output_file'])
                else:
                    self.debugger.dut.get_file(
                        self.db.campaign['output_file'],
                        'campaign-data/'+str(self.db.campaign['id'])+'/gold_' +
                        self.db.campaign['output_file'])
                    self.debugger.dut.command('rm ' +
                                              self.db.campaign['output_file'])
            with self.db as db:
                db.update('campaign')
        self.close()

    def __monitor_execution(self, latent_faults=0, persistent_faults=False,
                            log_time=False):

        def check_output():
            local_diff = \
                hasattr(self.options, 'local_diff') and self.options.local_diff
            try:
                if self.db.campaign['aux_output_file']:
                    directory_listing = self.debugger.aux.command('ls -l')[0]
                else:
                    directory_listing = self.debugger.dut.command('ls -l')[0]
            except DrSEUsError as error:
                self.db.result['outcome_category'] = 'Post execution error'
                self.db.result['outcome'] = error.type
                return
            if local_diff:
                directory_listing = directory_listing.replace(
                    'gold_'+self.db.campaign['output_file'], '')
            if self.db.campaign['output_file'] not in directory_listing:
                self.db.result['outcome_category'] = 'Execution error'
                self.db.result['outcome'] = 'Missing output file'
                return
            if local_diff:
                if self.debugger.dut.local_diff():
                    self.db.result['data_diff'] = 1.0
                else:
                    self.db.result['data_diff'] = 0
            if not local_diff or self.db.result['data_diff'] != 1.0:
                result_folder = (
                    'campaign-data/'+str(self.db.campaign['id']) +
                    '/results/'+str(self.db.result['id']))
                makedirs(result_folder)
                output_location = \
                    result_folder+'/'+self.db.campaign['output_file']
                gold_location = (
                    'campaign-data/'+str(self.db.campaign['id']) +
                    '/gold_'+self.db.campaign['output_file'])
                try:
                    if self.db.campaign['aux_output_file']:
                        self.debugger.aux.get_file(
                            self.db.campaign['output_file'], output_location)
                    else:
                        self.debugger.dut.get_file(
                            self.db.campaign['output_file'], output_location)
                except DrSEUsError as error:
                    self.db.result['outcome_category'] = 'File transfer error'
                    self.db.result['outcome'] = error.type
                    if not listdir(result_folder):
                        rmtree(result_folder)
                    return
                with open(gold_location, 'rb') as solution:
                    solutionContents = solution.read()
                with open(output_location, 'rb') as result:
                    resultContents = result.read()
                self.db.result['data_diff'] = SequenceMatcher(
                    None, solutionContents, resultContents).quick_ratio()
            if self.db.result['data_diff'] == 1.0:
                if not local_diff:
                    rmtree(result_folder)
                if self.db.result['detected_errors']:
                    self.db.result['outcome_category'] = 'Data error'
                    self.db.result['outcome'] = 'Corrected data error'
            else:
                self.db.result['outcome_category'] = 'Data error'
                if self.db.result['detected_errors']:
                    self.db.result['outcome'] = 'Detected data error'
                else:
                    self.db.result['outcome'] = 'Silent data error'
            try:
                if self.db.campaign['aux_output_file']:
                    self.debugger.aux.command('rm ' +
                                              self.db.campaign['output_file'])
                else:
                    self.debugger.dut.command('rm ' +
                                              self.db.campaign['output_file'])
            except DrSEUsError as error:
                self.db.result['outcome_category'] = 'Post execution error'
                self.db.result['outcome'] = error.type
                return

    # def __monitor_execution(self, start_time=None, latent_faults=0,
    #                         persistent_faults=False):
        if self.db.campaign['aux']:
            try:
                self.debugger.aux.read_until()
            except DrSEUsError as error:
                self.debugger.dut.write('\x03')
                self.db.result['outcome_category'] = 'AUX execution error'
                self.db.result['outcome'] = error.type
            else:
                if self.db.campaign['kill_dut']:
                    self.debugger.dut.write('\x03')
        try:
            self.db.result['returned'] = self.debugger.dut.read_until()[1]
        except DrSEUsError as error:
            self.db.result['outcome_category'] = 'Execution error'
            self.db.result['outcome'] = error.type
            self.db.result['returned'] = error.returned
        finally:
            if log_time:
                if self.db.campaign['simics']:
                    try:
                        self.debugger.halt_dut()
                    except DrSEUsError as error:
                        self.db.result['outcome_category'] = 'Simics error'
                        self.db.result['outcome'] = error.type
                    end_cycles, end_time = self.debugger.get_time()
                    self.db.result['cycles'] = \
                        end_cycles - self.db.campaign['start_cycle']
                    self.db.result['execution_time'] = (
                        end_time - self.db.campaign['start_time'])
                    self.debugger.continue_dut()
                else:
                    self.db.result['execution_time'] = \
                        self.debugger.dut.get_timer_value()
        if self.db.campaign['output_file'] and \
                self.db.result['outcome'] == 'In progress':
            check_output()
        if self.db.result['outcome'] == 'In progress':
            self.db.result['outcome_category'] = 'No error'
            if persistent_faults:
                self.db.result['outcome'] = 'Persistent faults'
            elif latent_faults:
                self.db.result['outcome'] = 'Latent faults'
            else:
                self.db.result['outcome'] = 'Masked faults'

    def inject_campaign(self, iteration_counter=None, timer=None):

        def prepare_dut():
            if self.options.command == 'inject':
                try:
                    self.debugger.reset_dut()
                except DrSEUsError as error:
                    self.db.result.update({
                        'outcome_category': 'Debugger error',
                        'outcome': str(error)})
                    with self.db as db:
                        db.log_result()
                    return False
            if self.db.campaign['aux']:
                with self.db as db:
                    db.log_event('Information', 'AUX', 'Command',
                                 self.db.campaign['aux_command'])
                self.debugger.aux.write(self.db.campaign['aux_command']+'\n')
            return True

        def continue_dut():
            try:
                self.debugger.continue_dut()
                if self.db.campaign['aux']:
                    aux_process = Thread(
                        target=self.debugger.aux.read_until,
                        kwargs={'flush': False})
                    aux_process.start()
                self.debugger.dut.read_until(flush=False)
                if self.db.campaign['aux']:
                    aux_process.join()
            except DrSEUsError:
                pass

        def close_simics():
            try:
                self.debugger.close()
            except DrSEUsError as error:
                self.db.result.update({
                    'outcome_category': 'Simics error',
                    'outcome': str(error)})
            finally:
                rmtree('simics-workspace/injected-checkpoints/' +
                       str(self.db.campaign['id'])+'/' +
                       str(self.db.result['id']))

        def check_latent_faults():
            for i in range(self.options.latent_iterations):
                if self.db.result['outcome'] == 'Latent faults' or \
                    (not self.db.campaign['simics'] and
                        self.db.result['outcome'] == 'Masked faults'):
                    with self.db as db:
                        if self.db.campaign['aux']:
                            db.log_event('Information', 'AUX', 'Command',
                                         self.db.campaign['aux_command'])
                        db.log_event('Information', 'DUT', 'Command',
                                     self.db.campaign['command'])
                    if self.db.campaign['aux']:
                        self.debugger.aux.write(
                            self.db.campaign['aux_command']+'\n')
                    self.debugger.dut.write(
                        self.db.campaign['command']+'\n')
                    outcome_category = self.db.result['outcome_category']
                    outcome = self.db.result['outcome']
                    self.__monitor_execution()
                    if self.db.result['outcome_category'] != 'No error':
                        self.db.result['outcome_category'] = \
                            'Post execution error'
                    else:
                        self.db.result.update({
                            'outcome_category': outcome_category,
                            'outcome': outcome})

    # def inject_campaign(self, iteration_counter):
        if self.db.campaign['command']:
            if timer is not None:
                start = perf_counter()
            while True:
                if timer is not None and (perf_counter()-start >= timer):
                    break
                if iteration_counter is not None:
                    with iteration_counter.get_lock():
                        iteration = iteration_counter.value
                        if iteration:
                            iteration_counter.value -= 1
                        else:
                            break
                self.db.result['num_injections'] = self.options.injections
                if not self.db.campaign['simics']:
                    if not prepare_dut():
                        continue
                    with self.db as db:
                        db.log_event('Information', 'DUT', 'Command',
                                     self.db.campaign['command'])
                    self.debugger.dut.reset_timer()
                try:
                    latent_faults, persistent_faults = \
                        self.debugger.inject_faults()
                except DrSEUsError as error:
                    self.db.result['outcome'] = str(error)
                    if self.db.campaign['simics']:
                        self.db.result['outcome_category'] = 'Simics error'
                    else:
                        self.db.result['outcome_category'] = 'Debugger error'
                        continue_dut()
                else:
                    self.__monitor_execution(
                        latent_faults, persistent_faults, log_time=True)
                    check_latent_faults()
                if self.db.campaign['simics']:
                    close_simics()
                else:
                    self.debugger.dut.flush()
                    if self.db.campaign['aux']:
                        self.debugger.aux.flush()
                with self.db as db:
                    db.log_result()
        elif self.options.injections:
            print('cannot inject campaign without application')
        else:
            print('cannot supervise campaign without application')
        if self.options.command == 'inject':
            self.close()
