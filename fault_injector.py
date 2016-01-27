from difflib import SequenceMatcher
from os import listdir, makedirs
from shutil import copy, rmtree
from subprocess import check_call, PIPE, Popen
from termcolor import colored
from threading import Thread

from database import database
from error import DrSEUsError
from jtag import bdi_p2020, openocd
from simics import simics


class fault_injector(object):
    def __init__(self, campaign_data, options):
        self.campaign_data = campaign_data
        self.options = options
        self.result_data = {}
        self.database = database(campaign_data, self.result_data)
        if options.command != 'new':
            self.__create_result()
        if campaign_data['use_simics']:
            self.debugger = simics(campaign_data, self.result_data,
                                   self.database, options)
        else:
            if campaign_data['architecture'] == 'p2020':
                self.debugger = bdi_p2020(campaign_data, self.result_data,
                                          self.database, options)
            elif campaign_data['architecture'] == 'a9':
                self.debugger = openocd(campaign_data, self.result_data,
                                        self.database, options)
        if campaign_data['use_aux'] and not campaign_data['use_simics']:
            self.debugger.aux.serial.write('\x03')
            self.debugger.aux.do_login()
            if options.command != 'new':
                self.send_dut_files(aux=True)

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
        self.debugger.close()
        if self.result_data:
            with self.database as db:
                result_items = db.get_result_item_count('event')
                result_items += db.get_result_item_count('injection')
                result_items += db.get_result_item_count('simics_memory_diff')
                result_items += db.get_result_item_count('simics_register_diff')
            if (self.result_data['dut_output'] or
                    self.result_data['aux_output'] or
                    self.result_data['debugger_output'] or
                    result_items):
                self.result_data.update({
                    'outcome_category': 'DrSEUs',
                    'outcome': 'Closed DrSEUs'})
                self.log_result(True)
            else:
                with self.database as db:
                    db.delete_result()

    def setup_campaign(self):

        def send_dut_files(aux=False):
            files = []
            files.append(self.options.directory+'/' +
                         (self.options.aux_application if aux
                          else self.options.application))
            if self.options.files:
                for file_ in self.options.files:
                    files.append(self.options.directory+'/'+file_)
            makedirs('campaign-data/'+str(self.campaign_data['id']) +
                     ('/aux-files/' if aux else '/dut-files'))
            for file_ in files:
                copy(file_, 'campaign-data/'+str(self.campaign_data['id']) +
                            ('/aux-files/' if aux else '/dut-files'))
            if aux:
                self.debugger.aux.send_files(files)
            else:
                self.debugger.dut.send_files(files)

    # def setup_campaign(self):
        if self.campaign_data['use_aux']:
            aux_process = Thread(target=send_dut_files, args=[True])
            aux_process.start()
        if not self.campaign_data['use_simics']:
            self.debugger.reset_dut()
        send_dut_files()
        if self.campaign_data['use_aux']:
            aux_process.join()
        self.debugger.time_application()
        if self.campaign_data['output_file']:
            if self.campaign_data['use_aux_output']:
                self.debugger.aux.get_file(
                    self.campaign_data['output_file'],
                    'campaign-data/'+str(self.campaign_data['id'])+'/gold_' +
                    self.campaign_data['output_file'])
                self.debugger.aux.command('rm ' +
                                          self.campaign_data['output_file'])
            else:
                self.debugger.dut.get_file(
                    self.campaign_data['output_file'],
                    'campaign-data/'+str(self.campaign_data['id'])+'/gold_' +
                    self.campaign_data['output_file'])
                self.debugger.dut.command('rm ' +
                                          self.campaign_data['output_file'])
        self.debugger.dut.flush()
        if self.campaign_data['use_aux']:
            self.debugger.aux.flush()
        with self.database as db:
            db.update_dict('campaign')
        self.close()

    def send_dut_files(self, aux=False):
        location = 'campaign-data/'+str(self.campaign_data['id'])
        if aux:
            location += '/aux-files/'
        else:
            location += '/dut-files/'
        files = []
        for item in listdir(location):
            files.append(location+item)
        if aux:
            self.debugger.aux.send_files(files)
        else:
            self.debugger.dut.send_files(files)

    def __create_result(self):
        self.result_data.update({'campaign_id': self.campaign_data['id'],
                                 'aux_output': '',
                                 'data_diff': None,
                                 'debugger_output': '',
                                 'detected_errors': None,
                                 'dut_output': '',
                                 'num_injections': 0,
                                 'outcome_category': 'Incomplete',
                                 'outcome': 'Incomplete',
                                 'timestamp': None})
        with self.database as db:
            db.insert_dict('result')

    def __monitor_execution(self, latent_faults=0, persistent_faults=False):

        def check_output():
            try:
                if self.campaign_data['use_aux_output']:
                    directory_listing = self.debugger.aux.command('ls -l')
                else:
                    directory_listing = self.debugger.dut.command('ls -l')
            except DrSEUsError as error:
                self.result_data['outcome_category'] = 'Post execution error'
                self.result_data['outcome'] = error.type
                return
            if self.campaign_data['output_file'] not in directory_listing:
                self.result_data['outcome_category'] = 'Data error'
                self.result_data['outcome'] = 'Missing output file'
                return
            result_folder = (
                'campaign-data/'+str(self.campaign_data['id']) +
                '/results/'+str(self.result_data['id']))
            makedirs(result_folder)
            output_location = \
                result_folder+'/'+self.campaign_data['output_file']
            gold_location = (
                'campaign-data/'+str(self.campaign_data['id']) +
                '/gold_'+self.campaign_data['output_file'])
            try:
                if self.campaign_data['use_aux_output']:
                    self.debugger.aux.get_file(
                        self.campaign_data['output_file'], output_location)
                else:
                    self.debugger.dut.get_file(
                        self.campaign_data['output_file'], output_location)
            except DrSEUsError as error:
                self.result_data['outcome_category'] = 'File transfer error'
                self.result_data['outcome'] = error.type
                return
            with open(gold_location, 'rb') as solution:
                solutionContents = solution.read()
            with open(output_location, 'rb') as result:
                resultContents = result.read()
            self.result_data['data_diff'] = SequenceMatcher(
                None, solutionContents, resultContents).quick_ratio()
            if self.result_data['data_diff'] == 1.0:
                rmtree(result_folder)
                if self.result_data['detected_errors']:
                    self.result_data['outcome_category'] = 'Data error'
                    self.result_data['outcome'] = 'Corrected data error'
            else:
                self.result_data['outcome_category'] = 'Data error'
                if self.result_data['detected_errors']:
                    self.result_data['outcome'] = 'Detected data error'
                else:
                    self.result_data['outcome'] = 'Silent data error'
            try:
                if self.campaign_data['use_aux_output']:
                    self.debugger.aux.command('rm ' +
                                              self.campaign_data['output_file'])
                else:
                    self.debugger.dut.command('rm ' +
                                              self.campaign_data['output_file'])
            except DrSEUsError as error:
                self.result_data['outcome_category'] = 'Post execution error'
                self.result_data['outcome'] = error.type
                return

    # def __monitor_execution(self, latent_faults=0, persistent_faults=False):
        if self.campaign_data['use_aux']:
            try:
                self.debugger.aux.read_until()
            except DrSEUsError as error:
                self.debugger.dut.serial.write('\x03')
                self.result_data['outcome_category'] = 'AUX execution error'
                self.result_data['outcome'] = error.type
            else:
                if self.campaign_data['kill_dut']:
                    self.debugger.dut.serial.write('\x03')
        try:
            self.debugger.dut.read_until()
        except DrSEUsError as error:
            self.result_data['outcome_category'] = 'Execution error'
            self.result_data['outcome'] = error.type
        if self.campaign_data['output_file'] and \
                self.result_data['outcome'] == 'Incomplete':
            check_output()
        if self.result_data['outcome'] == 'Incomplete':
            self.result_data['outcome_category'] = 'No error'
            if persistent_faults:
                self.result_data['outcome'] = 'Persistent faults'
            elif latent_faults:
                self.result_data['outcome'] = 'Latent faults'
            else:
                self.result_data['outcome'] = 'Masked faults'

    def log_result(self, close=False):
        self.debugger.dut.flush()
        if self.campaign_data['use_aux']:
            self.debugger.aux.flush()
        out = (self.debugger.dut.serial.port+', '+str(self.result_data['id']) +
               ': '+self.result_data['outcome_category']+' - ' +
               self.result_data['outcome'])
        if self.result_data['data_diff'] is not None and \
                self.result_data['data_diff'] < 1.0:
            out += ' {0:.2f}%'.format(max(self.result_data['data_diff']*100,
                                          99.990))
        print(colored(out, 'blue'))
        with self.database as db:
            db.update_dict('result')
        if not close:
            self.__create_result()

    def inject_campaign(self, iteration_counter):

        def prepare_dut():
            try:
                self.debugger.reset_dut()
            except DrSEUsError as error:
                self.result_data.update({
                    'outcome_category': 'Debugger error',
                    'outcome': str(error)})
                self.log_result()
                return False
            try:
                self.send_dut_files()
            except DrSEUsError as error:
                self.result_data.update({
                    'outcome_category': str(error),
                    'outcome': 'Error sending files to DUT'})
                self.log_result()
                return False
            if self.campaign_data['use_aux']:
                self.debugger.aux.write(
                    './'+self.campaign_data['aux_command']+'\n')
            return True

        def continue_dut():
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

        def close_simics():
            try:
                self.debugger.close()
            except DrSEUsError as error:
                self.result_data.update({
                    'outcome_category': 'Simics error',
                    'outcome': str(error)})
            finally:
                rmtree('simics-workspace/injected-checkpoints/' +
                       str(self.campaign_data['id'])+'/' +
                       str(self.result_data['id']))

        def check_latent_faults():
            for i in range(self.options.latent_iterations):
                if self.result_data['outcome'] == 'Latent faults' or \
                    (not self.campaign_data['use_simics'] and
                        self.result_data['outcome'] == 'Masked faults'):
                    if self.campaign_data['use_aux']:
                        self.debugger.aux.write(
                            './'+self.campaign_data['aux_command']+'\n')
                    self.debugger.dut.write(
                        './'+self.campaign_data['command']+'\n')
                    outcome_category = self.result_data['outcome_category']
                    outcome = self.result_data['outcome']
                    self.__monitor_execution()
                    if self.result_data['outcome'] != 'Masked faults':
                        self.result_data['outcome_category'] = \
                            'Post execution error'
                    else:
                        self.result_data.update({
                            'outcome_category': outcome_category,
                            'outcome': outcome})

    # def inject_campaign(self, iteration_counter):
        while True:
            if iteration_counter is not None:
                with iteration_counter.get_lock():
                    iteration = iteration_counter.value
                    if iteration:
                        iteration_counter.value -= 1
                    else:
                        break
            self.result_data['num_injections'] = self.options.injections
            if not self.campaign_data['use_simics']:
                if not prepare_dut():
                    continue
            try:
                latent_faults, persistent_faults = self.debugger.inject_faults()
                self.debugger.continue_dut()
            except DrSEUsError as error:
                self.result_data['outcome'] = str(error)
                if self.campaign_data['use_simics']:
                    self.result_data['outcome_category'] = 'Simics error'
                else:
                    self.result_data['outcome_category'] = 'Debugger error'
                    continue_dut()
            else:
                self.__monitor_execution(latent_faults, persistent_faults)
                check_latent_faults()
            if self.campaign_data['use_simics']:
                close_simics()
            self.log_result()
        self.close()

    def supervise(self, iteration_counter, packet_capture):

        def start_packet_capture():
            data_dir = ('campaign-data/'+str(self.campaign_data['id']) +
                        '/results/'+str(self.result_data['id']))
            makedirs(data_dir)
            self.capture_file = open(data_dir+'/capture.pcap', 'w')
            self.capture_process = Popen(
                ['ssh', 'p2020', 'tshark -F pcap -i eth1 -w -'],
                stderr=PIPE, stdout=self.capture_file)
            buff = ''
            while True:
                buff += self.capture_process.stderr.read(1)
                if buff[-len('Capturing on \'eth1\''):] == \
                        'Capturing on \'eth1\'':
                    break

        def end_packet_capture():
            check_call(['ssh', 'p2020', 'killall tshark'])
            self.capture_process.wait()
            self.capture_file.close()

    # def supervise(self, iteration_counter, packet_capture):
        interrupted = False
        while not interrupted:
            with iteration_counter.get_lock():
                iteration = iteration_counter.value
                if iteration:
                    iteration_counter.value -= 1
                else:
                    break
            if packet_capture:
                start_packet_capture()
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
                end_packet_capture()
