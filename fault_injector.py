from difflib import SequenceMatcher
import os
from paramiko import RSAKey
from shutil import copy, rmtree
from subprocess import PIPE, Popen
from termcolor import colored
from threading import Thread
from time import sleep

from error import DrSEUsError
from jtag import bdi_p2020, openocd
from simics import simics
from sql import sql


class fault_injector(object):
    def __init__(self, campaign_data, options):
        self.campaign_data = campaign_data
        self.options = options
        self.result_data = {'campaign_id': self.campaign_data['id'],
                            'aux_output': '',
                            'data_diff': None,
                            'debugger_output': '',
                            'detected_errors': None,
                            'dut_output': ''}
        if os.path.exists(
                'campaign-data/'+str(campaign_data['id'])+'/private.key'):
            self.rsakey = RSAKey.from_private_key_file(
                'campaign-data/'+str(campaign_data['id'])+'/private.key')
        else:
            self.rsakey = RSAKey.generate(1024)
            self.rsakey.write_private_key_file(
                'campaign-data/'+str(campaign_data['id'])+'/private.key')
        if self.campaign_data['use_simics']:
            self.debugger = simics(campaign_data, self.result_data, options,
                                   self.rsakey)
        else:
            if campaign_data['architecture'] == 'p2020':
                self.debugger = bdi_p2020(campaign_data, self.result_data,
                                          options, self.rsakey)
            elif campaign_data['architecture'] == 'a9':
                self.debugger = openocd(campaign_data, self.result_data,
                                        options, self.rsakey)
        if not self.campaign_data['use_simics']:
            if self.campaign_data['use_aux']:
                self.debugger.aux.serial.write('\x03')
                self.debugger.aux.do_login()
                if options.command != 'new':
                    self.send_dut_files(aux=True)
            if options.command == 'new':
                self.debugger.reset_dut()

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
        string += ('\n\t\t' +
                   ('Host 'if self.campaign_data['use_simics'] else '') +
                   'Execution Time: ' +
                   str(self.campaign_data['exec_time'])+' seconds')
        if self.campaign_data['use_simics']:
            string += ('\n\t\tExecution Cycles: ' +
                       '{:,}'.format(self.campaign_data['num_cycles']) +
                       ' cycles\n\t\tSimulated Time: ' +
                       str(self.campaign_data['sim_time'])+' seconds')
        return string

    def close(self):
        if not self.campaign_data['use_simics']:
            self.debugger.close()

    def setup_campaign(self):
        files = []
        files.append(self.options.directory+'/'+self.options.application)
        if self.options.files:
            for file_ in self.options.files:
                files.append(self.options.directory+'/'+file_)
        os.makedirs('campaign-data/'+str(self.campaign_data['id'])+'/dut-files')
        for item in files:
            copy(item, 'campaign-data/'+str(self.campaign_data['id']) +
                       '/dut-files/')
        if self.campaign_data['use_aux']:
            aux_files = []
            aux_files.append(self.options.directory+'/' +
                             self.options.aux_application)
            if self.options.aux_files:
                for file_ in self.options.aux_files:
                    aux_files.append(
                        self.options.directory+'/'+file_)
            os.makedirs('campaign-data/'+str(self.campaign_data['id']) +
                        '/aux-files')
            for item in aux_files:
                copy(item, 'campaign-data/'+str(self.campaign_data['id']) +
                           '/aux-files/')
            aux_process = Thread(target=self.debugger.aux.send_files,
                                 args=(aux_files, ))
            aux_process.start()
        self.debugger.dut.send_files(files)
        if self.campaign_data['use_aux']:
            aux_process.join()
            aux_process = Thread(target=self.debugger.aux.command)
            aux_process.start()
        self.debugger.dut.command()
        if self.campaign_data['use_aux']:
            aux_process.join()
        self.debugger.time_application()
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
        with sql() as db:
            db.update_dict('campaign', self.campaign_data)
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

    def create_result(self, num_injections=0, outcome_category='Incomplete',
                      outcome='Incomplete'):
        self.result_data.update({'aux_output': '',
                                 'data_diff': None,
                                 'debugger_output': '',
                                 'detected_errors': None,
                                 'dut_output': '',
                                 'num_injections': num_injections,
                                 'outcome_category': outcome_category,
                                 'outcome': outcome,
                                 'timestamp': None})
        if 'id' in self.result_data:
            del self.result_data['id']
        with sql() as db:
            db.insert_dict('result', self.result_data)
            self.result_data['id'] = db.cursor.lastrowid
            db.insert_dict('injection', {'result_id': self.result_data['id'],
                                         'injection_number': 0})

    def __monitor_execution(self, latent_faults=0, persistent_faults=False):

        def check_output():
            missing_output = False
            result_folder = ('campaign-data/'+str(self.campaign_data['id'])+'/'
                             'results/'+str(self.result_data['id']))
            os.makedirs(result_folder)
            output_location = \
                result_folder+'/'+self.campaign_data['output_file']
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
                with open(gold_location, 'rb') as solution:
                    solutionContents = solution.read()
                with open(output_location, 'rb') as result:
                    resultContents = result.read()
                self.result_data['data_diff'] = SequenceMatcher(
                    None, solutionContents, resultContents).quick_ratio()
                if self.result_data['data_diff'] == 1.0:
                    os.remove(output_location)
                    if not os.listdir(result_folder):
                        os.rmdir(result_folder)
            if self.campaign_data['use_aux_output']:
                self.debugger.aux.command('rm ' +
                                          self.campaign_data['output_file'])
            else:
                self.debugger.dut.command('rm ' +
                                          self.campaign_data['output_file'])
            if missing_output:
                raise DrSEUsError(DrSEUsError.missing_output)

    # def __monitor_execution(self, latent_faults=0, persistent_faults=False):
        outcome = ''
        outcome_category = ''
        if self.campaign_data['use_aux']:
            try:
                aux_buff = self.debugger.aux.read_until()
            except DrSEUsError as error:
                aux_buff = ''
                self.debugger.dut.serial.write('\x03')
                outcome = error.type
                outcome_category = 'AUX execution error'
            else:
                if self.campaign_data['kill_dut']:
                    self.debugger.dut.serial.write('\x03')
        try:
            buff = self.debugger.dut.read_until()
        except DrSEUsError as error:
            buff = ''
            outcome = error.type
            outcome_category = 'Execution error'
        for line in buff.split('\n'):
            if 'drseus_detected_errors:' in line:
                self.result_data['detected_errors'] = \
                    int(line.replace('drseus_detected_errors:', ''))
                break
        if self.campaign_data['use_aux']:
            for line in aux_buff.split('\n'):
                if 'drseus_detected_errors:' in line:
                    if self.result_data['detected_errors'] is None:
                        self.result_data['detected_errors'] = 0
                    self.result_data['detected_errors'] += \
                        int(line.replace('drseus_detected_errors:', ''))
                    break
        if self.campaign_data['output_file'] and not outcome:
            try:
                check_output()
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
            if self.result_data['detected_errors']:
                if self.result_data['data_diff'] is None or \
                        self.result_data['data_diff'] < 1.0:
                    outcome = 'Detected data error'
                    outcome_category = 'Data error'
                elif self.result_data['data_diff'] is not None and \
                        self.result_data['data_diff'] == 1:
                    outcome = 'Corrected data error'
                    outcome_category = 'Data error'
            elif self.result_data['data_diff'] is not None and \
                    self.result_data['data_diff'] < 1.0:
                outcome = 'Silent data error'
                outcome_category = 'Data error'
            elif persistent_faults:
                outcome = 'Persistent faults'
                outcome_category = 'No error'
            elif latent_faults:
                outcome = 'Latent faults'
                outcome_category = 'No error'
            else:
                outcome = 'Masked faults'
                outcome_category = 'No error'
        return outcome, outcome_category

    def log_result(self):
        out = ''
        try:
            out += self.debugger.dut.serial.port+' '
        except AttributeError:
            pass
        out += (str(self.result_data['id'])+': ' +
                self.result_data['outcome_category']+' - ' +
                self.result_data['outcome'])
        if self.result_data['data_diff'] is not None and \
                self.result_data['data_diff'] < 1.0:
            out += ' {0:.2f}%'.format(max(self.result_data['data_diff']*100,
                                          99.99))
        print(colored(out, 'blue'))
        with sql() as db:
            db.cursor.execute('SELECT COUNT(*) FROM log_injection '
                              'WHERE result_id=?', (self.result_data['id'],))
            if db.cursor.fetchone()[0] > 1:
                db.cursor.execute('DELETE FROM log_injection WHERE '
                                  'result_id=? AND injection_number=0',
                                  (self.result_data['id'],))
            db.update_dict('result', self.result_data)

    def inject_and_monitor(self, iteration_counter):
        while True:
            if iteration_counter is not None:
                with iteration_counter.get_lock():
                    iteration = iteration_counter.value
                    if iteration:
                        iteration_counter.value -= 1
                    else:
                        break
            self.create_result(self.options.injections)
            if not self.campaign_data['use_simics']:
                attempts = 10
                for attempt in range(attempts):
                    try:
                        self.debugger.reset_dut()
                    except Exception as error:
                        with sql() as db:
                            db.log_event_exception(
                                self.result_data['id'],
                                'Debugger',  # TODO: update source
                                'Error resetting DUT')
                        print(colored(
                            self.debugger.dut.serial.port+' ' +
                            str(self.result_data['id'])+': '
                            'Error resetting DUT (attempt '+str(attempt+1) +
                            '/'+str(attempts)+'): '+str(error), 'red'))
                        if attempt < attempts-1:
                            sleep(30)
                        else:
                            self.result_data.update({
                                'outcome_category': 'Debugger error',
                                'outcome': 'Error resetting dut'})
                            self.log_result()
                            self.close()
                            return
                    else:
                        break
                try:
                    self.send_dut_files()
                except DrSEUsError as error:
                    self.result_data.update({
                        'outcome_category': error.type,
                        'outcome': 'Error sending files to DUT'})
                    self.log_result()
                    continue
            if self.campaign_data['use_aux'] and \
                    not self.campaign_data['use_simics']:
                self.debugger.aux.write('./'+self.campaign_data['aux_command'] +
                                        '\n')
            try:
                latent_faults, persistent_faults = self.debugger.inject_faults()
                self.debugger.continue_dut()
            except DrSEUsError as error:
                self.result_data['outcome'] = error.type
                if self.campaign_data['use_simics']:
                    self.result_data['outcome_category'] = 'Simics error'
                else:
                    self.result_data['outcome_category'] = 'Debugger error'
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
                (self.result_data['outcome'],
                 self.result_data['outcome_category']) = \
                    self.__monitor_execution(latent_faults, persistent_faults)
                if self.result_data['outcome'] == 'Latent faults' or \
                    (not self.campaign_data['use_simics'] and
                        self.result_data['outcome'] == 'Masked faults'):
                    if self.campaign_data['use_aux']:
                        self.debugger.aux.write(
                            './'+self.campaign_data['aux_command']+'\n')
                    self.debugger.dut.write('./'+self.campaign_data['command'] +
                                            '\n')
                    next_outcome = self.__monitor_execution()[0]
                    if next_outcome != 'Masked faults':
                        self.result_data.update({
                            'outcome_category': 'Post execution error',
                            'outcome': next_outcome})
            if self.campaign_data['use_simics']:
                try:
                    self.debugger.close()
                except DrSEUsError as error:
                    self.result_data.update({
                        'outcome_category': 'Simics error',
                        'outcome': error.type})
                finally:
                    rmtree('simics-workspace/injected-checkpoints/' +
                           str(self.campaign_data['id'])+'/' +
                           str(self.result_data['id']))
            self.log_result()
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
                            '/results/'+str(self.result_data['id']))
                os.makedirs(data_dir)
                capture_file = open(data_dir+'/capture.pcap', 'w')
                capture_process = Popen(
                    ['ssh', 'p2020', 'tshark -F pcap -i eth1 -w -'],
                    stderr=PIPE, stdout=capture_file)
                buff = ''
                while True:
                    buff += capture_process.stderr.read(1)
                    if buff[-len('Capturing on \'eth1\''):] == \
                            'Capturing on \'eth1\'':
                        break
            if self.campaign_data['use_aux']:
                self.debugger.aux.write('./'+self.campaign_data['aux_command'] +
                                        '\n')
            self.debugger.dut.write('./'+self.campaign_data['command']+'\n')
            try:
                (self.result_data['outcome'],
                 self.result_data['outcome_category']) = \
                    self.__monitor_execution()
            except KeyboardInterrupt:
                if self.campaign_data['use_simics']:
                    self.debugger.continue_dut()
                self.debugger.dut.serial.write('\x03')
                self.debugger.dut.read_until()
                if self.campaign_data['use_aux']:
                    self.debugger.aux.serial.write('\x03')
                    self.debugger.aux.read_until()
                self.result_data.update({
                    'outcome_category': 'Incomplete',
                    'outcome': 'Interrupted'})
                interrupted = True
            self.log_result()
            if packet_capture:
                os.system('ssh p2020 \'killall tshark\'')
                capture_process.wait()
                capture_file.close()
