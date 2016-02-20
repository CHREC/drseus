from base64 import b64encode
from html.parser import HTMLParser
from multiprocessing import Lock
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
        self.events = 0

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
        response = urlopen(Request(
            'http://'+self.ip_address+'/index.htm',
            headers={'Authorization': b'Basic '+b64encode(
                bytes(self.username+':'+self.password, encoding='utf-8'))}))
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

    def set_outlet(self, outlet, state):
        if self.events >= 10:
            raise Exception('power events exceeded!')
        if outlet == 'all':
            outlet = 'a'
        elif outlet not in self.outlets:
            raise Exception('invalid outlet: '+str(outlet))
        state = state.upper()
        if state not in ('OFF', 'ON'):
            raise Exception('invalid state: '+state)
        self.events += 1
        urlopen(Request(
            'http://'+self.ip_address+'/outlet?'+str(outlet)+'='+state,
            headers={'Authorization': b'Basic '+b64encode(
                bytes(self.username+':'+self.password, encoding='utf-8'))}))
        sleep(5)

    def set_device(self, device, state):
        if '*' in device:
            device = device.replace('*', '').lower()
            for outlet in self.get_status():
                if device in outlet['device'].lower():
                    self.set_outlet(outlet['outlet'], state)
        else:
            for outlet in self.get_status():
                if outlet['device'].lower() == device.lower():
                    self.set_outlet(outlet['outlet'], state)
                    break
