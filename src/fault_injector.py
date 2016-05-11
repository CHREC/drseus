from datetime import datetime
from difflib import SequenceMatcher
from os import listdir, makedirs
from os.path import exists, join
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
    def __init__(self, options, power_switch=None):
        self.options = options
        self.db = database(options)
        if self.db.campaign.simics and self.db.campaign.architecture in \
                ['a9', 'p2020']:
            self.debugger = simics(self.db, options)
        elif options.jtag and self.db.campaign.architecture == 'a9':
            self.debugger = openocd(self.db, options, power_switch)
        elif options.jtag and self.db.campaign.architecture == 'p2020':
            self.debugger = bdi(self.db, options)
        else:
            self.debugger = dummy(self.db, options, power_switch)
        if self.db.campaign.aux and not self.db.campaign.simics:
            self.debugger.aux.write('\x03')
            self.debugger.aux.do_login()

    def __str__(self):
        string = 'DrSEUs Attributes:\n\tDebugger: {}\n\tDUT:\t{}'.format(
            self.debugger, str(self.debugger.dut).replace('\n\t', '\n\t\t'))
        if self.db.campaign.aux:
            string += '\n\tAUX:\t{}'.format(str(self.debugger.aux).replace(
                '\n\t', '\n\t\t'))
        string += ('\n\tCampaign Information:\n\t\tCampaign Number: {}'.format(
            self.db.campaign.id))
        if self.db.campaign.command:
            string += '\n\t\tDUT Command: "{}"'.format(
                self.db.campaign.command)
            if self.db.campaign.aux:
                string += '\n\t\tAUX Command: "{}"'.format(
                    self.db.campaign.aux_command)
            string += '\n\t\tExecution Time: {} seconds'.format(
                self.db.campaign.execution_time)
            if self.db.campaign.simics:
                string += '\n\t\tExecution Cycles: {:,}\n'.format(
                    self.db.campaign.cycles)
        return string

    def close(self, log=True):
        self.debugger.close()
        if log and self.db.result is not None:
            result_items = self.db.result.event_set.count()
            result_items += self.db.result.injection_set.count()
            result_items += self.db.result.simics_memory_diff_set.count()
            result_items += self.db.result.simics_register_diff_set.count()
            if result_items or self.db.result.dut_output or \
                    self.db.result.aux_output or self.db.result.debugger_output:
                if self.db.result.outcome == 'In progress':
                    self.db.result.outcome_category = 'DrSEUs'
                    self.db.result.outcome = 'Exited'
                self.db.log_result(exit=True)
            else:
                self.db.result.delete()

    def setup_campaign(self):
        if self.db.campaign.command or self.db.campaign.simics:
            if self.db.campaign.simics:
                self.debugger.launch_simics()
            self.debugger.reset_dut()
            self.debugger.time_application()
            gold_folder = 'campaign-data/{}/gold'.format(self.db.campaign.id)
            makedirs(gold_folder)
            if self.db.campaign.output_file:
                if self.db.campaign.aux_output_file:
                    self.debugger.aux.get_file(
                        self.db.campaign.output_file, gold_folder)
                    self.debugger.aux.command('rm {}'.format(
                        self.db.campaign.output_file))
                else:
                    self.debugger.dut.get_file(
                        self.db.campaign.output_file, gold_folder)
                    self.debugger.dut.command('rm {}'.format(
                      self.db.campaign.output_file))
            for log_file in self.db.campaign.log_files:
                if self.db.campaign.aux_output_file:
                    self.debugger.aux.get_file(log_file, gold_folder)
                    self.debugger.aux.command('rm {}'.format(log_file))
                else:
                    self.debugger.dut.get_file(log_file, gold_folder)
                    self.debugger.dut.command('rm {}'.format(log_file))
            if not listdir(gold_folder):
                rmtree(gold_folder)
            self.db.campaign.timestamp = datetime.now()
            self.db.campaign.save()
        self.close()

    def __monitor_execution(self, latent_faults=0, persistent_faults=False,
                            log_time=False, latent_iteration=0):

        def check_output():
            local_diff = \
                hasattr(self.options, 'local_diff') and self.options.local_diff
            try:
                if self.db.campaign.aux_output_file:
                    directory_listing = self.debugger.aux.command('ls -l')[0]
                else:
                    directory_listing = self.debugger.dut.command('ls -l')[0]
            except DrSEUsError as error:
                self.db.result.outcome_category = 'Post execution error'
                self.db.result.outcome = error.type
                return
            if local_diff:
                directory_listing = directory_listing.replace(
                    'gold_{}'.format(self.db.campaign.output_file), '')
            if self.db.campaign.output_file not in directory_listing:
                self.db.result.outcome_category = 'Execution error'
                self.db.result.outcome = 'Missing output file'
                return
            if local_diff:
                if self.debugger.dut.local_diff():
                    self.db.result.data_diff = 1.0
                else:
                    self.db.result.data_diff = 0
            if not local_diff or self.db.result.data_diff != 1.0:
                result_folder = 'campaign-data/{}/results/{}'.format(
                    self.db.campaign.id, self.db.result.id)
                if not exists(result_folder):
                    makedirs(result_folder)
                try:
                    if self.db.campaign.aux_output_file:
                        self.debugger.aux.get_file(
                            self.db.campaign.output_file, result_folder)
                    else:
                        self.debugger.dut.get_file(
                            self.db.campaign.output_file, result_folder)
                except DrSEUsError as error:
                    self.db.result.outcome_category = 'File transfer error'
                    self.db.result.outcome = error.type
                    if not listdir(result_folder):
                        rmtree(result_folder)
                    return
                with open(
                        'campaign-data/{}/gold/{}'.format(
                            self.db.campaign.id, self.db.campaign.output_file),
                        'rb') as solution:
                    solutionContents = solution.read()
                with open(join(result_folder, self.db.campaign.output_file),
                          'rb') as result:
                    resultContents = result.read()
                self.db.result.data_diff = SequenceMatcher(
                    None, solutionContents, resultContents).quick_ratio()
            if self.db.result.data_diff == 1.0:
                if not local_diff:
                    rmtree(result_folder)
                if self.db.result.detected_errors:
                    self.db.result.outcome_category = 'Data error'
                    self.db.result.outcome = 'Corrected data error'
            else:
                self.db.result.outcome_category = 'Data error'
                if self.db.result.detected_errors:
                    self.db.result.outcome = 'Detected data error'
                else:
                    self.db.result.outcome = 'Silent data error'
            try:
                if self.db.campaign.aux_output_file:
                    self.debugger.aux.command('rm {}'.format(
                        self.db.campaign.output_file))
                else:
                    self.debugger.dut.command('rm {}'.format(
                        self.db.campaign.output_file))
            except DrSEUsError as error:
                self.db.result.outcome_category = 'Post execution error'
                self.db.result.outcome = error.type
                return

        def get_log():
            result_folder = 'campaign-data/{}/results/{}'.format(
                self.db.campaign.id, self.db.result.id)
            if latent_iteration:
                result_folder += '/latent/{}'.format(latent_iteration)
            if not exists(result_folder):
                    makedirs(result_folder)
            for log_file in self.db.campaign.log_files:
                try:
                    if self.db.campaign.aux_output_file:
                        file_path = self.debugger.aux.get_file(log_file,
                                                               result_folder)
                    else:
                        file_path = self.debugger.dut.get_file(log_file,
                                                               result_folder)
                except DrSEUsError:
                    if not listdir(result_folder):
                        rmtree(result_folder)
                    return
                else:
                    if self.db.result.outcome == 'In progress' and \
                            self.options.log_error_messages:
                        with open(file_path, 'r') as log:
                            log_contents = log.read()
                        for message in self.options.log_error_messages:
                            if message in log_contents:
                                self.db.result.outcome_category = 'Log error'
                                self.db.result.outcome = message
                                break
                try:
                    if self.db.campaign.aux_output_file:
                        self.debugger.aux.command('rm {}'.format(log_file))
                    else:
                        self.debugger.dut.command('rm {}'.format(log_file))
                except DrSEUsError:
                    pass

    # def __monitor_execution(self, start_time=None, latent_faults=0,
    #                         persistent_faults=False):
        if self.db.campaign.aux:
            try:
                self.debugger.aux.read_until()
            except DrSEUsError as error:
                self.debugger.dut.write('\x03')
                self.db.result.outcome_category = 'AUX execution error'
                self.db.result.outcome = error.type
            else:
                if self.db.campaign.kill_dut:
                    self.debugger.dut.write('\x03')
        try:
            self.db.result.returned = self.debugger.dut.read_until()[1]
        except DrSEUsError as error:
            self.db.result.outcome_category = 'Execution error'
            self.db.result.outcome = error.type
            self.db.result.returned = error.returned
        finally:
            if log_time:
                if self.db.campaign.simics:
                    try:
                        self.debugger.halt_dut()
                    except DrSEUsError as error:
                        self.db.result.outcome_category = 'Simics error'
                        self.db.result.outcome = error.type
                    else:
                        try:
                            end_cycles, end_time = self.debugger.get_time()
                        except DrSEUsError as error:
                            self.db.result.outcome_category = 'Simics error'
                            self.db.result.outcome = error.type
                        else:
                            self.db.result.cycles = \
                                end_cycles - self.db.campaign.start_cycle
                            self.db.result.execution_time = (
                                end_time - self.db.campaign.start_time)
                        self.debugger.continue_dut()
                else:
                    self.db.result.execution_time = \
                        self.debugger.dut.get_timer_value()
        if self.db.campaign.output_file and \
                self.db.result.outcome == 'In progress':
            check_output()
        if self.db.campaign.log_files:
            get_log()
        if self.db.result.outcome == 'In progress':
            self.db.result.outcome_category = 'No error'
            if persistent_faults:
                self.db.result.outcome = 'Persistent faults'
            elif self.db.result.num_register_diffs or \
                    self.db.result.num_memory_diffs:
                self.db.result.outcome = 'Latent faults'
            else:
                self.db.result.outcome = 'Masked faults'

    def inject_campaign(self, iteration_counter=None, timer=None):

        def prepare_dut():
            if self.options.command == 'inject':
                try:
                    self.debugger.reset_dut()
                except DrSEUsError as error:
                    self.db.result.outcome_category = 'Debugger error'
                    self.db.result.outcome = str(error)
                    self.db.log_result()
                    return False
            if self.db.campaign.aux:
                self.db.log_event(
                    'Information', 'AUX', 'Command',
                    self.db.campaign.aux_command)
                self.debugger.aux.write('{}\n'.format(
                    self.db.campaign.aux_command))
            return True

        def continue_dut():
            try:
                self.debugger.continue_dut()
                if self.db.campaign.aux:
                    aux_process = Thread(
                        target=self.debugger.aux.read_until,
                        kwargs={'flush': False})
                    aux_process.start()
                self.debugger.dut.read_until(flush=False)
                if self.db.campaign.aux:
                    aux_process.join()
            except DrSEUsError:
                pass

        def close_simics():
            try:
                self.debugger.close()
            except DrSEUsError as error:
                self.db.result.outcome_category = 'Simics error'
                self.db.result.outcome = str(error)
            finally:
                rmtree('simics-workspace/injected-checkpoints/{}/{}'.format(
                       self.db.campaign.id, self.db.result.id))

        def check_latent_faults():
            for i in range(1, self.options.latent_iterations+1):
                if self.db.result.outcome == 'Latent faults' or \
                    (not self.db.campaign.simics and
                        self.db.result.outcome == 'Masked faults'):
                    if self.db.campaign.aux:
                        self.db.log_event(
                            'Information', 'AUX', 'Command',
                            self.db.campaign.aux_command)
                    self.db.log_event(
                        'Information', 'DUT', 'Command',
                        self.db.campaign.command)
                    if self.db.campaign.aux:
                        self.debugger.aux.write('{}\n'.format(
                            self.db.campaign.aux_command))
                    self.debugger.dut.write('{}\n'.format(
                        self.db.campaign.command))
                    outcome_category = self.db.result.outcome_category
                    outcome = self.db.result.outcome
                    self.__monitor_execution(latent_iteration=i)
                    if self.db.result.outcome_category != 'No error':
                        self.db.result.outcome_category = \
                            'Post execution error'
                    else:
                        self.db.result.outcome_category = outcome_category
                        self.db.result.outcome = outcome

    # def inject_campaign(self, iteration_counter):
        if self.db.campaign.command:
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
                self.db.result.num_injections = self.options.injections
                if not self.db.campaign.simics:
                    if not prepare_dut():
                        continue
                    self.db.log_event(
                        'Information', 'DUT', 'Command',
                        self.db.campaign.command)
                    self.debugger.dut.reset_timer()
                try:
                    (self.db.result.num_register_diffs,
                     self.db.result.num_memory_diffs, persistent_faults) = \
                        self.debugger.inject_faults()
                except DrSEUsError as error:
                    self.db.result.outcome = str(error)
                    if self.db.campaign.simics:
                        self.db.result.outcome_category = 'Simics error'
                    else:
                        self.db.result.outcome_category = 'Debugger error'
                        continue_dut()
                else:
                    self.__monitor_execution(persistent_faults, log_time=True)
                    check_latent_faults()
                if self.db.campaign.simics:
                    close_simics()
                else:
                    try:
                        self.debugger.dut.flush(check_errors=True)
                    except DrSEUsError as error:
                        self.db.result.outcome_category = 'Post execution error'
                        self.db.result.outcome = error.type
                    if self.db.campaign.aux:
                        self.debugger.aux.flush()
                self.db.log_result()
        elif self.options.injections:
            print('cannot inject campaign without application')
        else:
            print('cannot supervise campaign without application')
        if self.options.command == 'inject':
            self.close()
        elif self.options.command == 'supervise':
            self.db.result.outcome_category = 'DrSEUs'
            self.db.result.outcome = 'Supervisor'
