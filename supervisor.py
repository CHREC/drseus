from cmd import Cmd
from multiprocessing import Value
from os import makedirs, system
from pdb import set_trace
from select import select
from sys import stdin
from threading import Thread

from error import DrSEUsError
from fault_injector import fault_injector


class supervisor(Cmd):
    def __init__(self, campaign_data, options):
        self.campaign_data = campaign_data
        self.capture = options.capture
        options.debug = True
        self.drseus = fault_injector(campaign_data, options)
        self.drseus.create_result(outcome_category='Supervisor',
                                  outcome='Start')
        if not self.campaign_data['use_simics']:
            booted = False
            while not booted:
                try:
                    self.drseus.debugger.reset_dut()
                except DrSEUsError:
                    continue
                else:
                    booted = True
            self.drseus.send_dut_files()
        self.prompt = 'DrSEUs> '
        Cmd.__init__(self)
        if self.campaign_data['use_aux']:
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
        except ValueError:
            print('Invalid value entered')
            return
        if self.campaign_data['use_simics']:
            self.drseus.debugger.timeout = new_timeout
        if aux:
            self.drseus.debugger.aux.default_timeout = new_timeout
            self.drseus.debugger.aux.serial.timeout = new_timeout
        else:
            self.drseus.debugger.dut.default_timeout = new_timeout
            self.drseus.debugger.dut.serial.timeout = new_timeout

    def do_command_dut(self, arg, aux=False):
        """Send DUT device a command and interact, interrupt with ctrl-c"""

        def read_thread_worker():
            try:
                if aux:
                    self.drseus.debugger.aux.read_until()
                else:
                    self.drseus.debugger.dut.read_until()
            except DrSEUsError:
                pass

        self.drseus.create_result()
        if aux:
            self.drseus.debugger.aux.write(arg+'\n')
        else:
            self.drseus.debugger.dut.write(arg+'\n')
        read_thread = Thread(target=read_thread_worker)
        read_thread.start()
        try:
            while read_thread.is_alive():
                if select([stdin], [], [], 0.1)[0]:
                    if aux:
                        self.drseus.debugger.aux.write(stdin.readline()+'\n')
                    else:
                        self.drseus.debugger.dut.write(stdin.readline()+'\n')
        except KeyboardInterrupt:
            if self.campaign_data['use_simics']:
                self.drseus.debugger.continue_dut()
            if aux:
                self.drseus.debugger.aux.serial.write('\x03')
            else:
                self.drseus.debugger.dut.serial.write('\x03')
            read_thread.join()
        self.drseus.result_data.update({
            'outcome_category': ('AUX' if aux else 'DUT')+' command',
            'outcome': arg})
        self.drseus.log_result()
        self.drseus.create_result()

    def do_read_dut(self, arg=None, aux=False):
        """Read from DUT, interrupt with ctrl-c"""
        self.drseus.create_result()
        try:
            if aux:
                self.drseus.debugger.aux.read_until(continuous=True)
            else:
                self.drseus.debugger.dut.read_until(continuous=True)
        except KeyboardInterrupt:
            if self.campaign_data['use_simics']:
                self.drseus.debugger.continue_dut()
        self.drseus.result_data['outcome_category'] = \
            'Read '+('AUX' if aux else 'DUT')
        self.drseus.result_data['outcome'] = 'Read '+('AUX' if aux else 'DUT')
        self.drseus.log_result()
        self.drseus.create_result()

    def do_send_dut_file(self, arg, aux=False):
        """Send file to DUT, defaults to campaign files"""
        if arg:
            if aux:
                self.drseus.debugger.aux.send_files(arg, attempts=1)
            else:
                self.drseus.debugger.dut.send_files(arg, attempts=1)
        else:
            self.drseus.send_dut_files(aux)

    def do_get_dut_file(self, arg, aux=False):
        """Retrieve file from DUT device"""
        directory = ('campaign-data/'+str(self.campaign_data['id']) +
                     '/results/'+str(self.drseus.result_id)+'/')
        makedirs(directory)
        if aux:
            self.drseus.debugger.aux.get_file(arg, directory, attempts=1)
        else:
            self.drseus.debugger.dut.get_file(arg, directory, attempts=1)
        print('File saved to '+directory)

    def do_supervise(self, arg):
        """Supervise for targeted runtime (in seconds) or iterations"""
        if 's' in arg:
            try:
                run_time = int(arg.replace('s', ''))
            except ValueError:
                print('Invalid value entered')
                return
            supervise_iterations = max(
                int(run_time / self.campaign_data['exec_time']), 1)
        else:
            try:
                supervise_iterations = int(arg)
            except ValueError:
                print('Invalid value entered')
                return
        print('Performing '+str(supervise_iterations)+' iteration(s)...\n')
        iteration_counter = Value('L', supervise_iterations)
        self.drseus.supervise(iteration_counter, self.capture)

    def do_debug(self, arg=None):
        """Start PDB"""
        set_trace()

    def do_shell(self, arg):
        """Pass command to a system shell when line begins with \"!\""""
        system(arg)

    def do_exit(self, arg=None):
        """Exit DrSEUs"""
        if self.campaign_data['use_simics']:
            self.drseus.debugger.close()
        self.drseus.close()
        self.drseus.result_data.update({
            'outcome_category': 'Supervisor',
            'outcome': 'Exit'})
        self.drseus.log_result()
        return True


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
