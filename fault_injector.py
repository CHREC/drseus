from __future__ import print_function
import os
import shutil
import sys
import difflib
import random
import time
import sqlite3
from scp import SCPException

from error import DrSEUSError
from dut import dut
from bdi import bdi_p2020, bdi_arm
from simics import simics
from checkpoint_injection import inject_checkpoint


class fault_injector:
    # setup dut and debugger
    # TODO: move dut into debugger
    def __init__(self, dut_ip_address='10.42.0.20',
                 dut_serial_port='/dev/ttyUSB0',
                 debugger_ip_address='10.42.0.50',
                 architecture='p2020', use_simics=False, new=True, debug=True,
                 num_checkpoints=50):
        if not os.path.exists('campaign-data'):
            os.mkdir('campaign-data')
        self.architecture = architecture
        self.simics = use_simics
        self.debug = debug
        if new:
            if self.simics:
                self.num_checkpoints = num_checkpoints
                self.debugger = simics(architecture=architecture)
                self.dut = self.debugger.dut
                if architecture == 'p2020':
                    self.board = 'p2020rdb'
                elif architecture == 'arm':
                    self.board = 'a9x4'
                else:
                    print('invalid architecture:', architecture)
                    sys.exit()
            else:
                if architecture == 'p2020':
                    self.dut = dut(dut_ip_address, dut_serial_port)
                    self.debugger = bdi_p2020(debugger_ip_address, self.dut)
                elif architecture == 'arm':
                    self.dut = dut(dut_ip_address, dut_serial_port,
                                   prompt='[root@ZED]#')
                    self.debugger = bdi_arm(debugger_ip_address, self.dut)
                else:
                    print('invalid architecture:', architecture)
                    sys.exit()
            self.dut.set_rsakey()
            with open('campaign-data/private.key', 'w') as keyfile:
                self.dut.rsakey.write_private_key(keyfile)
            self.dut.do_login(change_prompt=self.simics)
            if self.simics:
                self.dut.command('ifconfig eth0 '+dut_ip_address +
                                 ' netmask 255.255.255.0 up')
                self.dut.command('')
        elif not self.simics:  # continuing bdi campaign
            if architecture == 'p2020':
                self.dut = dut(dut_ip_address, dut_serial_port)
                self.debugger = bdi_p2020(debugger_ip_address, self.dut,
                                          new=False)
            elif architecture == 'arm':
                self.dut = dut(dut_ip_address, dut_serial_port,
                               prompt='[root@ZED]#')
                self.debugger = bdi_arm(debugger_ip_address, self.dut,
                                        new=False)
            # TODO: should not need this
            else:
                print('invalid architecture:', architecture)
                sys.exit()
            with open('campaign-data/private.key', 'r') as keyfile:
                self.dut.set_rsakey(keyfile)

    def exit(self):
        if not self.simics:
            self.debugger.close()
            self.dut.close()
        sys.exit()

    def setup_campaign(self, directory, application, arguments, output_file,
                       additional_files, iterations):
        os.system('./django-logging/manage.py migrate')
        self.application = application
        self.output_file = output_file
        if arguments:
            self.command = application+' '+arguments
        else:
            self.command = application
        files = []
        files.append(directory+'/'+application)
        if additional_files:
            for item in additional_files.split(','):
                files.append(directory+'/'+item.lstrip().rstrip())
        self.dut.send_files(files)
        self.exec_time = self.time_application(5)
        self.dut.get_file(
            self.output_file, 'campaign-data/gold_'+self.output_file)
        sql_db = sqlite3.connect('campaign-data/db.sqlite3')
        sql = sql_db.cursor()
        sql.execute(
            'INSERT INTO drseus_logging_campaign_data ' +
            '(application,output_file,command,exec_time,architecture,simics) ' +
            'VALUES (?,?,?,?,?,?)',
            (
                self.application, self.output_file, self.command,
                self.exec_time, self.architecture, self.simics
            )
        )
        if self.simics:
            self.cycles_between = self.debugger.create_checkpoints(
                self.command, self.exec_time, self.num_checkpoints)
            sql.execute(
                'INSERT INTO drseus_logging_simics_campaign_data ' +
                '(board,num_checkpoints,cycles_between,dut_output,' +
                'debugger_output) VALUES (?,?,?,?,?)',
                (
                    self.board, self.num_checkpoints,
                    self.cycles_between,
                    self.dut.output.decode('utf-8', 'ignore'),
                    self.debugger.output.decode('utf-8', 'ignore')
                )
            )
        sql_db.commit()
        sql_db.close()

    def time_application(self, iterations):
        if self.simics:
            for i in xrange(iterations-1):
                self.dut.command('./'+self.command)
            self.debugger.halt_dut()
            start_cycles = self.debugger.command(
                'print-time').split('\n')[-2].split()[2]
            self.debugger.continue_dut()
            self.dut.command('./'+self.command)
            self.debugger.halt_dut()
            end_cycles = self.debugger.command(
                'print-time').split('\n')[-2].split()[2]
            self.debugger.continue_dut()
            return int(end_cycles) - int(start_cycles)
        else:
            start = time.time()
            for i in xrange(iterations):
                self.dut.command('./'+self.command)
            return (time.time() - start) / iterations

    def inject_fault(self, injection_number, selected_targets=['GPR']):
        if not os.path.exists('campaign-data/results'):
            os.mkdir('campaign-data/results')
        os.mkdir('campaign-data/results/'+str(injection_number))
        if self.simics:
            # TODO: try moving this all to simics class
            self.injected_checkpoint = inject_checkpoint(
                injection_number, self.board, selected_targets,
                self.num_checkpoints
            )
            self.debugger = simics(new=False,
                                   checkpoint=self.injected_checkpoint)
            self.dut = self.debugger.dut
            with open('campaign-data/private.key') as keyfile:
                self.dut.set_rsakey(keyfile)
        else:
            injection_time = random.uniform(0, self.exec_time)
            if self.debug:
                print('injection at:', injection_time)
            self.injection_data = self.debugger.inject_fault(
                injection_time, self.command)

    def monitor_execution(self, injection_number):
        outcome = None
        if self.simics:
            self.debugger.compare_checkpoints(
                injection_number, self.injected_checkpoint, self.board,
                self.cycles_between, self.num_checkpoints)
        self.debugger.continue_dut()
        try:
            self.dut.read_until(self.dut.prompt)
        except DrSEUSError as error:
            outcome = error.type
        data_diff = 0
        data_error = False
        # TODO: check for detected errors
        detected_errors = 0
        if outcome is None:
            try:
                result_folder = 'campaign-data/results/'+str(injection_number)
                output_location = result_folder+'/'+self.output_file
                gold_location = 'campaign-data/gold_'+self.output_file
                self.dut.get_file(self.output_file, output_location)
            except KeyboardInterrupt:
                # let DrSEUS handle this
                raise KeyboardInterrupt
            except SCPException:
                missing_output = True
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
                    # TODO: remove result folder
                    os.remove(output_location)
                    if not os.listdir(result_folder):
                        os.rmdir(result_folder)
            if missing_output:
                outcome = 'missing output'
            elif data_error:
                outcome = 'data error'
            else:
                outcome = 'no error'
        # TODO: set outcome_category
        outcome_category = 'N/A'
        if self.debug:
            print('\noutcome:', outcome, '\n')
        if self.simics:
            self.debugger.close()
            shutil.rmtree('simics-workspace/'+self.injected_checkpoint)
        sql_db = sqlite3.connect('campaign-data/db.sqlite3')
        sql = sql_db.cursor()
        sql.execute(
            'INSERT INTO drseus_logging_' +
            ('simics_result ' if self.simics else 'hw_reset ') +
            '(injection_id,outcome,outcome_category,data_diff,' +
            'detected_errors,qty,dut_output,debugger_output) ' +
            'VALUES (?,?,?,?,?,?,?,?)', (
                injection_number, outcome, outcome_category, data_diff,
                detected_errors, 1, self.dut.output, self.debugger.output
            )
        )
        sql_db.commit()
        sql_db.close()
