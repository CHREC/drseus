from cmd import Cmd
from multiprocessing import Value
from os import makedirs, system
from pdb import set_trace
from select import select
from sys import stdin
from threading import Thread
from traceback import print_exc

from fault_injector import fault_injector


# TODO: add background read thread and interact command
#       (remove dut read and dut command)
class supervisor(Cmd):
    def __init__(self, campaign, options):
        options.debug = True
        options.injections = 0
        options.latent_iterations = 0
        options.compare_all = False
        options.extract_blocks = False
        self.drseus = fault_injector(campaign, options)
        if campaign['simics']:
            self.drseus.debugger.launch_simics(
                'gold-checkpoints/'+str(self.drseus.db.campaign['id'])+'/' +
                str(self.drseus.db.campaign['checkpoints'])+'_merged')
            self.drseus.debugger.continue_dut()
        else:
            self.drseus.debugger.reset_dut()
        self.prompt = 'DrSEUs> '
        Cmd.__init__(self)
        if campaign['aux']:
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
        if self.drseus.db.campaign['simics']:
            self.drseus.debugger.timeout = new_timeout
        if aux:
            self.drseus.debugger.aux.default_timeout = new_timeout
            self.drseus.debugger.aux.serial.timeout = new_timeout
        else:
            self.drseus.debugger.dut.default_timeout = new_timeout
            self.drseus.debugger.dut.serial.timeout = new_timeout

    def do_command_dut(self, arg, aux=False):
        """Send DUT device a command and interact, interrupt with ctrl-c"""
        read_thread = Thread(target=(self.drseus.debugger.aux.command if aux
                                     else self.drseus.debugger.dut.command),
                             args=[arg])
        read_thread.start()
        try:
            while read_thread.is_alive():
                if select([stdin], [], [], 0.1)[0]:
                    if aux:
                        self.drseus.debugger.aux.write(stdin.readline()+'\n')
                    else:
                        self.drseus.debugger.dut.write(stdin.readline()+'\n')
        except KeyboardInterrupt:
            if self.drseus.db.campaign['simics']:
                self.drseus.debugger.continue_dut()
            if aux:
                self.drseus.debugger.aux.write('\x03')
            else:
                self.drseus.debugger.dut.write('\x03')
            read_thread.join()
        self.drseus.db.result.update({
            'outcome_category': ('AUX' if aux else 'DUT')+' command',
            'outcome': arg})
        with self.drseus.db as db:
            db.log_result()

    def do_read_dut(self, arg=None, aux=False):
        """Read from DUT, interrupt with ctrl-c"""
        try:
            if aux:
                self.drseus.debugger.aux.read_until(continuous=True)
            else:
                self.drseus.debugger.dut.read_until(continuous=True)
        except KeyboardInterrupt:
            if self.drseus.db.campaign['simics']:
                self.drseus.debugger.continue_dut()
        self.drseus.db.result.update({
            'outcome_category': 'Read '+('AUX' if aux else 'DUT'),
            'outcome': 'Read '+('AUX' if aux else 'DUT')})
        with self.drseus.db as db:
            db.log_result()

    def do_send_dut_file(self, arg, aux=False):
        """Send file to DUT, defaults to sending campaign files"""
        if aux:
            self.drseus.debugger.aux.send_files(arg, attempts=1)
        else:
            self.drseus.debugger.dut.send_files(arg, attempts=1)

    def do_get_dut_file(self, arg, aux=False):
        """Retrieve file from DUT device"""
        output = ('campaign-data/'+str(self.drseus.db.campaign['id']) +
                  '/results/'+str(self.drseus.result['id'])+'/')
        makedirs(output)
        output += '/'+arg
        if aux:
            self.drseus.debugger.aux.get_file(arg, output, attempts=1)
        else:
            self.drseus.debugger.dut.get_file(arg, output, attempts=1)
        print('File saved to '+output)

    def do_supervise(self, arg):
        """Supervise for targeted runtime (in seconds) or iterations"""
        if 's' in arg:
            try:
                timer = int(arg.replace('s', ''))
            except ValueError:
                print('Invalid value entered')
                return
            iteration_counter = None
        else:
            try:
                supervise_iterations = int(arg)
            except ValueError:
                print('Invalid value entered')
                return
            iteration_counter = Value('L', supervise_iterations)
            timer = None
        if self.drseus.db.campaign['simics']:
            self.drseus.debugger.close()
        self.drseus.db.result.update({
            'outcome_category': 'DrSEUs',
            'outcome': 'Pre-supervise'})
        self.drseus.debugger.dut.flush()
        with self.drseus.db as db:
            db.log_result()
        try:
            self.drseus.inject_campaign(iteration_counter, timer)
        except KeyboardInterrupt:
            with self.drseus.db as db:
                db.log_event('Information', 'User', 'Interrupted',
                             db.log_exception)
            self.drseus.db.result.update({'outcome_category': 'Incomplete',
                                          'outcome': 'Interrupted'})
            with self.drseus.db as db:
                db.log_result()
        except:
            print_exc()
            with self.drseus.db as db:
                db.log_event('Error', 'DrSEUs', 'Exception', db.log_exception)
            self.drseus.db.result.update({'outcome_category': 'Incomplete',
                                     'outcome': 'Uncaught exception'})
            with self.drseus.db as db:
                db.log_result()
        if self.drseus.db.campaign['simics']:
            self.drseus.debugger.launch_simics(
                'gold-checkpoints/'+str(self.drseus.db.campaign['id'])+'/' +
                str(self.drseus.db.campaign['checkpoints'])+'_merged')
            self.drseus.debugger.continue_dut()

    def do_debug(self, arg=None):
        """Start PDB"""
        set_trace()

    def do_shell(self, arg):
        """Pass command to a system shell when line begins with \"!\""""
        system(arg)

    def do_exit(self, arg=None):
        """Exit DrSEUs"""
        self.drseus.close()
        return True

    do_EOF = do_exit


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
