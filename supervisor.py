from __future__ import print_function
import os
import sys

from paramiko import RSAKey

from dut import dut
from simics import simics


class supervisor:
    def __init__(self, dut_ip_address='10.42.0.21',
                 dut_serial_port='/dev/ttyUSB1',
                 aux_ip_address='10.42.0.20',
                 aux_serial_port='/dev/ttyUSB0',
                 architecture='p2020',
                 use_simics=False, use_aux=True, new=True, debug=True):
        self.use_simics = use_simics
        self.use_aux = use_aux
        self.debug = debug
        if not os.path.exists('campaign-data'):
            os.mkdir('campaign-data')
        if os.path.exists('campaign-data/private.key'):
            self.rsakey = RSAKey.from_private_key_file(
                'campaign-data/private.key')
        else:
            self.rsakey = RSAKey.generate(1024)
            self.rsakey.write_private_key_file('campaign-data/private.key')
        if use_simics:
            self.debugger = simics(architecture, self.rsakey, use_aux, new,
                                   debug)
            self.dut = self.debugger.dut
            self.aux = self.debugger.aux
        else:
            self.dut = dut(dut_ip_address, self.rsakey, dut_serial_port,
                           'root@p2020rdb:~#', debug)
            self.aux = dut(aux_ip_address, self.rsakey, aux_serial_port,
                           'root@p2020rdb:~#', debug, color='cyan')
            if new:
                self.dut.do_login()
                self.aux.do_login()

    def exit(self):
        if self.use_simics:
            self.debugger.close()
        else:
            self.dut.close()
            self.aux.close()
        sys.exit()

    def setup_campaign(self, application, arguments,
                       aux_application, aux_arguments):
        self.application = application
        self.aux_application = aux_application
        if arguments:
            self.command = application+' '+arguments
        else:
            self.command = application
        if aux_arguments:
            self.aux_command = aux_application+' '+aux_arguments
        else:
            self.aux_command = aux_application
        files = []
        files.append('fiapps/'+application)
        aux_files = []
        aux_files.append('fiapps/'+aux_application)
        try:
            self.dut.send_files(files)
        except:
            print('could not send files to dut')
            sys.exit()
        try:
            self.aux.send_files(aux_files)
        except:
            print('could not send files to aux')
            sys.exit()

    def monitor_execution(self):
        self.dut.serial.write('./'+self.command+'\n')
        self.aux.serial.write('./'+self.aux_command+'\n')
        self.aux.read_until()
        if self.debug:
            print()
        self.dut.read_until()
        if self.debug:
            print()
