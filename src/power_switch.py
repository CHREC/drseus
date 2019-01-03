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

from base64 import b64encode
from datetime import datetime
from html.parser import HTMLParser
from multiprocessing import Lock
from os.path import exists
from terminaltables import AsciiTable
from time import sleep
from urllib.request import Request, urlopen


class power_switch(object):
    def __init__(self, options):
        self.ip_address = options.power_switch_ip_address
        self.username = options.power_switch_username
        self.password = options.power_switch_password
        self.outlets = range(1, 9)
        self.lock = Lock()

    def __enter__(self):
        self.lock.acquire()
        return self

    def __exit__(self, type_, value, traceback):
        self.lock.release()
        if type_ is not None or value is not None or traceback is not None:
            return False  # reraise exception

    def get_status(self):
        class table_parser(HTMLParser):
            def __init__(self):
                HTMLParser.__init__(self)
                self.__in_cell = False
                self.__current_table = []
                self.__current_row = []
                self.__current_cell = []
                self.tables = []

            def handle_starttag(self, tag, attrs):
                if tag in ('td', 'th'):
                    self.__in_cell = True

            def handle_data(self, data):
                if self.__in_cell:
                    self.__current_cell.append(data.strip())

            def handle_endtag(self, tag):
                if tag in ('td', 'th'):
                    self.__in_cell = False
                    self.__current_row.append(
                        ' '.join(self.__current_cell).strip())
                    self.__current_cell = []
                elif tag == 'tr':
                    self.__current_table.append(self.__current_row)
                    self.__current_row = []
                elif tag == 'table':
                    self.tables.append(self.__current_table)
                    self.__current_table = []

    # def get_status(self):
        try:
            response = urlopen(Request(
                'http://{}/index.htm'.format(self.ip_address),
                headers={'Authorization': b'Basic ' +
                         b64encode(bytes('{}:{}'.format(
                            self.username, self.password), encoding='utf-8'))}))
        except:
            raise Exception('Error connecting to power switch at {}'.format(
                self.ip_address))
        parser = table_parser()
        parser.feed(response.read().decode())
        for table in parser.tables:
            if 'Individual Control' in table[0]:
                status = []
                for row in table[2:]:
                    status.append({
                        'outlet': int(row[0]),
                        'device': row[1],
                        'status': row[2]})
                return status
        else:
            raise Exception('Could not parse outlet status table from response')

    def print_status(self):
        status = self.get_status()
        table = AsciiTable([['Outlet', 'Device', 'Status']],
                           'Power Switch Status')
        for outlet in status:
            table.table_data.append([str(outlet['outlet']), outlet['device'],
                                     outlet['status']])
        print(table.table)

    def set_outlet(self, outlet, state, delay=5):
        if outlet == 'all':
            outlet = 'a'
        elif outlet not in self.outlets:
            raise Exception('invalid outlet: {}'.format(outlet))
        state = state.upper()
        if state not in ('OFF', 'ON'):
            raise Exception('invalid state: {}'.format(state))
        if delay < 1:
            delay = 1
        try:
            urlopen(Request(
                'http://{}/outlet?{}={}'.format(self.ip_address, outlet, state),
                headers={'Authorization': b'Basic ' +
                         b64encode(bytes('{}:{}'.format(
                            self.username, self.password), encoding='utf-8'))}))
        except:
            raise Exception('Error connecting to power switch at {}'.format(
                self.ip_address))
        if exists('power_switch_log.txt'):
            log = open('power_switch_log.txt', 'a')
        else:
            log = open('power_switch_log.txt', 'w')
            log.write('IP Address\t\tOutlet\tState\tTimestamp\n')
        log.write('{}\t{}\t\t{}\t\t{}\n'.format(
            self.ip_address, outlet, state,
            datetime.now().strftime('%b %d, %Y %I:%M:%S %p')))
        log.close()
        sleep(delay)

    def set_device(self, device, state, delay=5):
        if '*' in device:
            device = device.replace('*', '').lower()
            for outlet in self.get_status():
                if device in outlet['device'].lower():
                    self.set_outlet(outlet['outlet'], state, delay)
        elif device == 'all':
            self.set_outlet('all', state, delay)
        else:
            for outlet in self.get_status():
                if outlet['device'].lower() == device.lower():
                    self.set_outlet(outlet['outlet'], state, delay)
                    break
