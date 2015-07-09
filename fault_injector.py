from __future__ import print_function
import os
import shutil
import sys
import difflib
import random
import sqlite3
import multiprocessing

from termcolor import colored
from paramiko import RSAKey

from error import DrSEUSError
from bdi import bdi_p2020, bdi_arm
from simics import simics


class fault_injector:
    def __init__(self, dut_ip_address, aux_ip_address, dut_serial_port,
                 aux_serial_port, debugger_ip_address, architecture,
                 use_aux, new, debug, use_simics):
        if not os.path.exists('campaign-data'):
            os.mkdir('campaign-data')
        self.use_simics = use_simics
        self.use_aux = use_aux
        self.debug = debug
        if os.path.exists('campaign-data/private.key'):
            self.rsakey = RSAKey.from_private_key_file(
                'campaign-data/private.key')
        else:
            self.rsakey = RSAKey.generate(1024)
            self.rsakey.write_private_key_file('campaign-data/private.key')
        if self.use_simics:
            self.debugger = simics(architecture, self.rsakey, use_aux, new,
                                   debug)
        else:
            if architecture == 'p2020':
                self.debugger = bdi_p2020(debugger_ip_address,
                                          dut_ip_address, self.rsakey,
                                          dut_serial_port, aux_ip_address,
                                          aux_serial_port, self.use_aux,
                                          'root@p2020rdb:~#', debug)
            elif architecture == 'arm':
                self.debugger = bdi_arm(debugger_ip_address,
                                        dut_ip_address, self.rsakey,
                                        dut_serial_port, aux_ip_address,
                                        aux_serial_port, self.use_aux,
                                        '[root@ZED]#', debug)
            if new:
                self.debugger.reset_dut()
                if self.use_aux:
                    aux_process = multiprocessing.Process(
                        target=self.debugger.aux.do_login)
                    aux_process.start()
                self.debugger.dut.do_login()
                aux_process.join()

    def exit(self):
        if not self.use_simics:
            self.debugger.close()
        sys.exit()

    def setup_campaign(self, directory, architecture, application, arguments,
                       output_file, dut_files, aux_files, iterations,
                       aux_application, aux_arguments, use_aux_output,
                       num_checkpoints):
        os.system('./django-logging/manage.py migrate')
        if arguments:
            self.command = application+' '+arguments
        else:
            self.command = application
        if self.use_aux:
            if aux_application:
                if aux_arguments:
                    self.aux_command = aux_application+' '+aux_arguments
                else:
                    self.aux_command = aux_application
            else:
                self.aux_command = self.command
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
        if self.debug:
            print(colored('sending files...', 'blue'), end='')
        if self.use_aux:
            aux_process = multiprocessing.Process(
                target=self.debugger.aux.send_files, args=(files_aux, ))
            aux_process.start()
        self.debugger.dut.send_files(files)
        if self.use_aux:
            aux_process.join()
        if self.debug:
            print(colored('files sent', 'blue'))
        self.exec_time = self.debugger.time_application(
            self.command, self.aux_command, iterations)
        if output_file:
            if use_aux_output:
                self.debugger.aux.get_file(output_file,
                                           'campaign-data/gold_'+output_file)
            else:
                self.debugger.dut.get_file(output_file,
                                           'campaign-data/gold_'+output_file)
        if self.use_simics:
            cycles_between = self.debugger.create_checkpoints(
                self.command, self.aux_command, self.exec_time, num_checkpoints)
        else:
            num_checkpoints = 0
            cycles_between = 0
        sql_db = sqlite3.connect('campaign-data/db.sqlite3')
        sql = sql_db.cursor()
        sql.execute(
            'INSERT INTO drseus_logging_campaign_data '
            '(application,output_file,command,aux_command,use_aux,'
            'use_aux_output,exec_time,architecture,use_simics,dut_output,'
            'aux_output,debugger_output,num_checkpoints, cycles_between)'
            'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (
                application, output_file, self.command, self.aux_command,
                self.use_aux, use_aux_output, self.exec_time, architecture,
                self.use_simics,
                self.debugger.dut.output.decode('utf-8', 'ignore'),
                self.debugger.aux.output.decode('utf-8', 'ignore') if
                self.use_aux else '',
                self.debugger.output.decode('utf-8', 'ignore'),
                num_checkpoints, cycles_between
            )
        )
        sql_db.commit()
        sql_db.close()
        if not self.use_simics:
            os.mkdir('campaign-data/dut-files')
            for item in files:
                shutil.copy(item, 'campaign-data/dut-files/')
            if self.use_aux:
                os.mkdir('campaign-data/aux-files')
                for item in files_aux:
                    shutil.copy(item, 'campaign-data/aux-files/')

    def inject_fault(self, injection_number, selected_targets):
        if self.use_simics:
            checkpoint_number = random.randrange(self.num_checkpoints-1)
            self.injected_checkpoint = \
                self.debugger.inject_fault(injection_number, checkpoint_number,
                                           selected_targets)
        else:
            if self.use_aux:
                def prepare_aux():
                    files_aux = []
                    for item in os.listdir('campaign-data/aux-files'):
                        files_aux.append('campaign-data/aux-files/'+item)
                    self.debugger.aux.send_files(files_aux)
                    self.debugger.aux.serial.write('./'+self.aux_command+'\n')
                aux_process = multiprocessing.Process(target=prepare_aux)
                aux_process.start()
            self.debugger.reset_dut()
            self.debugger.dut.do_login()
            files = []
            for item in os.listdir('campaign-data/dut-files'):
                files.append('campaign-data/dut-files/'+item)
            self.debugger.dut.send_files(files)
            if self.use_aux:
                aux_process.join()
            injection_time = random.uniform(0, self.exec_time)
            self.debugger.inject_fault(injection_number, injection_time,
                                       self.command, selected_targets)

    def check_output(self, number, output_file, use_aux_output):
        missing_output = False
        if not os.path.exists('campaign-data/results'):
            os.mkdir('campaign-data/results')
        os.mkdir('campaign-data/results/'+str(number))
        result_folder = 'campaign-data/results/'+str(number)
        output_location = result_folder+'/'+output_file
        gold_location = 'campaign-data/gold_'+output_file
        try:
            if use_aux_output:
                self.debugger.aux.get_file(output_file, output_location)
            else:
                self.debugger.dut.get_file(output_file, output_location)
        # except KeyboardInterrupt:
        #     raise KeyboardInterrupt
        except:
            missing_output = True
            if not os.listdir(result_folder):
                os.rmdir(result_folder)
        else:
            with open(gold_location, 'r') as solution:
                solutionContents = solution.read()
            with open(output_location, 'r') as result:
                resultContents = result.read()
            data_diff = difflib.SequenceMatcher(
                None, solutionContents, resultContents).quick_ratio()
            if data_diff == 1.0:
                os.remove(output_location)
                if not os.listdir(result_folder):
                    os.rmdir(result_folder)
        return missing_output, data_diff

    def monitor_execution(self, injection_number, output_file, use_aux_output,
                          compare_all):
        if self.use_aux:
            aux_process = multiprocessing.Process(
                target=self.debugger.aux.read_until)
            aux_process.start()
        outcome = None
        data_diff = -1.0
        detected_errors = 0
        try:
            if self.use_simics:
                self.debugger.compare_checkpoints(
                    injection_number, self.injected_checkpoint,
                    self.cycles_between, self.num_checkpoints,
                    compare_all)
            self.debugger.continue_dut()
        except DrSEUSError as error:
                outcome = error.type
        if outcome is None:
            try:
                buff = self.debugger.dut.read_until()
            except DrSEUSError as error:
                outcome = error.type
            missing_output = False
            for line in buff:
                if 'drseus_detected_errors:' in line:
                    detected_errors = int(line.replace(
                                          'drseus_detected_errors:', ''))
                    break
            if output_file:
                missing_output, data_diff = self.check_output(
                    injection_number, output_file, use_aux_output)
            if outcome is None:
                if missing_output:
                    outcome = 'missing output'
                elif detected_errors > 0:
                    outcome = 'detected data error'
                elif data_diff < 1.0 and data_diff != -1.0:
                    outcome = 'data error'
                else:
                    outcome = 'no error'
        # TODO: set outcome_category
        if self.use_aux:
            aux_process.join()
        outcome_category = 'N/A'
        if self.use_simics:
            self.debugger.close()
            shutil.rmtree('simics-workspace/'+self.injected_checkpoint)
            print(colored('outcome: '+outcome, 'blue'))
            if data_diff < 1.0 and data_diff != -1.0:
                print(colored('data diff: '+str(data_diff), 'blue'))
        sql_db = sqlite3.connect('campaign-data/db.sqlite3')
        sql = sql_db.cursor()
        sql.execute(
            'INSERT INTO drseus_logging_' +
            ('simics_result ' if self.use_simics else 'hw_result ') +
            '(injection_id,outcome,outcome_category,data_diff,'
            'detected_errors,qty,dut_output,aux_output,debugger_output) '
            'VALUES (?,?,?,?,?,?,?,?,?)', (
                injection_number, outcome, outcome_category, data_diff,
                detected_errors, 1,
                self.debugger.dut.output.decode('utf-8', 'ignore'),
                self.debugger.aux.output.decode('utf-8', 'ignore') if
                self.use_aux else '',
                self.debugger.output.decode('utf-8', 'ignore')
            )
        )
        sql_db.commit()
        sql_db.close()

    def supervise(self, iteration, output_file, use_aux_output):
        # TODO: run for specified amount of time
        if self.use_simics:
            self.debugger.launch_simics('gold-checkpoints/checkpoint-' +
                                        str(self.num_checkpoints-1)+'.ckpt')
            self.debugger.continue_dut()
        if self.use_aux:
            aux_process = multiprocessing.Process(
                target=self.debugger.aux.command, args=('./'+self.aux_command,))
            aux_process.start()

        outcome = None
        data_diff = -1.0
        missing_output = False
        try:
            buff = self.debugger.dut.command('./'+self.command)
            if self.use_aux:
                aux_process.join()
        except DrSEUSError as error:
            outcome = error.type
        detected_errors = 0
        for line in buff:
            if 'drseus_detected_errors:' in line:
                detected_errors = int(line.replace(
                                      'drseus_detected_errors:', ''))
                break
        if output_file:
            missing_output, data_diff = self.check_output(
                iteration, output_file, use_aux_output)
        if outcome is None:
            if missing_output:
                outcome = 'missing output'
            elif detected_errors > 0:
                outcome = 'detected data error'
            elif data_diff < 1.0 and data_diff != -1.0:
                outcome = 'undetected data error'
            else:
                outcome = 'no error'
        # TODO: set outcome_category
        if self.use_aux:
            aux_process.join()
        outcome_category = 'N/A'
        if self.use_simics:
            self.debugger.close()
            print(colored('outcome: '+outcome, 'blue'))
            if data_diff < 1.0 and data_diff != -1.0:
                print(colored('data diff: '+str(data_diff), 'blue'))
        sql_db = sqlite3.connect('campaign-data/db.sqlite3')
        sql = sql_db.cursor()
        sql.execute(
            'INSERT INTO drseus_logging_supervisor_result '
            '(iteration,outcome,outcome_category,data_diff,'
            'detected_errors,qty,dut_output,aux_output) ' +
            'VALUES (?,?,?,?,?,?,?,?)', (
                iteration, outcome, outcome_category, data_diff,
                detected_errors, 1,
                self.debugger.dut.output.decode('utf-8', 'ignore'),
                self.debugger.aux.output.decode('utf-8', 'ignore') if
                self.use_aux else '',
            )
        )
        sql_db.commit()
        sql_db.close()
