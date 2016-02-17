from base64 import b64encode
from html.parser import HTMLParser
from terminaltables import AsciiTable
from urllib.request import Request, urlopen


class power_switch(object):
    def __init__(self, ip_address='10.42.0.60', username='admin',
                 password='chrec'):
        self.ip_address = ip_address
        self.username = username
        self.password = password

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
        if outlet not in range(1, 9):
            raise Exception('invalid outlet: '+str(outlet))
        state = state.upper()
        if state not in ('OFF', 'ON'):
            raise Exception('invalid state: '+state)
        urlopen(Request(
            'http://'+self.ip_address+'/outlet?'+str(outlet)+'='+state,
            headers={'Authorization': b'Basic '+b64encode(
                bytes(self.username+':'+self.password, encoding='utf-8'))}))

    def toggle_outlet(self, outlet):
        for outlet_ in self.get_status():
            if outlet_['outlet'] == outlet:
                if outlet_['status'].upper() == 'ON':
                    self.set_outlet(outlet, 'OFF')
                elif outlet_['status'].upper() == 'OFF':
                    self.set_outlet(outlet, 'ON')
                break

    def set_device(self, device, state):
        for outlet in self.get_status():
            if outlet['device'].lower() == device.lower():
                self.set_outlet(outlet['outlet'], state)
                break

    def toggle_device(self, device):
        for outlet in self.get_status():
            if outlet['device'].lower() == device.lower():
                if outlet['status'].upper() == 'ON':
                    self.set_outlet(outlet['outlet'], 'OFF')
                elif outlet['status'].upper() == 'OFF':
                    self.set_outlet(outlet['outlet'], 'ON')
                break
