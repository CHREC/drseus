from __future__ import print_function
from datetime import datetime
from difflib import SequenceMatcher
import os
from paramiko import RSAKey
import random
import shutil
import sqlite3
import subprocess
from termcolor import colored
from threading import Thread

from bdi import bdi_p2020, bdi_arm
from error import DrSEUSError
from simics import simics


class fault_injector:
    def __init__(self, campaign_number, dut_ip_address, aux_ip_address,
                 dut_serial_port, aux_serial_port, debugger_ip_address,
                 architecture, use_aux, debug, use_simics, timeout):
        self.campaign_number = campaign_number
        self.use_simics = use_simics
        self.use_aux = use_aux
        self.debug = debug
        if os.path.exists('campaign-data/private.key'):
            self.rsakey = RSAKey.from_private_key_file('campaign-data/'
                                                       'private.key')
        else:
            self.rsakey = RSAKey.generate(1024)
            self.rsakey.write_private_key_file('campaign-data/private.key')
        if self.use_simics:
            self.debugger = simics(campaign_number, architecture, self.rsakey,
                                   use_aux, debug, timeout)
        else:
            if architecture == 'p2020':
                self.debugger = bdi_p2020(debugger_ip_address,
                                          dut_ip_address, self.rsakey,
                                          dut_serial_port, aux_ip_address,
                                          aux_serial_port, use_aux,
                                          'root@p2020rdb:~#', debug, timeout)
            elif architecture == 'a9':
                self.debugger = bdi_arm(debugger_ip_address,
                                        dut_ip_address, self.rsakey,
                                        dut_serial_port, aux_ip_address,
                                        aux_serial_port, use_aux, '[root@ZED]#',
                                        debug, timeout)
            if self.use_aux:
                self.debugger.aux.serial.write('\x03')
                aux_process = Thread(target=self.debugger.aux.do_login)
                aux_process.start()
            if self.debugger.telnet:
                self.debugger.reset_dut()
            else:
                self.debugger.dut.serial.write('\x03')
            self.debugger.dut.do_login()
            if self.use_aux:
                aux_process.join()

    def close(self):
        if not self.use_simics:
            self.debugger.close()

    def setup_campaign(self, directory, architecture, application, arguments,
                       output_file, dut_files, aux_files, iterations,
                       aux_application, aux_arguments, use_aux_output,
                       num_checkpoints, kill_dut):
        self.kill_dut = kill_dut
        if self.use_simics:
            self.debugger.launch_simics()
        if arguments:
            self.command = application+' '+arguments
        else:
            self.command = application
        if self.use_aux:
            if aux_arguments:
                self.aux_command = aux_application+' '+aux_arguments
            else:
                self.aux_command = aux_application
        else:
            self.aux_command = ''
        files = []
        files.append(directory+'/'+application)
        if self.use_aux:
            files_aux = []
            files_aux.append(directory+'/'+aux_application)
        if dut_files:
            for item in dut_files.split(','):
                files.append(directory+'/'+item.lstrip().rstrip())
        if self.use_aux:
            if aux_files:
                for item in aux_files.split(','):
                    files_aux.append(directory+'/'+item.lstrip().rstrip())
        if self.use_aux:
            aux_process = Thread(target=self.debugger.aux.send_files,
                                 args=(files_aux, ))
            aux_process.start()
        self.debugger.dut.send_files(files)
        if self.use_aux:
            aux_process.join()
        if self.use_aux:
            aux_process = Thread(target=self.debugger.aux.command)
            aux_process.start()
        self.debugger.dut.command()
        if self.use_aux:
            aux_process.join()
        if self.use_simics:
            num_cycles = self.debugger.calculate_cycles(
                self.command, self.aux_command, self.kill_dut)
        else:
            num_cycles = 0
        exec_time = self.debugger.time_application(self.command,
                                                   self.aux_command, iterations,
                                                   self.kill_dut)
        if output_file:
            if use_aux_output:
                self.debugger.aux.get_file(output_file, 'campaign-data/' +
                                           str(self.campaign_number)+'/gold_' +
                                           output_file)
            else:
                self.debugger.dut.get_file(output_file, 'campaign-data/' +
                                           str(self.campaign_number)+'/gold_' +
                                           output_file)
        if self.use_simics:
            cycles_between = self.debugger.create_checkpoints(
                self.command, self.aux_command, num_cycles, num_checkpoints,
                self.kill_dut)
        else:
            num_checkpoints = 0
            cycles_between = 0
        sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
        sql = sql_db.cursor()
        sql.execute(
            'INSERT INTO drseus_logging_campaign '
            '(campaign_number,application,output_file,command,aux_command,'
            'use_aux,use_aux_output,exec_time,architecture,'
            'use_simics,dut_output,aux_output,debugger_output,paramiko_output,'
            'aux_paramiko_output,num_cycles,num_checkpoints,cycles_between,'
            'timestamp,kill_dut) VALUES '
            '(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (
                self.campaign_number, application, output_file, self.command,
                self.aux_command, self.use_aux, use_aux_output, exec_time,
                architecture, self.use_simics,
                self.debugger.dut.output.decode('utf-8', 'ignore'),
                self.debugger.aux.output.decode('utf-8', 'ignore') if
                self.use_aux else '',
                self.debugger.output,  # .decode('utf-8', 'ignore'),
                self.debugger.dut.paramiko_output,
                self.debugger.aux.paramiko_output if self.use_aux else '',
                num_cycles, num_checkpoints, cycles_between, datetime.now(),
                self.kill_dut
            )
        )
        sql_db.commit()
        sql_db.close()
        if not self.use_simics:
            os.makedirs('campaign-data/'+str(self.campaign_number)+'/dut-files')
            for item in files:
                shutil.copy(item, 'campaign-data/'+str(self.campaign_number) +
                                  '/dut-files/')
            if self.use_aux:
                os.makedirs('campaign-data/'+str(self.campaign_number) +
                            '/aux-files')
                for item in files_aux:
                    shutil.copy(item, 'campaign-data/' +
                                      str(self.campaign_number)+'/aux-files/')
        self.close()

    def send_dut_files(self):
        files = []
        for item in os.listdir('campaign-data/'+str(self.campaign_number) +
                               '/dut-files'):
            files.append('campaign-data/'+str(self.campaign_number) +
                         '/dut-files/'+item)
        self.debugger.dut.send_files(files)

    def send_aux_files(self):
        files = []
        for item in os.listdir('campaign-data/'+str(self.campaign_number) +
                               '/aux-files'):
            files.append('campaign-data/'+str(self.campaign_number) +
                         '/aux-files/'+item)
        self.debugger.aux.send_files(files)

    def get_result_id(self):
        sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
        sql = sql_db.cursor()
        sql.execute('INSERT INTO drseus_logging_result (campaign_id,iteration'
                    ',outcome,outcome_category,timestamp) VALUES (?,?,?,?,?)',
                    (self.campaign_number, self.iteration, 'In progress',
                     'Incomplete', datetime.now()))
        sql_db.commit()
        result_id = sql.lastrowid
        sql_db.close()
        return result_id

    def inject_faults(self, num_injections, selected_targets, compare_all):
        if self.use_simics:
            checkpoint_nums = range(self.num_checkpoints-1)
            injected_checkpoint_nums = []
            for i in xrange(num_injections):
                checkpoint_num = random.choice(checkpoint_nums)
                checkpoint_nums.remove(checkpoint_num)
                injected_checkpoint_nums.append(checkpoint_num)
            injected_checkpoint_nums = sorted(injected_checkpoint_nums)
            return self.debugger.inject_fault(self.result_id, self.iteration,
                                              injected_checkpoint_nums,
                                              selected_targets,
                                              self.cycles_between,
                                              self.num_checkpoints,
                                              compare_all)
        else:
            injection_times = []
            for i in xrange(num_injections):
                injection_times.append(random.uniform(0, self.exec_time))
            injection_times = sorted(injection_times)
            self.debugger.inject_fault(self.result_id, self.iteration,
                                       injection_times, self.command,
                                       selected_targets)
            return 0

    def check_output(self, output_file, use_aux_output):
        missing_output = False
        data_diff = -1.0
        os.makedirs('campaign-data/'+str(self.campaign_number)+'/results/' +
                    str(self.iteration))
        result_folder = ('campaign-data/'+str(self.campaign_number) +
                         '/results/'+str(self.iteration))
        output_location = result_folder+'/'+output_file
        gold_location = ('campaign-data/'+str(self.campaign_number)+'/gold_' +
                         output_file)
        if use_aux_output:
            self.debugger.aux.get_file(output_file, output_location)
        else:
            self.debugger.dut.get_file(output_file, output_location)
        if not os.listdir(result_folder):
            os.rmdir(result_folder)
            missing_output = True
        else:
            with open(gold_location, 'r') as solution:
                solutionContents = solution.read()
            with open(output_location, 'r') as result:
                resultContents = result.read()
            data_diff = SequenceMatcher(None, solutionContents,
                                        resultContents).quick_ratio()
            if data_diff == 1.0:
                os.remove(output_location)
                if not os.listdir(result_folder):
                    os.rmdir(result_folder)
        try:
            if use_aux_output:
                self.debugger.aux.command('rm '+output_file)
            else:
                self.debugger.dut.command('rm '+output_file)
        except DrSEUSError as error:
            raise DrSEUSError(error.type)
        if missing_output:
            raise DrSEUSError(DrSEUSError.missing_output)
        return data_diff

    def monitor_execution(self, latent_faults, output_file, use_aux_output):
        buff = ''
        aux_buff = ''
        detected_errors = 0
        data_diff = -1.0
        outcome = ''
        outcome_category = ''
        if self.use_aux:
            try:
                aux_buff = self.debugger.aux.read_until()
            except DrSEUSError as error:
                self.debugger.dut.serial.write('\x03')
                outcome = error.type
                outcome_category = 'AUX execution error'
            else:
                if self.kill_dut:
                    self.debugger.dut.serial.write('\x03')
        try:
            buff = self.debugger.dut.read_until()
        except DrSEUSError as error:
            outcome = error.type
            outcome_category = 'Execution error'
        for line in buff.split('\n'):
            if 'drseus_detected_errors:' in line:
                detected_errors = int(line.replace(
                                      'drseus_detected_errors:', ''))
                break
        if self.use_aux:
            for line in aux_buff.split('\n'):
                if 'drseus_detected_errors:' in line:
                    detected_errors += int(line.replace(
                                           'drseus_detected_errors:', ''))
                    break
        if output_file and not outcome:
            try:
                data_diff = self.check_output(output_file, use_aux_output)
            except DrSEUSError as error:
                if error.type == DrSEUSError.missing_output:
                    outcome = error.type
                    outcome_category = 'SCP error'
                else:
                    outcome = error.type
                    outcome_category = 'Post execution error'
        if not outcome:
            if detected_errors > 0:
                outcome = 'Detected data error'
                outcome_category = 'Data error'
            elif data_diff < 1.0 and data_diff != -1.0:
                outcome = 'Silent data error'
                outcome_category = 'Data error'
            elif latent_faults:
                outcome = 'Latent faults'
                outcome_category = 'No error'
            else:
                outcome = 'No error'
                outcome_category = 'No error'
        return outcome, outcome_category, detected_errors, data_diff

    def log_result(self, outcome, outcome_category, detected_errors, data_diff):
        print(colored('iteration '+str(self.iteration)+' outcome: ' +
                      outcome_category+' - '+outcome, 'blue'), end='')
        if data_diff < 1.0 and data_diff != -1.0:
            print(colored(', data diff: '+str(data_diff), 'blue'))
        else:
            print()
        sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
        sql = sql_db.cursor()
        sql.execute(
            'UPDATE drseus_logging_result SET outcome=?,outcome_category=?,'
            'data_diff=?,detected_errors=?,dut_output=?,aux_output=?,'
            'debugger_output=?,paramiko_output=?,aux_paramiko_output=?,'
            'timestamp=? WHERE id=?', (
                outcome, outcome_category, data_diff, detected_errors,
                self.debugger.dut.output.decode('utf-8', 'ignore') if
                self.debugger.dut is not None else '',
                self.debugger.aux.output.decode('utf-8', 'ignore') if
                self.use_aux and self.debugger.aux is not None else '',
                self.debugger.output,
                self.debugger.dut.paramiko_output if
                self.debugger.dut is not None else '',
                self.debugger.aux.paramiko_output if
                self.use_aux and self.debugger.aux is not None else '',
                datetime.now(), self.result_id
            )
        )
        sql_db.commit()
        sql_db.close()

    def inject_and_monitor(self, iteration_counter, last_iteration,
                           num_injections, selected_targets, output_file,
                           use_aux_output, compare_all):
        if self.use_aux and not self.use_simics:
            self.send_aux_files()
        while True:
            with iteration_counter.get_lock():
                self.iteration = iteration_counter.value
                iteration_counter.value += 1
            if self.iteration >= last_iteration:
                break
            self.result_id = self.get_result_id()
            if not self.use_simics:
                self.debugger.reset_dut()
                self.debugger.dut.do_login()
                self.send_dut_files()
            if self.use_aux and not self.use_simics:
                self.debugger.aux.serial.write('./'+self.aux_command+'\n')
            try:
                latent_faults = self.inject_faults(num_injections,
                                                   selected_targets,
                                                   compare_all)
                self.debugger.continue_dut()
            except DrSEUSError as error:
                outcome = error.type
                if self.use_simics:
                    outcome_category = 'Simics error'
                else:
                    outcome_category = 'Debugger error'
                    if not self.use_simics:
                        try:
                            self.debugger.continue_dut()
                            if self.use_aux:
                                aux_process = Thread(
                                    target=self.debugger.aux.read_until)
                                aux_process.start()
                            self.debugger.dut.read_until()
                            if self.use_aux:
                                aux_process.join()
                        except:
                            pass
                data_diff = -1.0
                detected_errors = 0
            else:
                (outcome, outcome_category, detected_errors,
                 data_diff) = self.monitor_execution(latent_faults, output_file,
                                                     use_aux_output)
                if outcome == 'Latent faults' or (not self.use_simics
                                                  and outcome == 'No error'):
                    if self.use_aux:
                        self.debugger.aux.serial.write('./'+self.aux_command +
                                                       '\n')
                    self.debugger.dut.serial.write('./'+self.command+'\n')
                    next_outcome = self.monitor_execution(0, output_file,
                                                          use_aux_output)[0]
                    if next_outcome != 'No error':
                        outcome = next_outcome
                        outcome_category = 'Post execution error'
                    elif self.use_simics:
                        if self.debugger.persistent_faults(self.result_id):
                            outcome = 'Persistent faults'
            if self.use_simics:
                try:
                    self.debugger.close()
                except DrSEUSError as error:
                    outcome = error.type
                    outcome_category = 'Simics error'
                finally:
                    shutil.rmtree('simics-workspace/injected-checkpoints/' +
                                  str(self.campaign_number)+'/' +
                                  str(self.iteration))
            self.log_result(outcome, outcome_category, detected_errors,
                            data_diff)
            self.debugger.output = ''
            self.debugger.dut.output = ''
            self.debugger.dut.paramiko_output = ''
            if self.use_aux:
                self.debugger.aux.output = ''
                self.debugger.aux.paramiko_output = ''
        self.close()

    def supervise(self, starting_iteration, run_time, output_file,
                  use_aux_output, packet_capture):
        iterations = int(run_time / self.exec_time)
        print(colored('performing '+str(iterations)+' iterations', 'blue'))
        if self.use_simics:
            self.debugger.launch_simics('gold-checkpoints/' +
                                        str(self.campaign_number)+'/' +
                                        str(self.num_checkpoints-1)+'_merged')
            self.debugger.continue_dut()
        if not self.use_simics:
            self.send_dut_files()
            if self.use_aux:
                self.send_aux_files()
        for iteration in xrange(starting_iteration,
                                starting_iteration + iterations):
            result_id = self.get_result_id(iteration)
            # create empty injection, used for injection charts in log viewer
            sql_db = sqlite3.connect('campaign-data/db.sqlite3', timeout=60)
            sql = sql_db.cursor()
            sql.execute(
                'INSERT INTO drseus_logging_injection (result_id,'
                'injection_number,timestamp) VALUES (?,?,?)',
                (
                    result_id, 0, datetime.now()
                )
            )
            sql_db.commit()
            sql_db.close()
            if packet_capture:
                data_dir = ('campaign-data/'+str(self.campaign_number) +
                            '/results/'+str(iteration))
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
            if self.use_aux:
                self.debugger.aux.serial.write('./'+self.aux_command+'\n')
            self.debugger.dut.serial.write('./'+self.command+'\n')
            (outcome, outcome_category, detected_errors,
             data_diff) = self.monitor_execution(iteration, 0, output_file,
                                                 use_aux_output)
            self.log_result(result_id, iteration, outcome, outcome_category,
                            detected_errors, data_diff)
            if packet_capture:
                import time
                time.sleep(5)
                os.system('ssh p2020 \'killall tshark\'')
                capture_process.wait()
                capture_file.close()
            self.debugger.dut.output = ''
            self.debugger.dut.paramiko_output = ''
            if self.use_aux:
                self.debugger.aux.output = ''
                self.debugger.aux.paramiko_output = ''
        if self.use_simics:
            self.debugger.close()
        self.close()
