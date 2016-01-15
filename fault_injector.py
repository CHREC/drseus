from __future__ import print_function
from datetime import datetime
from difflib import SequenceMatcher
import os
from paramiko import RSAKey
import random
import shutil
import subprocess
from termcolor import colored
from threading import Thread
from time import sleep

from error import DrSEUsError
from jtag import bdi_p2020, openocd
from simics import simics
from sql import sql


class fault_injector:
    def __init__(self, campaign_data, options):
        self.campaign_data = campaign_data
        if os.path.exists(
                'campaign-data/'+str(campaign_data['id'])+'/private.key'):
            self.rsakey = RSAKey.from_private_key_file(
                'campaign-data/'+str(campaign_data['id'])+'/private.key')
        else:
            self.rsakey = RSAKey.generate(1024)
            self.rsakey.write_private_key_file(
                'campaign-data/'+str(campaign_data['id'])+'/private.key')
        if self.campaign_data['use_simics']:
            self.debugger = simics(
                campaign_data['id'], campaign_data['architecture'], self.rsakey,
                campaign_data['use_aux'], options.debug, options.timeout)
        else:
            if campaign_data['architecture'] == 'p2020':
                self.debugger = bdi_p2020(
                    options.debugger_ip_address, self.rsakey,
                    options.dut_serial_port, options.aux_serial_port,
                    campaign_data['use_aux'], options.dut_prompt,
                    options.aux_prompt, options.debug, options.timeout,
                    campaign_data['id'])
            elif campaign_data['architecture'] == 'a9':
                self.debugger = openocd(
                    options.debugger_ip_address, self.rsakey,
                    options.dut_serial_port, options.aux_serial_port,
                    options.campaign_data['use_aux'], options.dut_prompt,
                    options.aux_prompt, options.debug, options.timeout,
                    campaign_data['id'])

    def __str__(self):
        string = ('DrSEUs Attributes:\n\tDebugger: '+str(self.debugger) +
                  '\n\tDUT:\t'+str(self.debugger.dut).replace('\n\t', '\n\t\t'))
        if self.campaign_data['use_aux']:
            string += '\n\tAUX:\t'+str(self.debugger.aux).replace('\n\t',
                                                                  '\n\t\t')
        string += ('\n\tCampaign Information:\n\t\tCampaign Number: ' +
                   str(self.campaign_data['id'])+'\n\t\tDUT Command: \"' +
                   self.campaign_data['command']+'\"')
        if self.campaign_data['use_aux']:
            string += ('\n\t\tAUX Command: \"' +
                       self.campaign_data['aux_command']+'\"')
        try:
            string += ('\n\t\tExecution Time: ' +
                       str(self.campaign_data['exec_time'])+' seconds')
        except AttributeError:
            pass
        return string

    def close(self):
        if not self.campaign_data['use_simics']:
            self.debugger.close()

    def setup_campaign(self, options):
        if self.campaign_data['use_simics']:
            try:
                self.debugger.launch_simics()
            except DrSEUsError:
                raise Exception('error launching simics, check your license '
                                'connection')
        else:
            if self.campaign_data['use_aux']:
                self.debugger.aux.serial.write('\x03')
                aux_process = Thread(target=self.debugger.aux.do_login)
                aux_process.start()
            self.debugger.reset_dut()
            if self.campaign_data['use_aux']:
                aux_process.join()
        files = []
        files.append(options.directory+'/'+self.campaign_data['application'])
        if options.files:
            for item in options.files.split(','):
                files.append(options.directory+'/'+item.lstrip().rstrip())
        os.makedirs('campaign-data/'+str(self.campaign_data['id'])+'/dut-files')
        for item in files:
            shutil.copy(item, 'campaign-data/'+str(self.campaign_data['id']) +
                              '/dut-files/')
        if self.campaign_data['use_aux']:
            files_aux = []
            files_aux.append(options.directory+'/' +
                             self.campaign_data['aux_application'])
            if options.aux_files:
                for item in options.aux_files.split(','):
                    files_aux.append(
                        options.directory+'/'+item.lstrip().rstrip())
            os.makedirs('campaign-data/'+str(self.campaign_data['id']) +
                        '/aux-files')
            for item in files_aux:
                shutil.copy(item, 'campaign-data/' +
                                  str(self.campaign_data['id'])+'/aux-files/')
            aux_process = Thread(target=self.debugger.aux.send_files,
                                 args=(files_aux, ))
            aux_process.start()
        self.debugger.dut.send_files(files)
        if self.campaign_data['use_aux']:
            aux_process.join()
            aux_process = Thread(target=self.debugger.aux.command)
            aux_process.start()
        self.debugger.dut.command()
        if self.campaign_data['use_aux']:
            aux_process.join()
        self.campaign_data['exec_time'], self.campaign_data['num_cycles'] = \
            self.debugger.time_application(self.campaign_data['command'],
                                           self.campaign_data['aux_command'],
                                           options.timing_iterations,
                                           self.campaign_data['kill_dut'])
        if self.campaign_data['use_simics']:
            (self.campaign_data['cycles_between'],
             self.campaign_data['num_checkpoints']) = \
                self.debugger.create_checkpoints(
                    self.campaign_data['command'],
                    self.campaign_data['aux_command'],
                    self.campaign_data['num_cycles'], options.num_checkpoints,
                    self.campaign_data['kill_dut'])
        if self.campaign_data['output_file']:
            if self.campaign_data['use_aux_output']:
                self.debugger.aux.get_file(
                    self.campaign_data['output_file'],
                    'campaign-data/'+str(self.campaign_data['id'])+'/gold_' +
                    self.campaign_data['output_file'])
            else:
                self.debugger.dut.get_file(
                    self.campaign_data['output_file'],
                    'campaign-data/'+str(self.campaign_data['id'])+'/gold_' +
                    self.campaign_data['output_file'])
        if self.campaign_data['use_simics']:
            self.debugger.close()
        self.campaign_data['dut_output'] = self.debugger.dut.output
        self.campaign_data['debugger_output'] = self.debugger.output
        if self.campaign_data['use_aux']:
            self.campaign_data['aux_output'] = self.debugger.aux.output
        with sql() as db:
            db.update_dict('campaign', self.campaign_data,
                           self.campaign_data['id'])
        self.close()

    def send_dut_files(self, aux=False):
        location = 'campaign-data/'+str(self.campaign_data['id'])
        if aux:
            location += '/aux-files/'
        else:
            location += '/dut-files/'
        files = []
        for item in os.listdir(location):
            files.append(location+item)
        if aux:
            self.debugger.aux.send_files(files)
        else:
            self.debugger.dut.send_files(files)

    def create_result(self, num_injections=0):
        self.data_diff = None
        self.detected_errors = None
        self.logged = False
        result_data = {'campaign_id': self.campaign_data['id'],
                       'num_injections': num_injections,
                       'outcome': 'In progress',
                       'outcome_category': 'Incomplete',
                       'timestamp': datetime.now()}
        with sql() as db:
            db.insert_dict('result', result_data)
            self.result_id = db.cursor.lastrowid
            db.insert_dict('injection',
                           {'result_id': self.result_id, 'injection_number': 0})

    def inject_faults(self, num_injections, selected_targets, compare_all):
        if self.campaign_data['use_simics']:
            checkpoint_nums = range(1, self.campaign_data['num_checkpoints'])
            injected_checkpoint_nums = []
            for i in xrange(num_injections):
                checkpoint_num = random.choice(checkpoint_nums)
                checkpoint_nums.remove(checkpoint_num)
                injected_checkpoint_nums.append(checkpoint_num)
            injected_checkpoint_nums = sorted(injected_checkpoint_nums)
            return self.debugger.inject_fault(
                self.result_id, injected_checkpoint_nums, selected_targets,
                self.campaign_data['cycles_between'],
                self.campaign_data['num_checkpoints'], compare_all)
        else:
            injection_times = []
            for i in xrange(num_injections):
                injection_times.append(
                    random.uniform(0, self.campaign_data['exec_time']))
            injection_times = sorted(injection_times)
            self.debugger.inject_fault(
                self.result_id, injection_times, self.campaign_data['command'],
                selected_targets)
            return 0

    def check_output(self):
        missing_output = False
        result_folder = ('campaign-data/'+str(self.campaign_data['id'])+'/'
                         'results/'+str(self.result_id))
        os.makedirs(result_folder)
        output_location = result_folder+'/'+self.campaign_data['output_file']
        gold_location = ('campaign-data/'+str(self.campaign_data['id'])+'/'
                         'gold_'+self.campaign_data['output_file'])
        if self.campaign_data['use_aux_output']:
            self.debugger.aux.get_file(self.campaign_data['output_file'],
                                       output_location)
        else:
            self.debugger.dut.get_file(self.campaign_data['output_file'],
                                       output_location)
        if not os.listdir(result_folder):
            os.rmdir(result_folder)
            missing_output = True
        else:
            with open(gold_location, 'r') as solution:
                solutionContents = solution.read()
            with open(output_location, 'r') as result:
                resultContents = result.read()
            self.data_diff = SequenceMatcher(None, solutionContents,
                                             resultContents).quick_ratio()
            if self.data_diff == 1.0:
                os.remove(output_location)
                if not os.listdir(result_folder):
                    os.rmdir(result_folder)
        if self.campaign_data['use_aux_output']:
            self.debugger.aux.command('rm '+self.campaign_data['output_file'])
        else:
            self.debugger.dut.command('rm '+self.campaign_data['output_file'])
        if missing_output:
            raise DrSEUsError(DrSEUsError.missing_output)

    def monitor_execution(self, latent_faults=0):
        buff = ''
        aux_buff = ''
        outcome = ''
        outcome_category = ''
        if self.campaign_data['use_aux']:
            try:
                aux_buff = self.debugger.aux.read_until()
            except DrSEUsError as error:
                self.debugger.dut.serial.write('\x03')
                outcome = error.type
                outcome_category = 'AUX execution error'
            else:
                if self.campaign_data['kill_dut']:
                    self.debugger.dut.serial.write('\x03')
        try:
            buff = self.debugger.dut.read_until()
        except DrSEUsError as error:
            outcome = error.type
            outcome_category = 'Execution error'
        for line in buff.split('\n'):
            if 'drseus_detected_errors:' in line:
                self.detected_errors = int(line.replace(
                                           'drseus_detected_errors:', ''))
                break
        if self.campaign_data['use_aux']:
            for line in aux_buff.split('\n'):
                if 'drseus_detected_errors:' in line:
                    if self.detected_errors is None:
                        self.detected_errors = 0
                    self.detected_errors += int(line.replace(
                                                'drseus_detected_errors:', ''))
                    break
        if self.campaign_data['output_file'] and not outcome:
            try:
                self.check_output()
            except DrSEUsError as error:
                if error.type == DrSEUsError.scp_error:
                    outcome = 'Error getting output file'
                    outcome_category = 'SCP error'
                elif error.type == DrSEUsError.missing_output:
                    outcome = 'Missing output file'
                    outcome_category = 'SCP error'
                else:
                    outcome = error.type
                    outcome_category = 'Post execution error'
        if not outcome:
            if self.detected_errors:
                if self.data_diff is None or self.data_diff < 1.0:
                    outcome = 'Detected data error'
                    outcome_category = 'Data error'
                elif self.data_diff is not None and self.data_diff == 1:
                    outcome = 'Corrected data error'
                    outcome_category = 'Data error'
            elif self.data_diff is not None and self.data_diff < 1.0:
                outcome = 'Silent data error'
                outcome_category = 'Data error'
            elif latent_faults:
                outcome = 'Latent faults'
                outcome_category = 'No error'
            else:
                outcome = 'Masked faults'
                outcome_category = 'No error'
        return outcome, outcome_category

    def log_result(self, outcome, outcome_category):
        if self.logged:
            return
        try:
            print(colored(self.debugger.dut.serial.port+' ', 'blue'), end='')
        except AttributeError:
            pass
        print(colored('result id '+str(self.result_id)+' outcome: ' +
                      outcome_category+' - '+outcome, 'blue'), end='')
        if self.data_diff is not None and self.data_diff < 1.0:
            print(colored(', data diff: '+str(self.data_diff), 'blue'))
        else:
            print()
        result_data = {'outcome': outcome,
                       'outcome_category': outcome_category,
                       'data_diff': self.data_diff,
                       'detected_errors': self.detected_errors,
                       'debugger_output': self.debugger.output,
                       'timestamp': datetime.now()}
        try:
            result_data['dut_output'] = self.debugger.dut.output
            if self.campaign_data['use_aux']:
                result_data['aux_output'] = self.debugger.aux.output
        except AttributeError:
            pass
        with sql() as db:
            db.cursor.execute('SELECT COUNT(*) FROM log_injection '
                              'WHERE result_id=?', (self.result_id,))
            if db.cursor.fetchone()[0] > 1:
                db.cursor.execute('DELETE FROM log_injection WHERE '
                                  'result_id=? AND injection_number=0',
                                  (self.result_id,))
            db.update_dict('result', result_data, self.result_id)
        self.logged = True
        self.debugger.output = ''
        try:
            self.debugger.dut.output = ''
            if self.campaign_data['use_aux']:
                self.debugger.aux.output = ''
        except AttributeError:
            pass

    def inject_and_monitor(self, iteration_counter, num_injections,
                           selected_targets, compare_all):
        if self.campaign_data['use_aux'] and \
                not self.campaign_data['use_simics']:
            if self.campaign_data['use_aux']:
                self.debugger.aux.serial.write('\x03')
                self.debugger.aux.do_login()
                self.send_dut_files(aux=True)
        while True:
            with iteration_counter.get_lock():
                iteration = iteration_counter.value
                if iteration:
                    iteration_counter.value -= 1
                else:
                    break
            self.create_result(num_injections)
            if not self.campaign_data['use_simics']:
                attempts = 10
                for attempt in xrange(attempts):
                    try:
                        self.debugger.reset_dut()
                    except DrSEUsError as error:
                        print(colored('Error resetting DUT (attempt ' +
                                      str(attempt+1)+'/'+str(attempts) +
                                      '): '+error.type, 'red'))
                        if attempt < attempts-1:
                            sleep(30)
                        else:
                            self.log_result('Error resetting DUT',
                                            'Debugger error')
                            self.close()
                            return
                    else:
                        break
                try:
                    self.send_dut_files()
                except DrSEUsError:
                    self.log_result('Error sending files to DUT', 'SCP error')
                    continue
            if self.campaign_data['use_aux'] and \
                    not self.campaign_data['use_simics']:
                self.debugger.aux.serial.write(
                    str('./'+self.campaign_data['aux_command']+'\n'))
            try:
                latent_faults = self.inject_faults(
                    num_injections, selected_targets, compare_all)
                self.debugger.continue_dut()
            except DrSEUsError as error:
                outcome = error.type
                if self.campaign_data['use_simics']:
                    outcome_category = 'Simics error'
                else:
                    outcome_category = 'Debugger error'
                    if not self.campaign_data['use_simics']:
                        try:
                            self.debugger.continue_dut()
                            if self.campaign_data['use_aux']:
                                aux_process = Thread(
                                    target=self.debugger.aux.read_until)
                                aux_process.start()
                            self.debugger.dut.read_until()
                            if self.campaign_data['use_aux']:
                                aux_process.join()
                        except DrSEUsError:
                            pass
            else:
                outcome, outcome_category = self.monitor_execution(
                    latent_faults)
                if outcome == 'Latent faults' or \
                        (not self.campaign_data['use_simics']
                         and outcome == 'Masked faults'):
                    if self.campaign_data['use_aux']:
                        self.debugger.aux.serial.write(
                            str('./'+self.campaign_data['aux_command']+'\n'))
                    self.debugger.dut.serial.write(
                        str('./'+self.campaign_data['command']+'\n'))
                    next_outcome = self.monitor_execution()[0]
                    if next_outcome != 'Masked faults':
                        outcome = next_outcome
                        outcome_category = 'Post execution error'
                    elif self.campaign_data['use_simics']:
                        if self.debugger.persistent_faults(self.result_id):
                            outcome = 'Persistent faults'
            if self.campaign_data['use_simics']:
                try:
                    self.debugger.close()
                except DrSEUsError as error:
                    outcome = error.type
                    outcome_category = 'Simics error'
                finally:
                    shutil.rmtree('simics-workspace/injected-checkpoints/' +
                                  str(self.campaign_data['id'])+'/' +
                                  str(self.result_id))
            self.log_result(outcome, outcome_category)
        self.close()

    def supervise(self, iteration_counter, packet_capture):
        interrupted = False
        while not interrupted:
            with iteration_counter.get_lock():
                iteration = iteration_counter.value
                if iteration:
                    iteration_counter.value -= 1
                else:
                    break
            self.create_result()
            if packet_capture:
                data_dir = ('campaign-data/'+str(self.campaign_data['id']) +
                            '/results/'+str(self.result_id))
                os.makedirs(data_dir)
                capture_file = open(data_dir+'/capture.pcap', 'w')
                capture_process = subprocess.Popen(['ssh', 'p2020', 'tshark '
                                                    '-F pcap -i eth1 -w -'],
                                                   stderr=subprocess.PIPE,
                                                   stdout=capture_file)
                buff = ''
                while True:
                    buff += capture_process.stderr.read(1)
                    if buff[-len('Capturing on \'eth1\''):] == \
                            'Capturing on \'eth1\'':
                        break
            if self.campaign_data['use_aux']:
                self.debugger.aux.serial.write(
                    str('./'+self.campaign_data['aux_command']+'\n'))
            self.debugger.dut.serial.write(
                str('./'+self.campaign_data['command']+'\n'))
            try:
                outcome, outcome_category = self.monitor_execution()
            except KeyboardInterrupt:
                if self.campaign_data['use_simics']:
                    self.debugger.continue_dut()
                self.debugger.dut.serial.write('\x03')
                self.debugger.dut.read_until()
                if self.campaign_data['use_aux']:
                    self.debugger.aux.serial.write('\x03')
                    self.debugger.aux.read_until()
                outcome, outcome_category = ('Interrupted', 'Incomplete')
                interrupted = True
            self.log_result(outcome, outcome_category)
            if packet_capture:
                os.system('ssh p2020 \'killall tshark\'')
                capture_process.wait()
                capture_file.close()
