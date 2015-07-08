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
                 use_aux, new, debug, use_simics, num_checkpoints, compare_all):
        if not os.path.exists('campaign-data'):
            os.mkdir('campaign-data')
        self.architecture = architecture
        self.use_simics = use_simics
        self.compare_all = compare_all
        self.use_aux = use_aux
        self.debug = debug
        if os.path.exists('campaign-data/private.key'):
            self.rsakey = RSAKey.from_private_key_file(
                'campaign-data/private.key')
        else:
            self.rsakey = RSAKey.generate(1024)
            self.rsakey.write_private_key_file('campaign-data/private.key')
        if self.use_simics:
            self.num_checkpoints = num_checkpoints
            self.debugger = simics(architecture, self.rsakey, use_aux, new,
                                   debug)
            if architecture == 'p2020':
                self.board = 'p2020rdb'
            elif architecture == 'arm':
                self.board = 'a9x4'
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

    def setup_campaign(self, directory, application, arguments, output_file,
                       additional_files, iterations, aux_application,
                       aux_arguments, use_aux_output):
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
        files = []
        files.append(directory+'/'+application)
        if self.use_aux:
            aux_files = []
            aux_files.append('fiapps/'+aux_application)
            files.append(directory+'/'+aux_application)
        if additional_files:
            for item in additional_files.split(','):
                files.append(directory+'/'+item.lstrip().rstrip())
                if self.use_aux:
                    aux_files.append(directory+'/'+item.lstrip().rstrip())
        if self.debug:
            print(colored('sending files...', 'blue'), end='')
        if self.use_aux:
            aux_process = multiprocessing.Process(
                target=self.debugger.aux.send_files, args=(aux_files, ))
            aux_process.start()
        self.debugger.dut.send_files(files)
        if self.use_aux:
            aux_process.join()
        if self.debug:
            print(colored('files sent', 'blue'))
        self.exec_time = self.debugger.time_application(
            self.command, self.aux_command, iterations)
        if use_aux_output:
            self.debugger.aux.get_file(output_file,
                                       'campaign-data/gold_'+output_file)
        else:
            self.debugger.dut.get_file(output_file,
                                       'campaign-data/gold_'+output_file)
        if self.debug:
            print()
        sql_db = sqlite3.connect('campaign-data/db.sqlite3')
        sql = sql_db.cursor()
        sql.execute(
            'INSERT INTO drseus_logging_campaign_data ' +
            '(application,output_file,command,aux_command,use_aux,exec_time,'
            'architecture,use_simics) VALUES (?,?,?,?,?,?,?,?)',
            (
                application, output_file, self.command, self.aux_command,
                self.use_aux, self.exec_time, self.architecture, self.use_simics
            )
        )
        if self.use_simics:
            self.cycles_between = self.debugger.create_checkpoints(
                self.command, self.aux_command, self.exec_time,
                self.num_checkpoints, self.compare_all)
            sql.execute(
                'INSERT INTO drseus_logging_simics_campaign_data ' +
                '(board,num_checkpoints,cycles_between,dut_output,' +
                'debugger_output) VALUES (?,?,?,?,?)',
                (
                    self.board, self.num_checkpoints,
                    self.cycles_between,
                    self.debugger.dut.output.decode('utf-8', 'ignore'),
                    self.debugger.output.decode('utf-8', 'ignore')
                )
            )
        sql_db.commit()
        sql_db.close()
        if not self.use_simics:
            os.mkdir('campaign-data/dut-files')
            for item in files:
                shutil.copy(item, 'campaign-data/dut-files/')

    def inject_fault(self, injection_number, selected_targets):
        if self.use_aux:
            self.debugger.aux.serial.write('./'+self.aux_command+'\n')
        if self.use_simics:
            checkpoint_number = random.randrange(self.num_checkpoints-1)
            self.injected_checkpoint = \
                self.debugger.inject_fault(injection_number, checkpoint_number,
                                           self.board, selected_targets)
        else:
            self.debugger.reset_dut()
            self.debugger.dut.do_login()
            files = []
            for item in os.listdir('campaign-data/dut-files'):
                files.append('campaign-data/dut-files/'+item)
            self.debugger.dut.send_files(files)
            injection_time = random.uniform(0, self.exec_time)
            self.debugger.inject_fault(injection_number, injection_time,
                                       self.command, selected_targets)

    def monitor_execution(self, injection_number, output_file):
        if self.use_aux:
            aux_process = multiprocessing.Process(
                target=self.debugger.aux.read_until)
            aux_process.start()
        outcome = None
        data_diff = -1
        try:
            if self.use_simics:
                self.debugger.compare_checkpoints(
                    injection_number, self.injected_checkpoint, self.board,
                    self.cycles_between, self.num_checkpoints, self.compare_all)
            self.debugger.continue_dut()
        except DrSEUSError as error:
                outcome = error.type
        if outcome is None:
            try:
                self.debugger.dut.read_until()
            except DrSEUSError as error:
                outcome = error.type
            data_diff = -1
            data_error = False
            # TODO: check for detected errors
            detected_errors = 0
            if not os.path.exists('campaign-data/results'):
                os.mkdir('campaign-data/results')
            os.mkdir('campaign-data/results/'+str(injection_number))
            result_folder = 'campaign-data/results/'+str(injection_number)
            output_location = result_folder+'/'+output_file
            gold_location = 'campaign-data/gold_'+output_file
            try:
                self.debugger.dut.get_file(output_file, output_location)
            # except KeyboardInterrupt:
            #     raise KeyboardInterrupt
            except:
                missing_output = True
                if not os.listdir(result_folder):
                    os.rmdir(result_folder)
            else:
                missing_output = False
                with open(gold_location, 'r') as solution:
                    solutionContents = solution.read()
                with open(output_location, 'r') as result:
                    resultContents = result.read()
                data_diff = difflib.SequenceMatcher(
                    None, solutionContents, resultContents).quick_ratio()
                data_error = data_diff < 1.0
                if not data_error:
                    os.remove(output_location)
                    if not os.listdir(result_folder):
                        os.rmdir(result_folder)
            if outcome is None:
                if missing_output:
                    outcome = 'missing output'
                elif data_error:
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
        if self.debug:
            print()
            print(colored('outcome: '+outcome+'\n', 'blue'))
            if data_error:
                print(colored('data diff: '+str(data_diff)+'\n', 'blue'))
        sql_db = sqlite3.connect('campaign-data/db.sqlite3')
        sql = sql_db.cursor()
        sql.execute(
            'INSERT INTO drseus_logging_' +
            ('simics_result ' if self.use_simics else 'hw_result ') +
            '(injection_id,outcome,outcome_category,data_diff,' +
            'detected_errors,qty,dut_output,debugger_output) ' +
            'VALUES (?,?,?,?,?,?,?,?)', (
                injection_number, outcome, outcome_category, data_diff,
                detected_errors, 1,
                self.debugger.dut.output.decode('utf-8', 'ignore'),
                self.debugger.output.decode('utf-8', 'ignore')
            )
        )
        sql_db.commit()
        sql_db.close()

    def supervise(self):
        aux_process = multiprocessing.Process(target=self.debugger.aux.command,
                                              args=('./'+self.aux_command,))
        aux_process.start()
        self.debugger.dut.command('./'+self.command)
        print()
        aux_process.join()
