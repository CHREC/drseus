from __future__ import print_function
import os
import pdb
from select import select
import sys
from threading import Thread

from error import DrSEUsError


class supervisor():
    def __init__(self, campaign_data, drseus, options, iteration_counter):
        self.campaign_data = campaign_data
        self.drseus = drseus
        self.options = options
        self.iteration_counter = iteration_counter
        self.prompt = 'DrSEUs> '
        self.commands = [('h', 'Print these commands', self.print_help),
                         ('i', 'Print DrSEUs information', self.print_info),
                         ('t', 'Change DUT serial timeout',
                          self.change_dut_timeout),
                         ('c', 'Send DUT command', self.dut_command),
                         ('r', 'Read from DUT serial', self.dut_read),
                         ('f', 'Send DUT files', self.send_dut_files),
                         ('g', 'Get DUT file', self.get_dut_file),
                         ('s', 'Supervise', self.supervise)]
        if not self.drseus.use_simics:
            self.commands.append(('R', 'Reset DUT',
                                  self.drseus.debugger.reset_dut))
        self.commands.extend([('d', 'Debug with the Python Debugger',
                               pdb.set_trace),
                              ('q', 'Quit DrSEUs Supervisor', self.quit)])
        if self.drseus.use_aux:
            self.commands.extend([('at', 'Change AUX serial timeout',
                                   self.change_aux_timeout),
                                  ('ac', 'Send AUX command', self.aux_command),
                                  ('ar', 'Read from DUT serial', self.aux_read),
                                  ('af', 'Send AUX files', self.send_aux_files),
                                  ('ag', 'Get AUX file', self.get_aux_file)])
        self.drseus.data_diff = None
        self.drseus.detected_errors = None
        if self.drseus.use_simics:
            checkpoint = ('gold-checkpoints/' +
                          str(self.drseus.campaign_number)+'/' +
                          str(self.drseus.num_checkpoints)+'_merged')
            self.drseus.debugger.launch_simics(checkpoint)
            self.drseus.debugger.continue_dut()
        else:
            if self.drseus.use_aux:
                self.drseus.debugger.aux.serial.write('\x03')
                aux_process = Thread(target=self.drseus.debugger.aux.do_login)
                aux_process.start()
            booted = False
            while not booted:
                try:
                    self.drseus.debugger.reset_dut()
                except DrSEUsError:
                    continue
                else:
                    booted = True
            if self.drseus.use_aux:
                aux_process.join()
                self.drseus.send_aux_files()
            self.drseus.send_dut_files()

    def next_result(self):
        with self.iteration_counter.get_lock():
            self.drseus.iteration = self.iteration_counter.value
            self.iteration_counter.value += 1
        self.drseus.result_id = self.drseus.get_result_id(0)

    def print_help(self):
        print('DrSEUS Supervisor Commands:')
        for command in self.commands:
            print('\t', command[0], ':\t', command[1], sep='')

    def print_info(self):
        print(str(self.drseus))

    def change_aux_timeout(self):
        self.change_dut_timeout(aux=True)

    def change_dut_timeout(self, aux=False):
        print('Enter new device timeout in seconds:')
        new_timeout = raw_input(self.prompt)
        try:
            new_timeout = int(new_timeout)
        except:
            print('Invalid value entered')
            return
        if self.drseus.use_simics:
            self.drseus.debugger.timeout = new_timeout
        if aux:
            self.drseus.debugger.aux.default_timeout = new_timeout
            self.drseus.debugger.aux.serial.timeout = new_timeout
        else:
            self.drseus.debugger.dut.default_timeout = new_timeout
            self.drseus.debugger.dut.serial.timeout = new_timeout

    def aux_command(self):
        self.dut_command(aux=True)

    def dut_command(self, aux=False):
        self.next_result()
        if aux:
            print('Enter command for AUX:')
        else:
            print('Enter command for DUT:')
        command = raw_input(self.prompt)
        print('\nYou can interact with the device, interrupt with ctrl-c')
        if aux:
            self.drseus.debugger.aux.serial.write(command+'\n')
        else:
            self.drseus.debugger.dut.serial.write(command+'\n')

        def read_thread_worker():
            try:
                if aux:
                    self.drseus.debugger.aux.read_until()
                else:
                    self.drseus.debugger.dut.read_until()
            except DrSEUsError:
                pass
        read_thread = Thread(target=read_thread_worker)
        read_thread.start()
        try:
            while read_thread.is_alive():
                if select([sys.stdin], [], [], 0.1)[0]:
                    if aux:
                        self.drseus.debugger.aux.serial.write(
                            sys.stdin.readline()+'\n')
                    else:
                        self.drseus.debugger.dut.serial.write(
                            sys.stdin.readline()+'\n')
        except KeyboardInterrupt:
            if self.drseus.use_simics:
                self.drseus.debugger.continue_dut()
            if aux:
                self.drseus.debugger.aux.serial.write('\x03')
            else:
                self.drseus.debugger.dut.serial.write('\x03')
            read_thread.join()
        if aux:
            self.drseus.log_result(command, 'AUX command')
        else:
            self.drseus.log_result(command, 'DUT command')

    def aux_read(self):
        self.dut_read(aux=True)

    def dut_read(self, aux=False):
        print('Reading from device, interrupt with ctrl-c')
        self.next_result()
        try:
            if aux:
                self.drseus.debugger.aux.read_until('toinfinityandbeyond!')
            else:
                self.drseus.debugger.dut.read_until('toinfinityandbeyond!')
        except DrSEUsError as error:
            outcome = error.type
        except KeyboardInterrupt:
            outcome = 'Interrupted'
            if self.drseus.use_simics:
                self.drseus.debugger.continue_dut()
        else:
            outcome = 'No error'
        if aux:
            self.drseus.log_result(outcome, 'Read AUX')
        else:
            self.drseus.log_result(outcome, 'Read DUT')

    def send_aux_files(self):
        self.send_dut_files(aux=True)

    def send_dut_files(self, aux=False):
        print('Enter files to send from '+self.options.directory +
              ' (none for campaign files):')
        user_files = raw_input(self.prompt)
        print()
        try:
            if user_files:
                files = []
                for item in user_files.split(','):
                    files.append(self.options.directory+'/' +
                                 item.lstrip().rstrip())
                if aux:
                    self.drseus.debugger.aux.send_files(files)
                else:
                    self.drseus.debugger.dut.send_files(files)
            else:
                self.drseus.send_dut_files(aux)
        except KeyboardInterrupt:
            print('Transfer interrupted')

    def get_aux_file(self):
        self.get_dut_file(aux=True)

    def get_dut_file(self, aux=False):
        self.next_result()
        self.drseus.result_id = self.drseus.get_result_id(0)
        os.makedirs('campaign-data/'+str(self.drseus.campaign_number) +
                    '/results/'+str(self.drseus.iteration))
        directory = ('campaign-data/'+str(self.drseus.campaign_number) +
                     '/results/'+str(self.drseus.iteration)+'/')
        print('Enter file to get (file will be saved to '+directory+'):')
        file_ = raw_input(self.prompt)
        try:
            if aux:
                self.drseus.debugger.aux.get_file(file_, directory)
            else:
                self.drseus.debugger.dut.get_file(file_, directory)
        except KeyboardInterrupt:
            self.drseus.log_result(file_, 'Get '+('AUX' if aux else 'DUT') +
                                          ' file interrupted')
        else:
            self.drseus.log_result(file_, 'Get '+('AUX' if aux else 'DUT') +
                                          ' file')

    def supervise(self):
        print('Enter iterations to perform or targeted run time in seconds:')
        iterations = raw_input(self.prompt)
        if 's' in iterations:
            run_time = int(iterations.replace('s', ''))
            iterations = int(run_time / self.drseus.exec_time)
        else:
            iterations = int(iterations)
        print('Performing '+str(iterations)+' iteration(s)...\n')
        self.drseus.supervise(self.iteration_counter, iterations,
                              self.campaign_data['output_file'],
                              self.campaign_data['use_aux_output'],
                              self.options.capture)

    def quit(self):
        if self.drseus.use_simics:
            self.drseus.debugger.close()
        self.drseus.close()
        sys.exit()

    def main(self):
        print('\nWelcome to DrSEUs Supervisor\n')
        self.print_info()
        print()
        self.print_help()
        while True:
            print()
            user_commands = raw_input(self.prompt)
            for user_command in user_commands.split(';'):
                for command in self.commands:
                    if command[0] == user_command.strip():
                        print()
                        command[2]()
                        break
                else:
                    print('Unknown command \"'+user_command +
                          '\", enter "h" for help')
