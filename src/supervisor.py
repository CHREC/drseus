from cmd import Cmd
from datetime import datetime
from multiprocessing import Value
from os import makedirs, remove
from os.path import exists
from pdb import set_trace
from readline import read_history_file, set_history_length, write_history_file
from select import select
from subprocess import CalledProcessError, call, check_output
from sys import stdin
from threading import Thread
from traceback import print_exc

from .arguments import inject
from .fault_injector import fault_injector
from .jtag.bdi import bdi
from .jtag.openocd import openocd
from .power_switch import power_switch
from .simics import simics


# TODO: add background read thread and interact command
#       (remove dut read and dut command)
class supervisor(Cmd):
    def __init__(self, options):
        options.injections = 0
        options.latent_iterations = 0
        options.compare_all = False
        options.extract_blocks = False
        if options.power_switch_outlet is not None or \
                options.power_switch_ip_address:
            switch = power_switch(options)
        else:
            switch = None
        self.drseus = fault_injector(options, switch)
        if self.drseus.db.campaign.simics:
            self.launch_simics()
        else:
            self.drseus.debugger.reset_dut()
        self.prompt = 'DrSEUs> '
        Cmd.__init__(self)
        if exists('.supervisor_history'):
            read_history_file('.supervisor_history')
        set_history_length(options.history_length)
        if self.drseus.db.campaign.aux:
            self.__class__ = aux_supervisor

    def launch_simics(self):
        checkpoint = 'gold-checkpoints/{}/{}'.format(
            self.drseus.db.campaign.id,
            self.drseus.db.campaign.checkpoints)
        if exists('simics-workspace/{}_merged'.format(checkpoint)):
            self.drseus.debugger.launch_simics('{}_merged'.format(checkpoint))
        else:
            self.drseus.debugger.launch_simics(checkpoint)
        self.drseus.debugger.continue_dut()

    def cmdloop(self):
        try:
            Cmd.cmdloop(self)
        except:
            print_exc()
            self.drseus.db.log_event(
                'Error', 'Supervisor', 'Exception',
                self.drseus.db.log_exception)
            self.drseus.debugger.close()
            self.drseus.db.result.outcome_category = 'Supervisor'
            self.drseus.db.result.outcome = 'Uncaught exception'
            self.drseus.db.log_result(exit=True)

    def preloop(self):
        print('Welcome to DrSEUs!\n')
        self.do_info()
        self.do_help(None)

    def precmd(self, line):
        write_history_file('.supervisor_history')
        return line

    def complete(self, text, state):
        ret = Cmd.complete(self, text, state)
        if ret:
            return '{} '.format(ret)
        else:
            return ret

    def do_info(self, arg=None):
        """Print information about the current campaign"""
        print(self.drseus)

    def do_update_timeout_dut(self, arg, aux=False):
        """Update DUT serial timeout (in seconds)"""
        if aux:
            device = self.drseus.debugger.aux
        else:
            device = self.drseus.debugger.dut
        try:
            new_timeout = int(arg)
        except ValueError:
            print('Invalid value entered')
            return
        if self.drseus.db.campaign.simics:
            self.drseus.debugger.timeout = new_timeout
        device.default_timeout = new_timeout
        device.serial.timeout = new_timeout

    def do_command_dut(self, arg, aux=False):
        """Send DUT device a command and interact, interrupt with ctrl-c"""
        if aux:
            device = self.drseus.debugger.aux
        else:
            device = self.drseus.debugger.dut
        read_thread = Thread(target=device.command, args=[arg])
        read_thread.start()
        try:
            while read_thread.is_alive():
                if select([stdin], [], [], 0.1)[0]:
                    device.write('{}\n'.format(stdin.readline()))
        except KeyboardInterrupt:
            if self.drseus.db.campaign.simics:
                self.drseus.debugger.continue_dut()
            device.write('\x03')
            read_thread.join()

    def do_set_time_dut(self, arg=None, aux=False):
        """Set the time on the DUT using the current time on the host"""
        if aux:
            device = self.drseus.debugger.aux
        else:
            device = self.drseus.debugger.dut
        device.set_time()

    def do_read_dut(self, arg=None, aux=False):
        """Read from DUT, interrupt with ctrl-c"""
        if aux:
            device = self.drseus.debugger.aux
        else:
            device = self.drseus.debugger.dut
        try:
            device.read_until(continuous=True)
        except KeyboardInterrupt:
            if self.drseus.db.campaign.simics:
                self.drseus.debugger.continue_dut()

    def do_send_file_dut(self, arg, aux=False):
        """Send file to DUT, defaults to sending campaign files"""
        if aux:
            device = self.drseus.debugger.aux
        else:
            device = self.drseus.debugger.dut
        device.send_files(arg, attempts=1)

    def do_get_file_dut(self, arg, aux=False):
        """Retrieve file from DUT device"""
        if aux:
            device = self.drseus.debugger.aux
        else:
            device = self.drseus.debugger.dut
        output = 'campaign-data/{}/results/{}/'.format(
            self.drseus.db.campaign.id, self.drseus.result.id)
        makedirs(output)
        output += arg
        device.get_file(arg, output, attempts=1)
        print('File saved to {}'.format(output))

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
        if self.drseus.db.campaign.simics:
            self.drseus.debugger.close()
        else:
            self.drseus.debugger.dut.flush()
        self.drseus.db.log_result()
        self.drseus.inject_campaign(iteration_counter, timer)
        if self.drseus.db.campaign.simics:
            self.drseus.debugger.close()
            self.launch_simics()

    def do_inject(self, arg):
        if not (isinstance(self.drseus.debugger, bdi) or
                isinstance(self.drseus.debugger, openocd) or
                isinstance(self.drseus.debugger, simics)):
            print('injections not supported without debugger')
            return
        if '-h' in arg.split() or '--help' in arg.split():
            return self.help_inject()
        try:
            options = inject.parse_args(arg.split())
        except:
            return
        self.drseus.options.iterations = options.iterations
        self.drseus.options.injections = options.injections
        self.drseus.options.selected_targets = options.selected_targets
        self.drseus.options.selected_target_indices = \
            options.selected_target_indices
        self.drseus.options.selected_registers = options.selected_registers
        self.drseus.options.latent_iterations = options.latent_iterations
        self.drseus.options.processes = options.processes
        self.drseus.options.compare_all = options.compare_all
        self.drseus.options.extract_blocks = options.extract_blocks
        self.drseus.debugger.set_targets()
        if options.iterations is None:
            iteration_counter = None
        else:
            iteration_counter = Value('L', options.iterations)
        if self.drseus.db.campaign.simics:
            self.drseus.debugger.close()
        else:
            self.drseus.debugger.dut.flush()
        self.drseus.db.log_result()
        self.drseus.inject_campaign(iteration_counter)
        if self.drseus.db.campaign.simics:
            self.drseus.debugger.close()
            self.launch_simics()

    def do_minicom_dut(self, arg=None, aux=False):
        """Launch minicom connected to DUT and include session in log"""
        if aux:
            device = self.drseus.debugger.aux
        else:
            device = self.drseus.debugger.dut
        capture = 'minicom_capture.{}_{}'.format(
            '-'.join(['{:02}'.format(unit)
                      for unit in datetime.now().timetuple()[:3]]),
            '-'.join(['{:02}'.format(unit)
                      for unit in datetime.now().timetuple()[3:6]]))
        device.close()
        call(['minicom', '-D',
              self.drseus.options.aux_serial_port if aux
              else self.drseus.options.dut_serial_port,
              '--capturefile={}'.format(capture)])
        device.open()
        if exists(capture):
            with open(capture, 'r') as capture_file:
                if aux:
                    self.drseus.db.result.aux_output += capture_file.read()
                else:
                    self.drseus.db.result.dut_output += capture_file.read()
                self.drseus.db.result.save()
            remove(capture)

    def help_inject(self):
        inject.prog = 'inject'
        inject.print_help()

    def do_log(self, arg):
        """Log current status as a result"""
        self.drseus.db.result.outcome_category = 'Supervisor'
        self.drseus.db.result.outcome = arg if arg else 'User'
        self.drseus.db.log_result(supervisor=True)

    def do_event(self, arg):
        """Log an event"""
        if not arg:
            arg = input('Event type: ')
        description = input('Event description: ')
        self.drseus.db.log_event('Information', 'User', arg, description)

    def do_power_cycle(self, arg=None):
        """Power cycle device using web power switch"""
        if hasattr(self.drseus.debugger, 'power_switch') and \
            self.drseus.debugger.power_switch is not None and \
                hasattr(self.drseus.debugger, 'power_cycle_dut'):
            self.drseus.debugger.power_cycle_dut()
            self.drseus.debugger.reset_dut()
        else:
            print('Web power switch not configured, unable to power cycle')

    def do_debug(self, arg=None):
        """Start PDB"""
        set_trace()

    def do_shell(self, arg):
        """Pass command to a system shell when line begins with '!'"""
        event = self.drseus.db.log_event(
            'Information', 'Shell', arg, success=False)
        try:
            output = check_output(arg, shell=True, universal_newlines=True)
            print(output, end='')
            event.description = output
            event.success = True
            event.save()
        except CalledProcessError as error:
            print(error.output, end='')
            event.description = error.output
            event.save()

    def do_exit(self, arg=None):
        """Exit DrSEUs"""
        self.drseus.db.result.outcome = 'Exited'
        self.drseus.close()
        return True

    do_EOF = do_exit


class aux_supervisor(supervisor):
    def do_update_timeout_aux(self, arg):
        """Update AUX serial timeout (in seconds)"""
        self.do_update_timeout_dut(arg, aux=True)

    def do_command_aux(self, arg):
        """Send AUX device a command and interact, interrupt with ctrl-c"""
        self.do_command_dut(arg, aux=True)

    def do_set_time_aux(self, arg):
        """Set the time on the AUX using the current time on the host"""
        self.do_set_time_dut(arg, aux=True)

    def do_read_aux(self, arg):
        """Read from AUX, interrupt with ctrl-c"""
        self.do_read_dut(arg, aux=True)

    def do_send_file_aux(self, arg):
        """Send (comma-seperated) files to AUX, defaults to campaign files"""
        self.do_send_file_dut(arg, aux=True)

    def do_get_file_aux(self, arg):
        """Retrieve file from AUX device"""
        self.do_get_file_dut(arg, aux=True)

    def do_minicom_aux(self, arg):
        """Launch minicom connected to AUX and include session in log"""
        self.do_minicom_dut(arg, aux=True)
