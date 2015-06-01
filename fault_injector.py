from __future__ import print_function
import os
import sys
import difflib
import pickle
import random
import time
from socket import error as SocketError

import paramiko
from scp import SCPException

from error import DrSEUSError
from dut import dut
from bdi import bdi_p2020, bdi_arm
from simics import simics
import checkpoint_injection


class fault_injector:
    # setup dut and debugger
    # TODO: move dut into debugger
    def __init__(self, dut_ip_address='10.42.0.20',
                 dut_serial_port='/dev/ttyUSB0',
                 debugger_ip_address='10.42.0.50',
                 architecture='p2020', use_simics=False, new=True, debug=True):
        if not os.path.exists('campaign-data'):
            os.mkdir('campaign-data')
        self.architecture = architecture
        self.simics = use_simics
        self.debug = debug
        if new:
            if use_simics:
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
            self.dut.rsakey = paramiko.RSAKey.generate(1024)
            with open('campaign-data/private.key', 'w') as keyfile:
                self.dut.rsakey.write_private_key(keyfile)
            self.dut.do_login(change_prompt=use_simics)
            if use_simics:
                self.dut.command('ifconfig eth0 '+dut_ip_address +
                                 ' netmask 255.255.255.0 up')
                self.dut.command('')
        elif not use_simics:  # continuing bdi campaign
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
                self.dut.rsakey = paramiko.RSAKey.from_private_key(keyfile)

    def exit(self):
        if not self.simics:
            self.debugger.close()
            self.dut.close()
        sys.exit()

    def setup_campaign(self, directory, application, arguments, output_file,
                       additional_files, iterations, num_checkpoints):
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
        try:
            self.dut.send_files(files)
        except SocketError:
            print('could not connect to dut over ssh')
            sys.exit()
        self.exec_time = self.time_application(5)
        try:
            self.dut.get_file(self.output_file,
                              'campaign-data/gold_'+self.output_file)
        except SCPException:
            print ('could not get gold output file from dut')
            import pdb; pdb.set_trace()
            sys.exit()
        campaign = {
            'application': self.application,
            'output_file': self.output_file,
            'command': self.command,
            'architecture': self.architecture,
            'use_simics': self.simics,
        }
        if self.simics:
            self.cycles_between = self.debugger.create_checkpoints(
                self.command, self.exec_time, num_checkpoints)
            campaign['board'] = self.board
            campaign['num_checkpoints'] = num_checkpoints
            campaign['cycles_between'] = self.cycles_between
            campaign['dut_output'] = self.dut.output
            campaign['debugger_output'] = self.debugger.output
        else:
            campaign['exec_time'] = self.exec_time
        with open('campaign-data/campaign.pickle', 'w') as campaign_pickle:
            pickle.dump(campaign, campaign_pickle)

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

    def inject_fault(self, injection_number):
        if not os.path.exists('campaign-data/results'):
            os.mkdir('campaign-data/results')
        os.mkdir('campaign-data/results/'+str(injection_number))
        if self.simics:
            # TODO: try moving this all to simics() and update "self" with new instance
            self.injected_checkpoint = checkpoint_injection.InjectCheckpoint(
                injectionNumber=injection_number, selectedTargets=['GPR'])
            self.debugger = simics(new=False,
                                   checkpoint=self.injected_checkpoint)
            self.dut = self.debugger.dut
            with open('campaign-data/private.key') as keyfile:
                self.dut.rsakey = paramiko.RSAKey.from_private_key(keyfile)
        else:
            injection_time = random.uniform(0, self.exec_time)
            if self.debug:
                print('injection at:', injection_time)
            self.injection_data = self.debugger.inject_fault(
                injection_time, self.command)

    def monitor_execution(self, injection_number):
        self.outcome = None
        if self.simics:
            self.simics_results = self.debugger.compare_checkpoints(
                self.injected_checkpoint, self.cycles_between, 50)
        self.debugger.continue_dut()
        try:
            self.dut.read_until(self.dut.prompt)
        except DrSEUSError as error:
            self.outcome = error.type
        self.data_diff = None
        data_error = False
        if self.outcome is None:
            try:
                output_location = ('campaign-data/results/' +
                                   str(injection_number)+'/'+self.output_file)
                gold_location = 'campaign-data/gold_'+self.output_file
                self.dut.get_file(self.output_file, output_location)
            except paramiko.ssh_exception.AuthenticationException:
                missing_output = True
                print('could not create ssh connection')
            except SCPException:
                missing_output = True
                print('could not get output file')
            else:
                missing_output = False
                with open(gold_location, 'r') as solution:
                    solutionContents = solution.read()
                with open(output_location, 'r') as result:
                    resultContents = result.read()
                self.data_diff = difflib.SequenceMatcher(
                    None, solutionContents, resultContents).quick_ratio()
                data_error = self.data_diff < 1.0
            if missing_output:
                self.outcome = 'missing output'
            elif data_error:
                self.outcome = 'data error'
            else:
                self.outcome = 'no error'
        if self.debug:
            print('\noutcome:', self.outcome, '\n')
        if self.simics:
            self.debugger.close()

    def log_injection(self, injection_number):
        with open('campaign-data/campaign.pickle', 'r') as campaign_pickle:
            campaign_data = pickle.load(campaign_pickle)
        if self.simics:
            with open('simics-workspace/'+self.injected_checkpoint +
                      '/InjectionData.pickle', 'r') as injection_data_pickle:
                self.injection_data = pickle.load(injection_data_pickle)
        log = {
            'injection_data': self.injection_data,
            'dut_output': self.dut.output,
            'debugger_output': self.debugger.output,
            'data_diff': self.data_diff,
            'outcome': self.outcome,
        }
        if self.simics:
            log['checkpoint_comparisons'] = self.simics_results
            log['dut_output_previous'] = campaign_data['dut_output']
            log['debugger_output_previous'] = campaign_data['debugger_output']
        if not os.path.exists('campaign-data/results'):
            os.mkdir('campaign-data/results')
        with open('campaign-data/results/'+str(injection_number)+'/log.pickle',
                  'w') as log_pickle:
            pickle.dump(log, log_pickle)
