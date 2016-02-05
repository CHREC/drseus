from difflib import SequenceMatcher
from os import listdir, makedirs
from shutil import copy, rmtree
from subprocess import check_call, PIPE, Popen
from threading import Thread

from database import database
from error import DrSEUsError
from jtag import bdi_p2020, openocd
from simics import simics


class fault_injector(object):
    def __init__(self, campaign, options):
        self.options = options
        self.db = database(campaign, options.command != 'new')
        if campaign['simics']:
            self.debugger = simics(self.db, options)
        else:
            if campaign['architecture'] == 'p2020':
                self.debugger = bdi_p2020(self.db, options)
            elif campaign['architecture'] == 'a9':
                self.debugger = openocd(self.db, options)
        if campaign['aux'] and not campaign['simics']:
            self.debugger.aux.serial.write('\x03')
            self.debugger.aux.do_login()
            if options.command != 'new':
                self.send_dut_files(aux=True)

    def __str__(self):
        string = ('DrSEUs Attributes:\n\tDebugger: '+str(self.debugger) +
                  '\n\tDUT:\t'+str(self.debugger.dut).replace('\n\t', '\n\t\t'))
        if self.db.campaign['aux']:
            string += '\n\tAUX:\t'+str(self.debugger.aux).replace('\n\t',
                                                                  '\n\t\t')
        string += ('\n\tCampaign Information:\n\t\tCampaign Number: ' +
                   str(self.db.campaign['id'])+'\n\t\tDUT Command: \"' +
                   self.db.campaign['command']+'\"')
        if self.db.campaign['aux']:
            string += \
                '\n\t\tAUX Command: \"'+self.db.campaign['aux_command']+'\"'
        string += ('\n\t\t'+('Host 'if self.db.campaign['simics'] else '') +
                   'Execution Time: '+str(self.db.campaign['exec_time']) +
                   ' seconds')
        if self.db.campaign['simics']:
            string += ('\n\t\tExecution Cycles: ' +
                       '{:,}'.format(self.db.campaign['num_cycles']) +
                       ' cycles\n\t\tSimulated Time: ' +
                       str(self.db.campaign['sim_time'])+' seconds')
        return string

    def close(self):
        self.debugger.dut.flush()
        if self.db.campaign['aux']:
            self.debugger.aux.flush()
        self.debugger.close()
        if self.db.result:
            with self.db as db:
                result_items = db.get_count('event')
                result_items += db.get_count('injection')
                result_items += db.get_count('simics_memory_diff')
                result_items += db.get_count('simics_register_diff')
            if (self.db.result['dut_output'] or
                    self.db.result['aux_output'] or
                    self.db.result['debugger_output'] or
                    result_items):
                self.db.result.update({
                    'outcome_category': 'DrSEUs',
                    'outcome': 'Closed DrSEUs'})
                with self.db as db:
                    db.log_result(True)
            else:
                with self.db as db:
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
            makedirs('campaign-data/'+str(self.db.campaign['id']) +
                     ('/aux-files/' if aux else '/dut-files'))
            for file_ in files:
                copy(file_, 'campaign-data/'+str(self.db.campaign['id']) +
                            ('/aux-files/' if aux else '/dut-files'))
            if aux:
                self.debugger.aux.send_files(files)
            else:
                self.debugger.dut.send_files(files)

    # def setup_campaign(self):
        if self.db.campaign['aux']:
            aux_process = Thread(target=send_dut_files, args=[True])
            aux_process.start()
        if not self.db.campaign['simics']:
            self.debugger.reset_dut()
            self.debugger.dut.serial.timeout = 30
            self.debugger.dut.do_login()
        send_dut_files()
        if self.db.campaign['aux']:
            aux_process.join()
        self.debugger.time_application()
        if self.db.campaign['output_file']:
            if self.db.campaign['use_aux_output']:
                self.debugger.aux.get_file(
                    self.db.campaign['output_file'],
                    'campaign-data/'+str(self.db.campaign['id'])+'/gold_' +
                    self.db.campaign['output_file'])
                self.debugger.aux.command('rm ' +
                                          self.db.campaign['output_file'])
            else:
                self.debugger.dut.get_file(
                    self.db.campaign['output_file'],
                    'campaign-data/'+str(self.db.campaign['id'])+'/gold_' +
                    self.db.campaign['output_file'])
                self.debugger.dut.command('rm ' +
                                          self.db.campaign['output_file'])
        self.debugger.dut.flush()
        if self.db.campaign['aux']:
            self.debugger.aux.flush()
        with self.db as db:
            db.update('campaign')
        self.close()

    def send_dut_files(self, aux=False):
        location = 'campaign-data/'+str(self.db.campaign['id'])
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

    def __monitor_execution(self, latent_faults=0, persistent_faults=False):

        def check_output():
            try:
                if self.db.campaign['use_aux_output']:
                    directory_listing = self.debugger.aux.command('ls -l')
                else:
                    directory_listing = self.debugger.dut.command('ls -l')
            except DrSEUsError as error:
                self.db.result['outcome_category'] = 'Post execution error'
                self.db.result['outcome'] = error.type
                return
            if self.db.campaign['output_file'] not in directory_listing:
                self.db.result['outcome_category'] = 'Data error'
                self.db.result['outcome'] = 'Missing output file'
                return
            result_folder = (
                'campaign-data/'+str(self.db.campaign['id']) +
                '/results/'+str(self.db.result['id']))
            makedirs(result_folder)
            output_location = \
                result_folder+'/'+self.db.campaign['output_file']
            gold_location = (
                'campaign-data/'+str(self.db.campaign['id']) +
                '/gold_'+self.db.campaign['output_file'])
            try:
                if self.db.campaign['use_aux_output']:
                    self.debugger.aux.get_file(
                        self.db.campaign['output_file'], output_location)
                else:
                    self.debugger.dut.get_file(
                        self.db.campaign['output_file'], output_location)
            except DrSEUsError as error:
                self.db.result['outcome_category'] = 'File transfer error'
                self.db.result['outcome'] = error.type
                if not listdir(result_folder):
                    rmtree(result_folder)
                return
            with open(gold_location, 'rb') as solution:
                solutionContents = solution.read()
            with open(output_location, 'rb') as result:
                resultContents = result.read()
            self.db.result['data_diff'] = SequenceMatcher(
                None, solutionContents, resultContents).quick_ratio()
            if self.db.result['data_diff'] == 1.0:
                rmtree(result_folder)
                if self.db.result['detected_errors']:
                    self.db.result['outcome_category'] = 'Data error'
                    self.db.result['outcome'] = 'Corrected data error'
            else:
                self.db.result['outcome_category'] = 'Data error'
                if self.db.result['detected_errors']:
                    self.db.result['outcome'] = 'Detected data error'
                else:
                    self.db.result['outcome'] = 'Silent data error'
            try:
                if self.db.campaign['use_aux_output']:
                    self.debugger.aux.command('rm ' +
                                              self.db.campaign['output_file'])
                else:
                    self.debugger.dut.command('rm ' +
                                              self.db.campaign['output_file'])
            except DrSEUsError as error:
                self.db.result['outcome_category'] = 'Post execution error'
                self.db.result['outcome'] = error.type
                return

    # def __monitor_execution(self, latent_faults=0, persistent_faults=False):
        if self.db.campaign['aux']:
            try:
                self.debugger.aux.read_until()
            except DrSEUsError as error:
                self.debugger.dut.serial.write('\x03')
                self.db.result['outcome_category'] = 'AUX execution error'
                self.db.result['outcome'] = error.type
            else:
                if self.db.campaign['kill_dut']:
                    self.debugger.dut.serial.write('\x03')
        try:
            self.debugger.dut.read_until()
        except DrSEUsError as error:
            self.db.result['outcome_category'] = 'Execution error'
            self.db.result['outcome'] = error.type
        if self.db.campaign['output_file'] and \
                self.db.result['outcome'] == 'Incomplete':
            check_output()
        if self.db.result['outcome'] == 'Incomplete':
            self.db.result['outcome_category'] = 'No error'
            if persistent_faults:
                self.db.result['outcome'] = 'Persistent faults'
            elif latent_faults:
                self.db.result['outcome'] = 'Latent faults'
            else:
                self.db.result['outcome'] = 'Masked faults'

    def inject_campaign(self, iteration_counter):

        def prepare_dut():
            try:
                self.debugger.reset_dut()
            except DrSEUsError as error:
                self.db.result.update({
                    'outcome_category': 'Debugger error',
                    'outcome': str(error)})
                with self.db as db:
                    db.log_result()
                return False
            try:
                self.debugger.dut.serial.timeout = 30
                self.debugger.dut.do_login()
            except DrSEUsError as error:
                self.db.result.update({
                    'outcome_category': 'DUT login error',
                    'outcome': str(error)})
                with self.db as db:
                    db.log_result()
                return False
            try:
                self.send_dut_files()
            except DrSEUsError as error:
                self.db.result.update({
                    'outcome_category': str(error),
                    'outcome': 'Error sending files to DUT'})
                with self.db as db:
                    db.log_result()
                return False
            if self.db.campaign['aux']:
                self.debugger.aux.write(
                    './'+self.db.campaign['aux_command']+'\n')
            return True

        def continue_dut():
            try:
                self.debugger.continue_dut()
                if self.db.campaign['aux']:
                    aux_process = Thread(
                        target=self.debugger.aux.read_until)
                    aux_process.start()
                self.debugger.dut.read_until()
                if self.db.campaign['aux']:
                    aux_process.join()
            except DrSEUsError:
                pass

        def close_simics():
            try:
                self.debugger.close()
            except DrSEUsError as error:
                self.db.result.update({
                    'outcome_category': 'Simics error',
                    'outcome': str(error)})
            finally:
                rmtree('simics-workspace/injected-checkpoints/' +
                       str(self.db.campaign['id'])+'/' +
                       str(self.db.result['id']))

        def check_latent_faults():
            for i in range(self.options.latent_iterations):
                if self.db.result['outcome'] == 'Latent faults' or \
                    (not self.db.campaign['simics'] and
                        self.db.result['outcome'] == 'Masked faults'):
                    if self.db.campaign['aux']:
                        self.debugger.aux.write(
                            './'+self.db.campaign['aux_command']+'\n')
                    self.debugger.dut.write(
                        './'+self.db.campaign['command']+'\n')
                    outcome_category = self.db.result['outcome_category']
                    outcome = self.db.result['outcome']
                    self.__monitor_execution()
                    if self.db.result['outcome'] != 'Masked faults':
                        self.db.result['outcome_category'] = \
                            'Post execution error'
                    else:
                        self.db.result.update({
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
            self.db.result['num_injections'] = self.options.injections
            if not self.db.campaign['simics']:
                if not prepare_dut():
                    continue
            try:
                latent_faults, persistent_faults = self.debugger.inject_faults()
                self.debugger.continue_dut()
            except DrSEUsError as error:
                self.db.result['outcome'] = str(error)
                if self.db.campaign['simics']:
                    self.db.result['outcome_category'] = 'Simics error'
                else:
                    self.db.result['outcome_category'] = 'Debugger error'
                    continue_dut()
            else:
                self.__monitor_execution(latent_faults, persistent_faults)
                check_latent_faults()
            self.debugger.dut.flush()
            if self.db.campaign['aux']:
                self.debugger.aux.flush()
            if self.db.campaign['simics']:
                close_simics()
            with self.db as db:
                db.log_result()
        self.close()

    def supervise(self, iteration_counter, packet_capture):

        def start_packet_capture():
            data_dir = ('campaign-data/'+str(self.db.campaign['id']) +
                        '/results/'+str(self.db.result['id']))
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
            if self.db.campaign['aux']:
                self.debugger.aux.write('./'+self.db.campaign['aux_command'] +
                                        '\n')
            self.debugger.dut.write('./'+self.db.campaign['command']+'\n')
            try:
                self.__monitor_execution()
            except KeyboardInterrupt:
                if self.db.campaign['simics']:
                    self.debugger.continue_dut()
                self.debugger.dut.serial.write('\x03')
                self.debugger.dut.read_until()
                if self.db.campaign['aux']:
                    self.debugger.aux.serial.write('\x03')
                    self.debugger.aux.read_until()
                self.db.result.update({
                    'outcome_category': 'Incomplete',
                    'outcome': 'Interrupted'})
                interrupted = True
            with self.db as db:
                db.log_result()
            if packet_capture:
                end_packet_capture()
