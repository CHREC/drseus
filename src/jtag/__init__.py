from random import uniform
from telnetlib import Telnet
from termcolor import colored
from threading import Thread
from time import sleep

from ..dut import dut
from ..error import DrSEUsError
from ..targets import choose_bit, choose_register, choose_target


class jtag(object):
    def __init__(self, database, options):
        self.db = database
        self.options = options
        self.timeout = 30
        self.prompts = [bytes(prompt, encoding='utf-8')
                        for prompt in self.prompts]
        if self.options.command == 'inject' and \
                self.options.selected_targets is not None:
            for target in self.options.selected_targets:
                if target not in self.targets:
                    raise Exception('invalid injection target: '+target)

    def __str__(self):
        string = 'JTAG Debugger at '+self.options.debugger_ip_address
        try:
            string += ' port '+str(self.port)
        except AttributeError:
            pass
        return string

    def connect_telnet(self):
        self.telnet = Telnet(self.options.debugger_ip_address, self.port,
                             timeout=self.timeout)
        with self.db as db:
            db.log_event('Information', 'Debugger', 'Connected to telnet',
                         self.options.debugger_ip_address+':'+str(self.port),
                         success=True)

    def open(self):
        self.dut = dut(self.db, self.options)
        if self.db.campaign['aux']:
            self.aux = dut(self.db, self.options, aux=True)
        self.connect_telnet()

    def close(self):
        self.telnet.close()
        with self.db as db:
            db.log_event('Information', 'Debugger', 'Closed telnet',
                         success=True)
        self.dut.close()
        if self.db.campaign['aux']:
            self.aux.close()

    def reset_dut(self, expected_output, attempts):

        def attempt_exception(attempt, attempts, error, event_type):
            with self.db as db:
                db.log_event('Warning' if attempt < attempts-1 else 'Error',
                             'Debugger', event_type, db.log_exception)
            print(colored(
                self.dut.serial.port+': Error resetting DUT (attempt ' +
                str(attempt+1)+'/'+str(attempts)+'): '+str(error), 'red'))
            if attempt < attempts-1:
                sleep(30)
            else:
                raise DrSEUsError(error.type)

    # def reset_dut(self, expected_output, attempts):
        self.dut.flush()
        self.dut.reset_ip()
        for attempt in range(attempts):
            try:
                self.command('reset', expected_output,
                             'Error resetting DUT', False)
            except DrSEUsError as error:
                attempt_exception(attempt, attempts, error,
                                  'Error resetting DUT')
            else:
                try:
                    self.dut.do_login()
                except DrSEUsError as error:
                    attempt_exception(attempt, attempts, error,
                                      'Error booting DUT')
                else:
                    with self.db as db:
                        db.log_event('Information', 'Debugger', 'Reset DUT',
                                     success=True)
                    break

    def halt_dut(self, halt_command, expected_output):
        with self.db as db:
            event = db.log_event('Information', 'Debugger', 'Halt DUT',
                                 success=False)
        self.command(halt_command, expected_output, 'Error halting DUT', False)
        self.dut.stop_timer()
        with self.db as db:
            db.log_event_success(event)

    def continue_dut(self, continue_command):
        with self.db as db:
            event = db.log_event('Information', 'Debugger', 'Continue DUT',
                                 success=False)
        self.command(continue_command, error_message='Error continuing DUT',
                     log_event=False)
        self.dut.start_timer()
        with self.db as db:
            db.log_event_success(event)

    def time_application(self):
        with self.db as db:
            event = db.log_event('Information', 'Debugger', 'Timed application',
                                 success=False, campaign=True)
        self.dut.reset_timer()
        for i in range(self.options.iterations):
            if self.db.campaign['aux']:
                aux_process = Thread(
                    target=self.aux.command,
                    kwargs={'command': './'+self.db.campaign['aux_command'],
                            'flush': False})
                aux_process.start()
            dut_process = Thread(
                target=self.dut.command,
                kwargs={'command': './'+self.db.campaign['command'],
                        'flush': False})
            dut_process.start()
            if self.db.campaign['aux']:
                aux_process.join()
            if self.db.campaign['kill_dut']:
                self.dut.write('\x03')
            dut_process.join()
        self.db.campaign['execution_time'] = \
            self.dut.get_timer_value() / self.options.iterations
        with self.db as db:
            db.log_event_success(event)

    def inject_faults(self):
        injection_times = []
        for i in range(self.options.injections):
            injection_times.append(uniform(0,
                                           self.db.campaign['execution_time']))
        injections = []
        for injection_time in sorted(injection_times):
            target, target_index = \
                choose_target(self.options.selected_targets, self.targets)
            register, register_index, register_alias = \
                choose_register(target, self.targets)
            bit, field = choose_bit(register, target, self.targets)
            injection = {'bit': bit,
                         'field': field,
                         'register': register,
                         'register_alias': register_alias,
                         'register_index': register_index,
                         'result_id': self.db.result['id'],
                         'success': False,
                         'target': target,
                         'target_index': target_index,
                         'time': injection_time,
                         'timestamp': None}
            with self.db as db:
                db.insert('injection', injection)
        self.dut.write('./'+self.db.campaign['command']+'\n')
        previous_injection_time = 0
        for injection in injections:
            if target in ('CPU', 'GPR', 'TLB') or \
                ('CP' in self.targets[target] and
                    self.targets[target]['CP']):
                self.select_core(injection['target_index'])
            sleep(injection['time']-previous_injection_time)
            self.halt_dut()
            previous_injection_time = injection['time']
            injection['processor_mode'] = self.get_mode()
            if 'access' in (self.targets[target]
                                        ['registers'][injection['register']]):
                injection['register_access'] = \
                    self.targets([target]
                                 ['registers'][injection['register']]['access'])
            injection['gold_value'] = \
                self.get_register_value(injection)
            injection['injected_value'] = hex(
                int(injection['gold_value'], base=16) ^ (1 << bit))
            with self.db as db:
                db.update('injection', injection)
            if self.options.debug:
                print(colored('injection time: '+str(injection['time']),
                              'magenta'))
                print(colored('target: '+target, 'magenta'))
                if 'target_index' in injection:
                    print(colored('target_index: ' +
                                  str(injection['target_index']), 'magenta'))
                print(colored('register: '+injection['register'], 'magenta'))
                print(colored('bit: '+str(injection['bit']), 'magenta'))
                print(colored('gold value: '+injection['gold_value'],
                              'magenta'))
                print(colored('injected value: ' +
                              injection['injected_value'], 'magenta'))
            self.set_register_value(injection)
            if int(injection['injected_value'], base=16) == \
                    int(self.get_register_value(injection), base=16):
                injection['success'] = True
                with self.db as db:
                    db.update('injection', injection)
                    db.log_event('Information', 'Debugger', 'Fault injected',
                                 success=True)
            else:
                self.set_mode()
                self.set_register_value(injection)
                if int(injection['injected_value'], base=16) == \
                        int(self.get_register_value(injection), base=16):
                    injection['success'] = True
                    with self.db as db:
                        db.update('injection', injection)
                        db.log_event('Information', 'Debugger',
                                     'Fault injected as supervisor',
                                     success=True)
                else:
                    with self.db as db:
                        db.log_event('Error', 'Debugger', 'Injection failed',
                                     success=False)
                self.set_mode(injection['processor_mode'])
            self.continue_dut()
        return 0, False

    def command(self, command, expected_output, error_message,
                log_event, line_ending, echo):
        if log_event:
            with self.db as db:
                event = db.log_event('Information', 'Debugger', 'Command',
                                     command, success=False)
        expected_output = [bytes(output, encoding='utf-8')
                           for output in expected_output]
        return_buffer = ''
        if error_message is None:
            error_message = command
        buff = self.telnet.read_very_eager().decode('utf-8', 'replace')
        if self.db.result:
            self.db.result['debugger_output'] += buff
        else:
            self.db.campaign['debugger_output'] += buff
        if self.options.debug:
            print(colored(buff, 'yellow'))
        if command:
            self.telnet.write(bytes(command+line_ending, encoding='utf-8'))
            if echo:
                index, match, buff = self.telnet.expect(
                    [bytes(command, encoding='utf-8')], timeout=self.timeout)
                buff = buff.decode('utf-8', 'replace')
            else:
                buff = command+'\n'
            if self.db.result:
                self.db.result['debugger_output'] += buff
            else:
                self.db.campaign['debugger_output'] += buff
            if self.options.debug:
                print(colored(buff, 'yellow'))
            if echo and index < 0:
                raise DrSEUsError(error_message)
        for i in range(len(expected_output)):
            index, match, buff = self.telnet.expect(expected_output,
                                                    timeout=self.timeout)
            buff = buff.decode('utf-8', 'replace')
            if self.db.result:
                self.db.result['debugger_output'] += buff
            else:
                self.db.campaign['debugger_output'] += buff
            return_buffer += buff
            if self.options.debug:
                print(colored(buff, 'yellow'), end='')
            if index < 0:
                raise DrSEUsError(error_message)
        else:
            if self.options.debug:
                print()
        index, match, buff = self.telnet.expect(self.prompts,
                                                timeout=self.timeout)
        buff = buff.decode('utf-8', 'replace')
        if self.db.result:
            self.db.result['debugger_output'] += buff
        else:
            self.db.campaign['debugger_output'] += buff
        return_buffer += buff
        if self.options.debug:
            print(colored(buff, 'yellow'))
        with self.db as db:
            if self.db.result:
                db.update('result')
            else:
                db.update('campaign')
        if index < 0:
            raise DrSEUsError(error_message)
        for message in self.error_messages:
            if message in return_buffer:
                raise DrSEUsError(error_message)
        if log_event:
            with self.db as db:
                db.log_event_success(event)
        return return_buffer
