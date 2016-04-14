from termcolor import colored

from ..dut import dut
from . import jtag


class dummy(jtag):
    def __init__(self, database, options, power_switch=None):
        self.db = database
        self.options = options
        self.power_switch = power_switch
        self.open()

    def __str__(self):
        return 'dummy debugger'

    def open(self):
        self.dut = dut(self.db, self.options)
        self.dut.write('\x03')
        self.dut.do_login()
        if self.db.campaign['aux']:
            self.aux = dut(self.db, self.options, aux=True)
            self.aux.write('\x03')
            self.aux.do_login()

    def close(self):
        self.dut.close()
        if self.db.campaign['aux']:
            self.aux.close()

    def reset_dut(self):
        pass

    def power_cycle_dut(self):
        with self.db as db:
            event = db.log_event('Information', 'Debugger',
                                 'Power cycled DUT', success=False)
        self.close()
        with self.power_switch as ps:
            ps.set_outlet(self.options.power_switch_outlet, 'off')
            ps.set_outlet(self.options.power_switch_outlet, 'on')
        self.open()
        print(colored('Power cycled device: '+self.dut.serial.port, 'red'))
        with self.db as db:
            db.log_event_success(event)

    def halt_dut(self):
        pass

    def continue_dut(self):
        pass

    def inject_faults(self):
        self.dut.write('./'+self.db.campaign['command']+'\n')
        return None, None
