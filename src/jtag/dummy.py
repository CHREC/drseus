from termcolor import colored

from ..dut import dut
from . import jtag

# TODO: set outlet if power_switch supplied


class dummy(jtag):
    def __init__(self, database, options, power_switch=None):
        self.db = database
        self.options = options
        self.power_switch = power_switch
        self.open()

    def __str__(self):
        return 'Dummy Debugger'

    def open(self):
        self.dut = dut(self.db, self.options)
        self.dut.write('\x03')
        self.dut.do_login()
        if self.db.campaign.aux:
            self.aux = dut(self.db, self.options, aux=True)
            self.aux.write('\x03')
            self.aux.do_login()

    def close(self):
        self.dut.close()
        if self.db.campaign.aux:
            self.aux.close()

    def power_cycle_dut(self):
        event = self.db.log_event(
            'Information', 'Debugger', 'Power cycled DUT', success=False)
        self.close()
        with self.power_switch as ps:
            ps.set_outlet(self.options.power_switch_outlet, 'off')
            ps.set_outlet(self.options.power_switch_outlet, 'on')
        self.open()
        print(colored('Power cycled device: {}'.format(self.dut.serial.port),
                      'red'))
        event.success = True
        event.save()

    def set_targets(self):
        self.targets = {}

    def reset_dut(*args, **kwargs):
        pass

    def halt_dut(*args, **kwargs):
        pass

    def continue_dut(*args, **kwargs):
        pass
