#!/usr/bin/python

from __future__ import print_function
from cmd import Cmd
import multiprocessing
import os
import pdb
from select import select
import sys
from threading import Thread

from error import DrSEUsError
from options import options
import utilities


class supervisor(Cmd):
    def __init__(self, options):
        self.options = options
        self.options.debug = True
        if not self.options.campaign_number:
            self.options.campaign_number = utilities.get_last_campaign()
        self.campaign_data = utilities.get_campaign_data(
            options.campaign_number)
        self.drseus = utilities.load_campaign(self.campaign_data, options)
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
        self.prompt = 'DrSEUs> '
        Cmd.__init__(self)
        if self.drseus.use_aux:
            self.__class__ = aux_supervisor

    def preloop(self):
        print('Welcome to DrSEUs!\n')
        self.do_info()
        self.do_help(None)
        Cmd.preloop(self)

    def do_info(self, arg=None):
        """Print information about the current campaign"""
        print(str(self.drseus))

    def do_update_dut_timeout(self, arg, aux=False):
        """Update DUT serial timeout (in seconds)"""
        try:
            new_timeout = int(arg)
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

    def do_command_dut(self, arg, aux=False):
        """Send DUT device a command and interact, interrupt with ctrl-c"""
        self.drseus.create_result()
        if aux:
            self.drseus.debugger.aux.serial.write(arg+'\n')
        else:
            self.drseus.debugger.dut.serial.write(arg+'\n')

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
            self.drseus.log_result(arg, 'AUX command')
        else:
            self.drseus.log_result(arg, 'DUT command')

    def do_read_dut(self, arg=None, aux=False):
        """Read from DUT, interrupt with ctrl-c"""
        self.drseus.create_result()
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

    def do_send_dut_files(self, arg, aux=False):
        """Send (comma-seperated) files to DUT, defaults to campaign files"""
        try:
            if arg:
                files = []
                for item in arg.split(','):
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
            if self.drseus.use_simics:
                self.drseus.debugger.continue_dut()

    def do_get_dut_file(self, arg, aux=False):
        """Retrieve file from DUT device"""
        self.drseus.create_result()
        directory = ('campaign-data/'+str(self.drseus.campaign_number) +
                     '/results/'+str(self.drseus.result_id)+'/')
        os.makedirs(directory)
        try:
            if aux:
                self.drseus.debugger.aux.get_file(arg, directory)
            else:
                self.drseus.debugger.dut.get_file(arg, directory)
        except KeyboardInterrupt:
            self.drseus.log_result(arg, 'Get '+('AUX' if aux else 'DUT') +
                                        ' file interrupted')
            if self.drseus.use_simics:
                self.drseus.debugger.continue_dut()
        else:
            self.drseus.log_result(arg, 'Get '+('AUX' if aux else 'DUT') +
                                        ' file')
            print('File saved to '+directory)

    def do_supervise(self, arg):
        """Supervise for targeted runtime (in seconds) or iterations"""
        if 's' in arg:
            try:
                run_time = int(arg.replace('s', ''))
            except:
                print('Invalid value entered')
                return
            supervise_iterations = max(int(run_time / self.drseus.exec_time), 1)
        else:
            try:
                supervise_iterations = int(arg)
            except:
                print('Invalid value entered')
                return
        print('Performing '+str(supervise_iterations)+' iteration(s)...\n')
        iteration_counter = multiprocessing.Value('I', supervise_iterations)
        self.drseus.supervise(iteration_counter,
                              self.campaign_data['output_file'],
                              self.campaign_data['use_aux_output'],
                              self.options.capture)

    def do_debug(self, arg=None):
        """Start PDB"""
        pdb.set_trace()

    def do_shell(self, arg):
        """Pass command to a system shell when line begins with \"!\""""
        os.system(arg)

    def do_exit(self, arg=None):
        """Exit DrSEUs"""
        if self.drseus.use_simics:
            self.drseus.debugger.close()
        self.drseus.close()
        sys.exit()


class aux_supervisor(supervisor):
    def do_update_aux_timeout(self, arg):
        """Update AUX serial timeout (in seconds)"""
        self.do_update_dut_timeout(arg, aux=True)

    def do_command_aux(self, arg):
        """Send AUX device a command and interact, interrupt with ctrl-c"""
        self.do_dut_command(arg, aux=True)

    def do_read_aux(self, arg):
        """Read from AUX, interrupt with ctrl-c"""
        self.do_read_dut(arg, aux=True)

    def send_aux_files(self, arg):
        """Send (comma-seperated) files to AUX, defaults to campaign files"""
        self.do_send_dut_files(arg, aux=True)

    def do_get_aux_file(self, arg):
        """Retrieve file from AUX device"""
        self.do_get_dut_file(arg, aux=True)

if __name__ == '__main__':
    supervisor(options).cmdloop()
