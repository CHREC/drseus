"""
Copyright (c) 2018 NSF Center for Space, High-performance, and Resilient Computing (SHREC)
University of Pittsburgh. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided
that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. 
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.
"""

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
