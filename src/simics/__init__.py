from os import getcwd, listdir, makedirs, mkdir
from os.path import exists
from random import choice
from re import findall
from shutil import copyfile
from signal import SIGINT
from subprocess import call, check_call, check_output, DEVNULL, PIPE, Popen
from sys import stdout
from termcolor import colored
from threading import Thread
from time import sleep

from ..dut import dut
from ..error import DrSEUsError
from ..targets import choose_injection, get_num_bits, get_targets
from ..timeout import timeout, TimeoutException
from .config import simics_config


class simics(object):
    error_messages = ['Address not mapped', 'Illegal Instruction',
                      'Illegal instruction', 'Illegal memory mapping',
                      'Illegal Memory Mapping', 'Error setting attribute',
                      'dropping memop (peer attribute not set)',
                      'where nothing is mapped', 'Error']

    def __init__(self, database, options):
        self.simics = None
        self.dut = None
        self.aux = None
        self.running = False
        self.db = database
        self.options = options
        if database.campaign['architecture'] == 'p2020':
            self.board = 'p2020rdb'
        elif database.campaign['architecture'] == 'a9':
            self.board = 'a9x2'
        self.set_targets()

    def __str__(self):
        string = 'Simics simulation of '+self.board
        return string

    def set_targets(self):
        if hasattr(self.options, 'selected_targets'):
            selected_targets = self.options.selected_targets
        else:
            selected_targets = None
        if hasattr(self.options, 'selected_registers'):
            selected_registers = self.options.selected_registers
        else:
            selected_registers = None
        if self.db.campaign['architecture'] == 'p2020':
            self.targets = get_targets('p2020', 'simics', selected_targets,
                                       selected_registers)
        elif self.db.campaign['architecture'] == 'a9':
            self.targets = get_targets('a9', 'simics', selected_targets,
                                       selected_registers)

    def launch_simics(self, checkpoint=None):
        attempts = 10
        for attempt in range(attempts):
            self.simics = Popen([getcwd()+'/simics-workspace/simics',
                                 '-no-win', '-no-gui', '-q'], bufsize=0,
                                cwd=getcwd()+'/simics-workspace',
                                universal_newlines=True,
                                stdin=PIPE, stdout=PIPE)
            try:
                self.__command()
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as error:
                self.simics.kill()
                with self.db as db:
                    db.log_event('Warning' if attempt < attempts-1 else 'Error',
                                 'Simics', 'Error launching Simics',
                                 db.log_exception)
                print(colored(
                    'error launching simics (attempt {}/{}): {}'.format(
                        attempt, attempts, error), 'red'))
                if attempt < attempts-1:
                    sleep(30)
                elif attempt == attempts-1:
                    raise Exception('error launching simics, check your '
                                    'license connection')
            else:
                with self.db as db:
                    db.log_event('Information', 'Simics', 'Launched Simics',
                                 success=True)
                break
        if checkpoint is None:
            self.__command('$drseus=TRUE')
            buff = self.__command(
                'run-command-file simics-{0}/{0}-linux{1}.simics'.format(
                    self.board, '-ethernet' if self.db.campaign['aux'] else ''))
        else:
            buff = self.__command('read-configuration {}'.format(checkpoint))
            buff += self.__command('connect-real-network-port-in ssh '
                                   'ethernet_switch0 target-ip=10.10.0.100')
            if self.db.campaign['aux']:
                buff += self.__command('connect-real-network-port-in ssh '
                                       'ethernet_switch0 target-ip=10.10.0.104')
        self.__command('enable-real-time-mode')
        found_settings = 0
        if checkpoint is None:
            serial_ports = []
        else:
            serial_ports = [0, 0]
        ssh_ports = []
        for line in buff.split('\n'):
            if 'pseudo device opened: /dev/pts/' in line:
                if checkpoint is None:
                    serial_ports.append(line.split(':')[1].strip())
                else:
                    if 'AUX_' in line:
                        serial_ports[1] = line.split(':')[1].strip()
                    else:
                        serial_ports[0] = line.split(':')[1].strip()
                found_settings += 1
            elif 'Host TCP port' in line:
                ssh_ports.append(int(line.split('->')[0].split()[-1]))
                found_settings += 1
            if not self.db.campaign['aux'] and found_settings == 2:
                break
            elif self.db.campaign['aux'] and found_settings == 4:
                break
        else:
            self.close()
            raise DrSEUsError('Error finding port or pseudoterminal')
        if self.board == 'p2020rdb':
            self.options.aux_prompt = self.options.dut_prompt = \
                'root@p2020rdb:~#'
            if self.options.dut_uboot:
                self.options.dut_uboot += '; '
            self.options.dut_uboot += ('setenv ethaddr 00:01:af:07:9b:8a; '
                                       'setenv eth1addr 00:01:af:07:9b:8b; '
                                       'setenv eth2addr 00:01:af:07:9b:8c; '
                                       'setenv consoledev ttyS0; '
                                       'setenv bootargs root=/dev/ram rw '
                                       'console=$consoledev,$baudrate; '
                                       'bootm ef080000 10000000 ef040000')
            if self.options.aux_uboot:
                self.options.aux_uboot += '; '
            self.options.aux_uboot += ('setenv ethaddr 00:01:af:07:9b:8d; '
                                       'setenv eth1addr 00:01:af:07:9b:8e; '
                                       'setenv eth2addr 00:01:af:07:9b:8f; '
                                       'setenv consoledev ttyS0; '
                                       'setenv bootargs root=/dev/ram rw '
                                       'console=$consoledev,$baudrate; '
                                       'bootm ef080000 10000000 ef040000; ')
        elif self.board == 'a9x2':
            self.options.aux_prompt = self.options.dut_prompt = '\n#'
            if self.options.dut_uboot:
                self.options.dut_uboot += ';'
            self.options.dut_uboot += ('setenv bootargs console=ttyAMA0 '
                                       'root=/dev/ram0 rw;'
                                       'bootm 0x40800000 0x70000000')
            if self.options.aux_uboot:
                self.options.aux_uboot += ';'
            self.options.aux_uboot += ('setenv bootargs console=ttyAMA0 '
                                       'root=/dev/ram0 rw;'
                                       'bootm 0x40800000 0x70000000')
        self.options.dut_serial_port = serial_ports[0]
        self.options.dut_ip_address = '10.10.0.100'
        self.options.dut_scp_port = ssh_ports[0]
        self.dut = dut(self.db, self.options)
        if self.db.campaign['aux']:
            self.options.aux_serial_port = serial_ports[1]
            self.options.aux_ip_address = '10.10.0.104'
            self.options.aux_scp_port = ssh_ports[1]
            self.aux = dut(self.db, self.options, aux=True)
        if checkpoint is None:
            self.continue_dut()
            self.dut.read_until('Hit any key')
            self.halt_dut()
            if self.board == 'p2020rdb':
                self.__command('DUT_p2020rdb.soc.phys_mem.load-file '
                               '$initrd_image $initrd_addr')
                if self.db.campaign['aux']:
                    self.__command('AUX_p2020rdb_1.soc.phys_mem.load-file '
                                   '$initrd_image $initrd_addr')
            elif self.board == 'a9x2':
                self.__command('DUT_a9x2.coretile.mpcore.phys_mem.load-file '
                               '$kernel_image $kernel_addr')
                self.__command('DUT_a9x2.coretile.mpcore.phys_mem.load-file '
                               '$initrd_image $initrd_addr')
                if self.db.campaign['aux']:
                    self.__command('AUX_a9x2_1.coretile.mpcore.phys_mem.'
                                   'load-file $kernel_image $kernel_addr')
                    self.__command('AUX_a9x2_1.coretile.mpcore.phys_mem.'
                                   'load-file $initrd_image $initrd_addr')
            self.continue_dut()
            if self.db.campaign['aux']:
                aux_process = Thread(
                    target=self.aux.do_login,
                    kwargs={'change_prompt': self.board == 'a9x2',
                            'flush': False})
                aux_process.start()
            self.dut.do_login(change_prompt=(self.board == 'a9x2'), flush=False)
            if self.db.campaign['aux']:
                aux_process.join()
        else:
            self.dut.ip_address = '127.0.0.1'
            if self.board == 'a9x2':
                self.dut.prompt = 'DrSEUs# '
            if self.db.campaign['aux']:
                self.aux.ip_address = '127.0.0.1'
                if self.board == 'a9x2':
                    self.aux.prompt = 'DrSEUs# '

    def launch_simics_gui(self, checkpoint):
        dut_board = 'DUT_'+self.board
        if self.board == 'p2020rdb':
            serial_port = 'serial[0]'
        elif self.board == 'a9x2':
            serial_port = 'serial0'
        simics_commands = ('read-configuration '+checkpoint+';'
                           'new-text-console-comp text_console0;'
                           'disconnect '+dut_board+'.console0.serial'
                           ' '+dut_board+'.'+serial_port+';'
                           'connect text_console0.serial'
                           ' '+dut_board+'.'+serial_port+';'
                           'connect-real-network-port-in ssh '
                           'ethernet_switch0 target-ip=10.10.0.100;')
        if self.db.campaign['aux']:
            aux_board = 'AUX_'+self.board+'_1'
            simics_commands += ('new-text-console-comp text_console1;'
                                'disconnect '+aux_board+'.console0.serial'
                                ' '+aux_board+'.'+serial_port+';'
                                'connect text_console1.serial'
                                ' '+aux_board+'.'+serial_port+';'
                                'connect-real-network-port-in ssh '
                                'ethernet_switch0 target-ip=10.10.0.104;')
        call([getcwd()+'/simics-workspace/simics-gui', '-e', simics_commands],
             cwd=getcwd()+'/simics-workspace')

    def close(self):
        if self.simics:
            if self.dut:
                self.dut.close()
                self.dut = None
            if self.aux:
                self.aux.close()
                self.aux = None
            try:
                self.halt_dut()
                self.__command('quit')
            except DrSEUsError as error:
                if error.type == 'Timeout reading from Simics':
                    self.simics.kill()
                    with self.db as db:
                        db.log_event('Warning', 'Simics',
                                     'Killed unresponsive Simics',
                                     db.log_exception)
                    self.simics = None
                    return
            self.simics.wait()
            with self.db as db:
                db.log_event('Information', 'Simics', 'Closed Simics',
                             success=True)
            self.simics = None

    def halt_dut(self):
        if self.running:
            with self.db as db:
                db.log_event('Information', 'Simics', 'Halt DUT')
            self.simics.send_signal(SIGINT)
            self.running = False
            self.__command()

    def continue_dut(self):
        if not self.running:
            self.simics.stdin.write('run\n')
            self.running = True
            if self.db.result:
                self.db.result['debugger_output'] += 'run\n'
            else:
                self.db.campaign['debugger_output'] += 'run\n'
            if self.options.debug:
                print(colored('run', 'yellow'))
            with self.db as db:
                db.log_event('Information', 'Simics', 'Continue DUT',
                             success=True)

    def reset_dut(self):
        pass

    def __command(self, command=None, time=10):

        def read_until():
            buff = ''
            hanging = False
            while True:
                try:
                    with timeout(time):
                        char = self.simics.stdout.read(1)
                except TimeoutException:
                    char = ''
                    hanging = True
                    with self.db as db:
                        db.log_event('Warning', 'Simics', 'Read timeout',
                                     db.log_exception)
                if not char:
                    break
                if self.db.result:
                    self.db.result['debugger_output'] += char
                else:
                    self.db.campaign['debugger_output'] += char
                if self.options.debug:
                    print(colored(char, 'yellow'), end='')
                    stdout.flush()
                buff += char
                if buff.endswith('simics> '):
                    break
            if self.options.debug:
                print()
            with self.db as db:
                if self.db.result:
                    db.update('result')
                else:
                    db.update('campaign')
            for message in self.error_messages:
                if message in buff:
                    with self.db as db:
                        db.log_event('Error', 'Simics', message, buff)
                    raise DrSEUsError(message)
            if hanging:
                raise DrSEUsError('Timeout reading from Simics')
            return buff

    # def __command(self, command=None, time=10):
        if command:
            with self.db as db:
                event = db.log_event('Information', 'Simics', 'Command',
                                     command, success=False)
        if command is not None:
            self.simics.stdin.write(command+'\n')
            if self.db.result:
                self.db.result['debugger_output'] += command+'\n'
            else:
                self.db.campaign['debugger_output'] += command+'\n'
            if self.options.debug:
                print(colored(command, 'yellow'))
        buff = read_until()
        if command:
            with self.db as db:
                db.log_event_success(event)
        return buff

    def __merge_checkpoint(self, checkpoint):
        if self.options.debug:
            print(colored('merging checkpoint...', 'blue'), end='')
            stdout.flush()
        merged_checkpoint = checkpoint+'_merged'
        check_call([getcwd()+'/simics-workspace/bin/checkpoint-merge',
                    checkpoint, merged_checkpoint],
                   cwd=getcwd()+'/simics-workspace', stdout=DEVNULL)
        if self.options.debug:
            print(colored('done', 'blue'))
        return merged_checkpoint

    def get_time(self):
        time_data = self.__command('print-time').split('\n')[-2].split()
        return int(time_data[2]), float(time_data[3])

    def time_application(self):

        def create_checkpoints():
            with self.db as db:
                event = db.log_event('Information', 'Simics',
                                     'Created gold checkpoints', success=False,
                                     campaign=True)
            makedirs('simics-workspace/gold-checkpoints/{}'.format(
                self.db.campaign['id']))
            if self.db.campaign['command']:
                self.db.campaign['cycles_between'] = \
                    int(self.db.campaign['cycles'] / self.options.checkpoints)
                if self.db.campaign['aux']:
                    with self.db as db:
                        db.log_event('Information', 'AUX', 'Command',
                                     self.db.campaign['aux_command'])
                    aux_process = Thread(
                        target=self.aux.command,
                        kwargs={'command': self.db.campaign['aux_command'],
                                'flush': False})
                    aux_process.start()
                with self.db as db:
                    db.log_event('Information', 'DUT', 'Command',
                                 self.db.campaign['command'])
                self.dut.write('{}\n'.format(self.db.campaign['command']))
                read_thread = Thread(target=self.dut.read_until,
                                     kwargs={'flush': False})
                read_thread.start()
                checkpoint = 0
                while True:
                    checkpoint += 1
                    self.__command('run-cycles {}'.format(
                        self.db.campaign['cycles_between']), time=300)
                    self.db.campaign['dut_output'] += '\n{:*^80}\n\n'.format(
                        ' Checkpoint {} '.format(checkpoint))
                    incremental_checkpoint = 'gold-checkpoints/{}/{}'.format(
                        self.db.campaign['id'], checkpoint)
                    self.__command('write-configuration {}'.format(
                        incremental_checkpoint), time=300)
                    if not read_thread.is_alive() or \
                        (self.db.campaign['aux'] and
                            self.db.campaign['kill_dut'] and
                            not aux_process.is_alive()):
                        self.__merge_checkpoint(incremental_checkpoint)
                        break
                self.db.campaign['checkpoints'] = checkpoint
                with self.db as db:
                    db.log_event_success(event, update_timestamp=True)
                self.continue_dut()
                if self.db.campaign['aux']:
                    aux_process.join()
                if self.db.campaign['kill_dut']:
                    self.dut.write('\x03')
                read_thread.join()
            else:
                self.db.campaign['checkpoints'] = 1
                self.halt_dut()
                self.__command(
                    'write-configuration gold-checkpoints/{}/1'.format(
                        self.db.campaign['id']), time=300)

    # def time_application(self):
        if self.db.campaign['command']:
            with self.db as db:
                event = db.log_event('Information', 'Simics',
                                     'Timed application', success=False,
                                     campaign=True)
            self.halt_dut()
            start_cycles, start_time = self.get_time()
            self.continue_dut()
            for i in range(self.options.iterations):
                if self.db.campaign['aux']:
                    aux_process = Thread(
                        target=self.aux.command,
                        kwargs={'command': self.db.campaign['aux_command'],
                                'flush': False})
                    aux_process.start()
                dut_process = Thread(
                    target=self.dut.command,
                    kwargs={'command': self.db.campaign['command'],
                            'flush': False})
                dut_process.start()
                if self.db.campaign['aux']:
                    aux_process.join()
                if self.db.campaign['kill_dut']:
                    self.dut.write('\x03')
                dut_process.join()
            self.halt_dut()
            end_cycles, end_time = self.get_time()
            self.db.campaign['start_cycle'] = end_cycles
            self.db.campaign['start_time'] = end_time
            self.db.campaign['cycles'] = \
                int((end_cycles - start_cycles) / self.options.iterations)
            self.db.campaign['execution_time'] = \
                (end_time - start_time) / self.options.iterations
            with self.db as db:
                db.log_event_success(event, update_timestamp=True)
        create_checkpoints()

    def inject_faults(self):

        def persistent_faults():
            with self.db as db:
                injections = \
                    db.get_item('injection')
                register_diffs = db.get_item('simics_register_diff')
                memory_diffs = db.get_count('simics_memory_diff')
            if memory_diffs > 0:
                return False
            for register_diff in register_diffs:
                for injection in injections:
                    if injection['register_index'] is None:
                        injected_register = injection['register']
                    else:
                        injected_register = '{}:{}'.format(
                            injection['register'],
                            ':'.join(map(str, injection['register_index'])))
                    if register_diff['config_object'] == \
                        injection['config_object'] and \
                            register_diff['register'] == injected_register:
                        if (int(register_diff['monitored_value'], base=0) ==
                                int(injection['injected_value'], base=0)):
                            break
                else:
                    return False
            else:
                return True

    # def inject_faults(self):
        checkpoint_nums = list(range(1, self.db.campaign['checkpoints']))
        checkpoints_to_inject = []
        for i in range(self.options.injections):
            checkpoint_num = choice(checkpoint_nums)
            checkpoint_nums.remove(checkpoint_num)
            checkpoints_to_inject.append(checkpoint_num)
        checkpoints_to_inject = sorted(checkpoints_to_inject)
        latent_faults = 0
        if checkpoints_to_inject:
            for injection_number, checkpoint in \
                    enumerate(checkpoints_to_inject, start=1):
                injected_checkpoint = self.__inject_checkpoint(injection_number,
                                                               checkpoint)
                self.launch_simics(injected_checkpoint)
                injections_remaining = \
                    injection_number < len(checkpoints_to_inject)
                if injections_remaining:
                    next_checkpoint = checkpoints_to_inject[injection_number]
                else:
                    next_checkpoint = self.db.campaign['checkpoints']
                errors = self.__compare_checkpoints(checkpoint, next_checkpoint)
                if errors > latent_faults:
                    latent_faults = errors
                if injections_remaining:
                    self.close()
                else:
                    self.continue_dut()
        else:
            self.close()
            makedirs('simics-workspace/injected-checkpoints/{}/{}'.format(
                self.db.campaign['id'], self.db.result['id']))
            self.launch_simics('gold-checkpoints/{}/1'.format(
                self.db.campaign['id']))
            latent_faults = \
                self.__compare_checkpoints(1, self.db.campaign['checkpoints'])
        return latent_faults, (latent_faults and persistent_faults())

    def regenerate_checkpoints(self, injections):
        self.db.result['id'] = self.options.result_id
        for injection_number, injection in enumerate(injections, start=1):
            injected_checkpoint = self.__inject_checkpoint(
                injection_number, injection['checkpoint'], injection)
            if injection_number < len(injections):
                self.launch_simics(checkpoint=injected_checkpoint)
                for j in range(injection['checkpoint'],
                               injections[injection_number]['checkpoint']):
                    self.__command('run-cycles {}'.format(
                        self.db.campaign['cycles_between']), time=300)
                self.__command(
                    'write-configuration injected-checkpoints/{}/{}/{}'.format(
                        self.db.campaign['id'], self.options.result_id,
                        injections[injection_number]['checkpoint']), time=300)
                self.close()
        return injected_checkpoint

    def __inject_checkpoint(self, injection_number, checkpoint, injection=None):

        def inject_config(injected_checkpoint, injection):

            def flip_bit(value, bit):
                num_bits = get_num_bits(
                    injection['register'], injection['target'], self.targets)
                if bit >= num_bits or bit < 0:
                    raise Exception('invalid bit: {} for num_bits: {}'.format(
                        bit, num_bits))
                value = int(value, base=0)
                binary_list = list(bin(value)[2:].zfill(num_bits))
                binary_list[num_bits-1-bit] = (
                    '1' if binary_list[num_bits-1-bit] == '0' else '0')
                injected_value = int(''.join(binary_list), 2)
                injected_value = hex(injected_value).rstrip('L')
                return injected_value

        # def inject_config(injected_checkpoint, injection):
            with simics_config(injected_checkpoint) as config:
                config_object = injection['config_object']
                if 'register_alias' in injection:
                    register = injection['register_alias']
                else:
                    register = injection['register']
                gold_value = config.get(config_object, register)
                if gold_value is None:
                    raise Exception('error getting register value from config')
                if 'register_index' in injection:
                    register_list_ = register_list = gold_value
                    if 'injected_value' not in injection:
                        for index in injection['register_index']:
                            gold_value = gold_value[index]
                        injected_value = flip_bit(gold_value, injection['bit'])
                    for index in range(len(injection['register_index'])-1):
                        register_list_ = \
                            register_list_[injection['register_index'][index]]
                    register_list_[injection['register_index'][-1]] = \
                        injected_value
                    config.set(config_object, register, register_list)
                else:
                    if 'injected_value' not in injection:
                        injected_value = flip_bit(gold_value, injection['bit'])
                    config.set(config_object, register, injected_value)
                config.save()
            return gold_value, injected_value

    # def __inject_checkpoint(self, injection_number, checkpoint,
    #                         injection=None):
        if injection_number == 1:
            gold_checkpoint = 'simics-workspace/gold-checkpoints/{}/{}'.format(
                self.db.campaign['id'], checkpoint)
        else:
            gold_checkpoint = \
                'simics-workspace/injected-checkpoints/{}/{}/{}'.format(
                    self.db.campaign['id'], self.db.result['id'], checkpoint)
        injected_checkpoint = \
            'simics-workspace/injected-checkpoints/{}/{}/{}_injected'.format(
                self.db.campaign['id'], self.db.result['id'], checkpoint)
        makedirs(injected_checkpoint)
        checkpoint_files = listdir(gold_checkpoint)
        for checkpoint_file in checkpoint_files:
            copyfile('{}/{}'.format(gold_checkpoint, checkpoint_file),
                     '{}/{}'.format(injected_checkpoint, checkpoint_file))
        if injection is None:
            injection = choose_injection(self.targets,
                                         self.options.selected_target_indices)
            config_object = 'DUT_{}.{}'.format(
                self.board, self.targets[injection['target']]['object'])
            if 'target_index' in injection:
                config_object += '[{}]'.format(injection['target_index'])
            injection.update({'checkpoint': checkpoint,
                              'config_object': config_object,
                              'result_id': self.db.result['id'],
                              'success': False,
                              'timestamp': None})
            with self.db as db:
                db.insert('injection', injection)
            try:
                injection['gold_value'], injection['injected_value'] = \
                    inject_config(injected_checkpoint, injection)
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except:
                with self.db as db:
                    db.update('injection', injection)
                    db.log_event('Error', 'Simics', 'Error injecting fault',
                                 db.log_exception, success=False)
                raise DrSEUsError('Error injecting fault')
            else:
                injection['success'] = True
                with self.db as db:
                    db.update('injection', injection)
                    db.log_event('Information', 'Simics', 'Fault injected',
                                 success=True)
            if self.options.debug:
                print(colored(
                    'result id: {}\ncheckpoint number: {}\ntarget: {}'.format(
                        self.db.result['id'], checkpoint,  injection['target']),
                    'magenta'))
                if 'target_index' in injection:
                    print(colored('target_index: {}'.format(
                        injection['target_index']), 'magenta'))
                print(colored(
                    'register: {}\nbit: {}\ngold value: {}\ninjected value: {}'
                    ''.format(injection['register'], injection['bit'],
                              injection['gold_value'],
                              injection['injected_value']), 'magenta'))
        else:
            inject_config(injected_checkpoint, injection)
        return injected_checkpoint.replace('simics-workspace/', '')

    def __compare_checkpoints(self, checkpoint, last_checkpoint):

        def compare_registers(checkpoint, gold_checkpoint,
                              monitored_checkpoint):
            """
            Compares the register values of the checkpoint for iteration
            to the gold_checkpoint and adds the differences to the database.
            """

            def get_registers(checkpoint):
                """
                Retrieves all the register values of the targets specified in
                simics_targets.py for the specified checkpoint and returns a
                dictionary with all the values.
                """
                with simics_config('simics-workspace/'+checkpoint) as config:
                    registers = {}
                    for target in self.targets:
                        if 'count' in self.targets[target]:
                            count = self.targets[target]['count']
                        else:
                            count = 1
                        for target_index in range(count):
                            config_object = 'DUT_{}.{}'.format(
                                self.board, self.targets[target]['object'])
                            if count > 1:
                                config_object += '[{}]'.format(target_index)
                            if config_object not in registers:
                                registers[config_object] = {}
                            for register in self.targets[target]['registers']:
                                if 'alias' in (self.targets[target]['registers']
                                                           [register]):
                                    register = \
                                        (self.targets[target]['registers']
                                                     [register]['alias']
                                                     ['register'])
                                if register not in registers[config_object]:
                                    registers[config_object][register] = \
                                        config.get(config_object, register)
                return registers

            # watch out! we're gonna use recursion
            # keep your arms and legs inside the stack frame at all times
            def log_diffs(db, config_object, register, gold_value,
                          monitored_value):
                if isinstance(gold_value, list):
                    for index in range(len(gold_value)):
                        log_diffs(db, config_object,
                                  '{}:{}'.format(register, index),
                                  gold_value[index], monitored_value[index])
                else:
                    if int(monitored_value, base=0) != int(gold_value, base=0):
                        register_diff = {
                            'result_id': self.db.result['id'],
                            'checkpoint': checkpoint,
                            'config_object': config_object,
                            'register': register,
                            'gold_value': gold_value,
                            'monitored_value': monitored_value}
                        db.insert('simics_register_diff', register_diff)

        # def compare_registers(checkpoint, gold_checkpoint,
        #                       monitored_checkpoint):
            # import pprint
            gold_registers = get_registers(gold_checkpoint)
            # with open('gold_regs.txt', 'w') as gold_out:
            #     pp = pprint.PrettyPrinter(indent=4, stream=gold_out)
            #     pp.pprint(gold_registers)
            monitored_registers = get_registers(monitored_checkpoint)
            # with open('mon_regs.txt', 'w') as mon_out:
            #     pp = pprint.PrettyPrinter(indent=4, stream=mon_out)
            #     pp.pprint(monitored_registers)
            with self.db as db:
                for config_object in gold_registers:
                    for register in gold_registers[config_object]:
                        log_diffs(db, config_object, register,
                                  gold_registers[config_object][register],
                                  monitored_registers[config_object][register])
                diffs = db.get_count('simics_register_diff')
            return diffs

        def compare_memory(checkpoint, gold_checkpoint, monitored_checkpoint):
            """
            Compare the memory contents of gold_checkpoint with
            monitored_checkpoint and return the list of blocks that do not
            match. If extract_blocks is true then extract any blocks that do not
            match to incremental_checkpoint/memory-blocks/.
            """

            def parse_content_map(content_map, block_size):
                """
                Parse a content_map created by the Simics craff utility and
                returns a list of the addresses of the image that contain data.
                """
                with open('simics-workspace/'+content_map, 'r') as content_map:
                    diff_addresses = []
                    for line in content_map:
                        if 'empty' not in line:
                            line = line.split()
                            base_address = int(line[0], 16)
                            offsets = [index for index, value
                                       in enumerate(line[1]) if value == 'D']
                            for offset in offsets:
                                diff_addresses.append(base_address +
                                                      offset*block_size)
                return diff_addresses

            def extract_diff_blocks(gold_ram, monitored_ram,
                                    incremental_checkpoint, addresses,
                                    block_size):
                """
                Extract all of the blocks of size block_size specified in
                addresses of both the gold_ram image and the monitored_ram
                image.
                """
                if len(addresses) > 0:
                    mkdir('{}/memory-blocks'.format(incremental_checkpoint))
                    for address in addresses:
                        check_call([craff, gold_ram,
                                    '--extract={:#x}'.format(address),
                                    '--extract-block-size={}'.format(
                                        block_size),
                                    '--output={}/memory-blocks/{:#x}_gold.raw'
                                    ''.format(incremental_checkpoint, address)],
                                   cwd=cwd)
                        check_call([craff,  monitored_ram,
                                    '--extract={:#x}'.format(address),
                                    '--extract-block-size={}'.format(
                                        block_size),
                                    '--output={}/memory-blocks/{:#x}_monitored'
                                    '.raw'.format(incremental_checkpoint,
                                                  address)],
                                   cwd=cwd)

        # def compare_memory(checkpoint, gold_checkpoint, monitored_checkpoint):
            if self.board == 'p2020rdb':
                gold_rams = '{}/DUT_{}.soc.ram_image[0].craff'.format(
                    gold_checkpoint, self.board)
                monitored_rams = '{}/DUT_{}.soc.ram_image[0].craff'.format(
                    monitored_checkpoint, self.board)
            elif self.board == 'a9x2':
                gold_rams = ['{}/DUT_{}.coretile.ddr_image[{}].craff'.format(
                    gold_checkpoint, self.board, index) for index in range(2)]
                monitored_rams = [
                    '{}/DUT_{}.coretile.ddr_image[{}].craff'.format(
                        monitored_checkpoint, self.board, index)
                    for index in range(2)]
            ram_diffs = ['{}.diff'.format(ram) for ram in monitored_rams]
            diff_content_maps = ['{}.content_map'.format(diff)
                                 for diff in ram_diffs]
            diffs = 0
            memory_diff = {'result_id': self.db.result['id'],
                           'checkpoint': checkpoint}
            cwd = '{}/simics-workspace'.format(getcwd())
            craff = '{}/bin/craff'.format(cwd)
            with self.db as db:
                for (memory_diff['image_index'], gold_ram, monitored_ram,
                     ram_diff, diff_content_map) in zip(
                        range(len(monitored_rams)), gold_rams, monitored_rams,
                        ram_diffs, diff_content_maps):
                    check_call([craff, '--diff', gold_ram, monitored_ram,
                                '--output={}'.format(ram_diff)],
                               cwd=cwd, stdout=DEVNULL)
                    check_call([craff, '--content-map', ram_diff,
                                '--output='+diff_content_map],
                               cwd=cwd, stdout=DEVNULL)
                    craff_output = check_output([craff, '--info', ram_diff],
                                                cwd=cwd,
                                                universal_newlines=True)
                    block_size = int(findall(r'\d+',
                                             craff_output.split('\n')[2])[1])
                    changed_blocks = parse_content_map(diff_content_map,
                                                       block_size)
                    diffs += len(changed_blocks)
                    if self.options.extract_blocks:
                        extract_diff_blocks(gold_ram, monitored_ram,
                                            monitored_checkpoint,
                                            changed_blocks, block_size)
                    for block in changed_blocks:
                        memory_diff['block'] = hex(block)
                        db.insert('simics_memory_diff', memory_diff)
            return diffs

    # def __compare_checkpoints(self, checkpoint, last_checkpoint):
        reg_errors = 0
        mem_errors = 0
        if self.options.compare_all:
            checkpoints = range(checkpoint+1, last_checkpoint+1)
            cycles_between = self.db.campaign['cycles_between']
        else:
            checkpoints = [last_checkpoint]
            cycles_between = self.db.campaign['cycles_between'] * \
                (last_checkpoint-checkpoint)
        for checkpoint in checkpoints:
            self.__command('run-cycles {}'.format(cycles_between),
                           time=300 if self.options.compare_all else 600)
            incremental_checkpoint = 'injected-checkpoints/{}/{}/{}'.format(
                self.db.campaign['id'], self.db.result['id'], checkpoint)
            monitor = self.options.compare_all or \
                checkpoint == self.db.campaign['checkpoints']
            if monitor or checkpoint == last_checkpoint:
                self.__command('write-configuration {}'.format(
                    incremental_checkpoint), time=300)
            if monitor:
                monitored_checkpoint = \
                    self.__merge_checkpoint(incremental_checkpoint)
                gold_incremental_checkpoint = 'gold-checkpoints/{}/{}'.format(
                    self.db.campaign['id'], checkpoint)
                gold_checkpoint = '{}_merged'.format(
                    gold_incremental_checkpoint)
                if not exists('simics-workspace/{}'.format(gold_checkpoint)):
                    self.__merge_checkpoint(gold_incremental_checkpoint)
                errors = compare_registers(
                    checkpoint, gold_checkpoint, monitored_checkpoint)
                if errors > reg_errors:
                    reg_errors = errors
                errors = compare_memory(
                    checkpoint, gold_checkpoint, monitored_checkpoint)
                if errors > reg_errors:
                    mem_errors = errors
        return reg_errors + mem_errors
