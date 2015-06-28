from __future__ import print_function
import os
import sys
import pickle

from dut import dut


class supervisor:
    def __init__(self, dut_ip_address='10.42.0.21',
                 dut_serial_port='/dev/ttyUSB1',
                 aux_ip_address='10.42.0.20',
                 aux_serial_port='/dev/ttyUSB0',
                 use_aux=True, new=True):
        self.use_aux = use_aux
        if not os.path.exists('campaign-data'):
            os.mkdir('campaign-data')
        self.dut = dut(dut_ip_address, dut_serial_port)
        self.aux = dut(aux_ip_address, aux_serial_port)
        if new:
            self.dut.do_login()
            self.aux.do_login()

    def exit(self):
        self.dut.serial.close()
        self.aux.serial.close()
        sys.exit()

    def setup_campaign(self, directory, application, arguments,
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
        files.append(directory+'/'+application)
        aux_files = []
        aux_files.append(directory+'/'+aux_application)
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
        campaign = {
            'application': self.application,
            'aux_application': self.aux_application,
            'command': self.command,
            'aux_command': self.aux_command,
            'use_aux': self.use_aux,
        }
        with open('campaign-data/campaign.pickle', 'w') as campaign_pickle:
            pickle.dump(campaign, campaign_pickle)

    def monitor_execution(self):
        self.dut.serial.write('./'+self.command+'\n')
        self.aux.serial.write('./'+self.aux_command+'\n')
        self.aux.read_until()
        self.dut.read_until()
