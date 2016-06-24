from datetime import datetime
from os import listdir, makedirs
from shutil import rmtree
from threading import Thread
from time import perf_counter
from traceback import print_exc

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

        def time_application():
            if self.db.campaign.command:
                event = self.db.log_event(
                    'Information', 'Fault Injector', 'Timed application',
                    success=False, campaign=True)
                execution_cycles = []
                execution_times = []
                for i in range(self.options.iterations):
                    if self.db.campaign.aux:
                        self.debugger.aux.write('{}\n'.format(
                            self.db.campaign.aux_command))
                    if self.db.campaign.simics:
                        self.debugger.halt_dut()
                        start = self.debugger.get_time()
                    else:
                        self.debugger.dut.reset_timer()
                    self.debugger.dut.write('{}\n'.format(
                        self.db.campaign.command))
                    if self.db.campaign.simics:
                        self.debugger.continue_dut()
                    if self.db.campaign.kill_dut:
                        self.debugger.aux.read_until()
                        self.debugger.dut.write('\x03')
                        self.debugger.dut.read_until()
                    elif self.db.campaign.kill_aux:
                        self.debugger.dut.read_until()
                        self.debugger.aux.write('\x03')
                        self.debugger.aux.read_until()
                    elif self.db.campaign.aux:
                        self.debugger.dut.read_until()
                        self.debugger.aux.read_until()
                    else:
                        self.debugger.dut.read_until()
                    if self.db.campaign.simics:
                        self.debugger.halt_dut()
                        end = self.debugger.get_time()
                        execution_cycles.append(end[0] - start[0])
                        execution_times.append(end[1] - start[1])
                        self.debugger.continue_dut()
                    else:
                        execution_times.append(
                            self.debugger.dut.get_timer_value())
                    if i < self.options.iterations-1:
                        if self.db.campaign.output_file:
                            if self.db.campaign.aux_output_file:
                                self.debugger.aux.command('rm {}'.format(
                                    self.db.campaign.output_file))
                            else:
                                self.debugger.dut.command('rm {}'.format(
                                    self.db.campaign.output_file))
                        for log_file in self.db.campaign.log_files:
                            self.debugger.dut.command('rm {}'.format(log_file))
                        if self.db.campaign.aux:
                            for log_file in self.db.campaign.aux_log_files:
                                self.debugger.aux.command(
                                    'rm {}'.format(log_file))
                if self.db.campaign.simics:
                    self.debugger.halt_dut()
                    end_cycles, end_time = self.debugger.get_time()
                    self.db.campaign.start_cycle = end_cycles
                    self.db.campaign.start_time = end_time
                    self.db.campaign.cycles = \
                        int(sum(execution_cycles) / len(execution_cycles))
                self.db.campaign.execution_time = \
                    sum(execution_times) / len(execution_times)
                event.success = True
                event.timestamp = datetime.now()
                event.save()
                if self.db.campaign.simics:
                    self.debugger.create_checkpoints()

    # def setup_campaign(self):
        if self.db.campaign.command or self.db.campaign.simics:
            if self.db.campaign.simics:
                self.debugger.launch_simics()
            self.debugger.reset_dut()
            time_application()
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
                self.debugger.dut.get_file(log_file, gold_folder)
                self.debugger.dut.command('rm {}'.format(log_file))
            if self.db.campaign.aux:
                for log_file in self.db.campaign.aux_log_files:
                    self.debugger.aux.get_file(log_file, gold_folder)
                    self.debugger.aux.command('rm {}'.format(log_file))
            if not listdir(gold_folder):
                rmtree(gold_folder)
            self.db.campaign.timestamp = datetime.now()
            self.db.campaign.save()
        self.close()

    def inject_campaign(self, iteration_counter=None, timer=None):

        def monitor_execution(persistent_faults=False, log_time=False,
                              latent_iteration=0):
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
                if hasattr(self.debugger, 'aux') and \
                        self.db.campaign.aux_output_file:
                    self.debugger.aux.check_output()
                else:
                    self.debugger.dut.check_output()
            if self.db.campaign.log_files:
                self.debugger.dut.get_logs(latent_iteration)
            if self.db.campaign.aux_log_files:
                self.debugger.aux.get_logs(latent_iteration)
            if self.db.result.outcome == 'In progress':
                self.db.result.outcome_category = 'No error'
                if persistent_faults:
                    self.db.result.outcome = 'Persistent faults'
                elif self.db.result.num_register_diffs or \
                        self.db.result.num_memory_diffs:
                    self.db.result.outcome = 'Latent faults'
                else:
                    self.db.result.outcome = 'Masked faults'

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
                    monitor_execution(latent_iteration=i)
                    if self.db.result.outcome_category != 'No error':
                        self.db.result.outcome_category = \
                            'Post execution error'
                    else:
                        self.db.result.outcome_category = outcome_category
                        self.db.result.outcome = outcome

        def perform_injections():
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
                        if self.options.command == 'inject':
                            try:
                                self.debugger.reset_dut()
                            except DrSEUsError as error:
                                self.db.result.outcome_category = \
                                    'Debugger error'
                                self.db.result.outcome = str(error)
                                self.db.log_result()
                                continue
                        if self.db.campaign.aux:
                            self.db.log_event(
                                'Information', 'AUX', 'Command',
                                self.db.campaign.aux_command)
                            self.debugger.aux.write('{}\n'.format(
                                self.db.campaign.aux_command))
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
                    else:
                        monitor_execution(persistent_faults, True)
                        check_latent_faults()
                    if self.db.campaign.simics:
                        try:
                            self.debugger.close()
                        except DrSEUsError as error:
                            self.db.result.outcome_category = 'Simics error'
                            self.db.result.outcome = str(error)
                        finally:
                            rmtree('simics-workspace/injected-checkpoints/{}/{}'
                                   ''.format(self.db.campaign.id,
                                             self.db.result.id))
                    else:
                        try:
                            self.debugger.dut.flush(check_errors=True)
                        except DrSEUsError as error:
                            self.db.result.outcome_category = \
                                'Post execution error'
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
                self.db.result.outcome_category = 'Supervisor'
                self.db.result.outcome = ''
                self.db.result.save()

    # def inject_campaign(self, iteration_counter):
        try:
            perform_injections()
        except KeyboardInterrupt:
            self.db.result.outcome_category = 'Incomplete'
            self.db.result.outcome = 'Interrupted'
            self.db.result.save()
            self.db.log_event(
                'Information', 'User', 'Interrupted', self.db.log_exception)
            if self.db.campaign.simics:
                self.debugger.continue_dut()
            self.debugger.dut.write('\x03')
            if self.db.campaign.aux:
                self.debugger.aux.write('\x03')
            self.debugger.close()
            self.db.log_result(
                exit=self.options.command != 'supervise',
                supervisor=self.options.command == 'supervise')
        except:
            self.db.result.outcome_category = 'Incomplete'
            self.db.result.outcome = 'Uncaught exception'
            self.db.result.save()
            print_exc()
            self.db.log_event(
                'Error', 'Fault injector', 'Exception', self.db.log_exception)
            self.debugger.close()
            self.db.log_result(
                exit=self.options.command != 'supervise',
                supervisor=self.options.command == 'supervise')
