from os import getcwd, listdir, makedirs, mkdir
from os.path import exists
from random import choice, randrange
from re import findall
from shutil import copyfile
from signal import SIGINT
from subprocess import call, check_call, check_output, DEVNULL, PIPE, Popen
from sys import stdout
from termcolor import colored
from threading import Thread
from time import sleep, time

from dut import dut
from error import DrSEUsError
from simics_config import simics_config
from simics_targets import devices
from targets import choose_register, choose_target


class simics(object):
    error_messages = ['Address not mapped', 'Illegal Instruction',
                      'Illegal instruction', 'Illegal memory mapping',
                      'Illegal Memory Mapping', 'Error setting attribute',
                      'dropping memop (peer attribute not set)',
                      'where nothing is mapped', 'Error']

    def __init__(self, database, options):
        self.simics = None
        self.db = database
        self.options = options
        if database.campaign['architecture'] == 'p2020':
            self.board = 'p2020rdb'
        elif database.campaign['architecture'] == 'a9':
            self.board = 'a9x2'
        self.targets = devices[self.board]
        if options.command == 'inject' and options.selected_targets is not None:
            for target in options.selected_targets:
                if target not in self.targets:
                    raise Exception('invalid injection target: '+target)
        if options.command == 'new':
            self.__launch_simics()
        elif options.command == 'supervise':
            self.__launch_simics(
                'gold-checkpoints/'+str(database.campaign['id'])+'/' +
                str(database.campaign['num_checkpoints'])+'_merged')
            self.continue_dut()

    def __str__(self):
        string = 'Simics simulation of '+self.board
        return string

    def __launch_simics(self, checkpoint=None):
        attempts = 10
        for attempt in range(attempts):
            self.simics = Popen([getcwd()+'/simics-workspace/simics',
                                 '-no-win', '-no-gui', '-q'], bufsize=0,
                                cwd=getcwd()+'/simics-workspace',
                                universal_newlines=True,
                                stdin=PIPE, stdout=PIPE)
            try:
                self.__command()
            except Exception as error:
                self.simics.kill()
                with self.db as db:
                    db.log_event('Warning' if attempt < attempts-1 else 'Error',
                                 'Simics', 'Error launching Simics',
                                 db.log_exception)
                print(colored(
                    'error launching simics (attempt '+str(attempt+1)+'/' +
                    str(attempts)+'): '+str(error), 'red'))
                if attempt < attempts-1:
                    sleep(30)
                elif attempt == attempts-1:
                    raise Exception('error launching simics, check your '
                                    'license connection')
            else:
                with self.db as db:
                    db.log_event('Information', 'Simics', 'Launched Simics',
                                 checkpoint, success=True)
                break
        if checkpoint is None:
            self.__command('$drseus=TRUE')
            buff = self.__command(
                'run-command-file simics-'+self.board+'/'+self.board+'-linux' +
                ('-ethernet' if self.db.campaign['aux'] else '') +
                '.simics')
        else:
            buff = self.__command('read-configuration '+checkpoint)
            buff += self.__command('connect-real-network-port-in ssh '
                                   'ethernet_switch0 target-ip=10.10.0.100')
            if self.db.campaign['aux']:
                buff += self.__command('connect-real-network-port-in ssh '
                                       'ethernet_switch0 target-ip=10.10.0.104')
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
                aux_process = Thread(target=self.aux.do_login,
                                     args=[self.board == 'a9x2'])
                aux_process.start()
            self.dut.do_login(change_prompt=(self.board == 'a9x2'))
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
            self.dut.close()
            if self.db.campaign['aux']:
                self.aux.close()
            self.simics.send_signal(SIGINT)
            try:
                self.__command()
                self.__command('quit')
            except:
                self.simics.kill()
                with self.db as db:
                    db.log_event('Warning', 'Simics',
                                 'Killed unresponsive Simics', db.log_exception)
            else:
                self.simics.wait()
                with self.db as db:
                    db.log_event('Information', 'Simics', 'Closed Simics',
                                 success=True)
            self.simics = None

    def halt_dut(self):
        self.simics.send_signal(SIGINT)
        self.__command()
        with self.db as db:
            db.log_event('Information', 'Simics', 'Halt DUT', success=True)
        return True

    def continue_dut(self):
        self.simics.stdin.write('run\n')
        if self.db.result:
            self.db.result['debugger_output'] += 'run\n'
        else:
            self.db.campaign['debugger_output'] += 'run\n'
        if self.options.debug:
            print(colored('run', 'yellow'))
        with self.db as db:
            db.log_event('Information', 'Simics', 'Continue DUT', success=True)

    def __command(self, command=None):

        def read_until():

            def read_char():
                self.char = None

                def read_char_worker():
                    if self.simics:
                        self.char = \
                            self.simics.stdout.read(1)

            # def read_char():
                read_thread = Thread(target=read_char_worker)
                read_thread.start()
                read_thread.join(timeout=10)
                if read_thread.is_alive():
                    with self.db as db:
                        db.log_event('Warning', 'Simics', 'Read timeout',
                                     db.log_trace)
                    raise DrSEUsError('Timeout reading from simics')
                return self.char

        # def read_until():
            buff = ''
            while True:
                char = read_char()
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
                if buff[-len('simics> '):] == 'simics> ':
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
            return buff

    # def __command(self, command=None):
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

    def time_application(self):

        def create_checkpoints():
            with self.db as db:
                event = db.log_event('Information', 'Simics',
                                     'Created gold checkpoints', success=False,
                                     campaign=True)
            makedirs('simics-workspace/gold-checkpoints/' +
                     str(self.db.campaign['id']))
            self.db.campaign['cycles_between'] = \
                int(self.db.campaign['num_cycles'] / self.options.checkpoints)
            self.halt_dut()
            if self.db.campaign['aux']:
                    aux_process = Thread(
                        target=self.aux.command,
                        args=('./'+self.db.campaign['aux_command'], ))
                    aux_process.start()
            self.dut.write('./'+self.db.campaign['command']+'\n')
            read_thread = Thread(target=self.dut.read_until)
            read_thread.start()
            checkpoint = 0
            while True:
                checkpoint += 1
                self.__command('run-cycles ' +
                               str(self.db.campaign['cycles_between']))
                self.db.campaign['dut_output'] += \
                    '\n***drseus_checkpoint: '+str(checkpoint)+'***\n'
                incremental_checkpoint = ('gold-checkpoints/' +
                                          str(self.db.campaign['id'])+'/' +
                                          str(checkpoint))
                self.__command('write-configuration '+incremental_checkpoint)
                if not read_thread.is_alive() or \
                    (self.db.campaign['aux'] and
                        self.db.campaign['kill_dut'] and
                        not aux_process.is_alive()):
                    self.__merge_checkpoint(incremental_checkpoint)
                    break
            self.db.campaign['num_checkpoints'] = checkpoint
            with self.db as db:
                db.log_event_success(event)
            self.continue_dut()
            if self.db.campaign['aux']:
                aux_process.join()
            if self.db.campaign['kill_dut']:
                self.dut.serial.write('\x03')
            read_thread.join()

    # def time_application(self):
        with self.db as db:
            event = db.log_event('Information', 'Simics', 'Timed application',
                                 success=False, campaign=True)
        self.halt_dut()
        time_data = self.__command('print-time').split('\n')[-2].split()
        start_cycles = int(time_data[2])
        start_sim_time = float(time_data[3])
        start_time = time()
        self.continue_dut()
        for i in range(self.options.iterations):
            if self.db.campaign['aux']:
                aux_process = Thread(
                    target=self.aux.command,
                    args=('./'+self.db.campaign['aux_command'], ))
                aux_process.start()
            dut_process = Thread(
                target=self.dut.command,
                args=('./'+self.db.campaign['command'], ))
            dut_process.start()
            if self.db.campaign['aux']:
                aux_process.join()
            if self.db.campaign['kill_dut']:
                self.dut.serial.write('\x03')
            dut_process.join()
        self.halt_dut()
        end_time = time()
        time_data = self.__command('print-time').split('\n')[-2].split()
        end_cycles = int(time_data[2])
        end_sim_time = float(time_data[3])
        self.continue_dut()
        self.db.campaign['exec_time'] = \
            (end_time - start_time) / self.options.iterations
        self.db.campaign['num_cycles'] = \
            int((end_cycles - start_cycles) / self.options.iterations)
        self.db.campaign['sim_time'] = \
            (end_sim_time - start_sim_time) / self.options.iterations
        with self.db as db:
            db.log_event_success(event)
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
                    if injection['register_index']:
                        injected_register = (injection['register']+':' +
                                             injection['register_index'])
                    else:
                        injected_register = injection['register']
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
        checkpoint_nums = list(range(1, self.db.campaign['num_checkpoints']))
        checkpoints_to_inject = []
        for i in range(self.options.injections):
            checkpoint_num = choice(checkpoint_nums)
            checkpoint_nums.remove(checkpoint_num)
            checkpoints_to_inject.append(checkpoint_num)
        checkpoints_to_inject = sorted(checkpoints_to_inject)
        latent_faults = 0
        for injection_number, checkpoint_number in \
                enumerate(checkpoints_to_inject, start=1):
            injected_checkpoint = self.__inject_checkpoint(injection_number,
                                                           checkpoint_number)
            self.__launch_simics(injected_checkpoint)
            injections_remaining = injection_number < len(checkpoints_to_inject)
            if injections_remaining:
                next_checkpoint = checkpoints_to_inject[injection_number]
            else:
                next_checkpoint = self.db.campaign['num_checkpoints']
            errors = self.__compare_checkpoints(checkpoint_number,
                                                next_checkpoint)
            if errors > latent_faults:
                latent_faults = errors
            if injections_remaining:
                self.close()
        return latent_faults, (latent_faults and persistent_faults())

    def regenerate_checkpoints(self, injections):
        self.db.result['id'] = self.options.result_id
        for i in range(len(injections)):
            injected_checkpoint = self.__inject_checkpoint(
                injections[i]['injection_number'],
                injections[i]['checkpoint_number'], injections[i])
            if i < len(injections) - 1:
                self.__launch_simics(checkpoint=injected_checkpoint)
                for j in range(injections[i]['checkpoint_number'],
                               injections[i+1]['checkpoint_number']):
                    self.__command('run-cycles ' +
                                   str(self.db.campaign['cycles_between']))
                self.__command('write-configuration injected-checkpoints/' +
                               str(self.db.campaign['id'])+'/' +
                               str(self.options.result_id)+'/' +
                               str(injections[i+1]['checkpoint_number']))
                self.close()
        return injected_checkpoint

    def __inject_checkpoint(self, injection_number, checkpoint_number,
                            previous_injection=None):
        """
        Create a new injected checkpoint (only performing injection on the
        selected_targets if provided) and return the path of the injected
        checkpoint.
        """

        def inject_register(injected_checkpoint, register, target):
            """
            Creates config file for injected_checkpoint with an injected value
            for the register of the target in the gold_checkpoint and return the
            injection information.
            """

            def flip_bit(value_to_inject, num_bits_to_inject, bit_to_inject):
                """
                Flip the bit_to_inject of the binary representation of
                value_to_inject and return the new value.
                """
                if bit_to_inject >= num_bits_to_inject or bit_to_inject < 0:
                    raise DrSEUsError('invalid bit_to_inject: ' +
                                      str(bit_to_inject) +
                                      ' for num_bits_to_inject: ' +
                                      str(num_bits_to_inject))
                value_to_inject = int(value_to_inject, base=0)
                binary_list = list(
                    str(bin(value_to_inject))[2:].zfill(num_bits_to_inject))
                binary_list[num_bits_to_inject-1-bit_to_inject] = (
                    '1'
                    if binary_list[num_bits_to_inject-1-bit_to_inject] == '0'
                    else '0')
                injected_value = int(''.join(binary_list), 2)
                injected_value = hex(injected_value).rstrip('L')
                return injected_value

        # def inject_register(injected_checkpoint, register, target):
            if previous_injection is None:
                # create injection
                injection = {}
                injection['register'] = register
                if ':' in target:
                    target_index = target.split(':')[1]
                    target = target.split(':')[0]
                    config_object = ('DUT_'+self.board +
                                     self.targets[target]['OBJECT'] +
                                     '['+target_index+']')
                else:
                    target_index = None
                    config_object = \
                        'DUT_'+self.board+self.targets[target]['OBJECT']
                injection['target_index'] = target_index
                injection['target'] = target
                injection['config_object'] = config_object
                if 'count' in self.targets[target]['registers'][register]:
                    register_index = []
                    for dimension in (self.targets[target]['registers']
                                                  [register]['count']):
                        index = randrange(dimension)
                        register_index.append(index)
                else:
                    register_index = None
                # choose bit_to_inject and TLB field_to_inject
                if ('is_tlb' in self.targets[target]['registers'][register] and
                        self.targets[target]['registers'][register]['is_tlb']):
                    fields = \
                        self.targets[target]['registers'][register]['fields']
                    field_to_inject = None
                    fields_list = []
                    total_bits = 0
                    for field in fields:
                        bits = fields[field]['bits']
                        fields_list.append((field, bits))
                        total_bits += bits
                    random_bit = randrange(total_bits)
                    bit_sum = 0
                    for field in fields_list:
                        bit_sum += field[1]
                        if random_bit < bit_sum:
                            field_to_inject = field[0]
                            break
                    else:
                        raise DrSEUsError('Error choosing TLB field to inject')
                    injection['field'] = field_to_inject
                    if 'split' in fields[field_to_inject] and \
                            fields[field_to_inject]['split']:
                        total_bits = (fields[field_to_inject]['bits_h'] +
                                      fields[field_to_inject]['bits_l'])
                        random_bit = randrange(total_bits)
                        if random_bit < fields[field_to_inject]['bits_l']:
                            register_index[-1] = \
                                fields[field_to_inject]['index_l']
                            start_bit_index = \
                                fields[field_to_inject]['bit_indicies_l'][0]
                            end_bit_index = \
                                fields[field_to_inject]['bit_indicies_l'][1]
                        else:
                            register_index[-1] = \
                                fields[field_to_inject]['index_h']
                            start_bit_index = \
                                fields[field_to_inject]['bit_indicies_h'][0]
                            end_bit_index = \
                                fields[field_to_inject]['bit_indicies_h'][1]
                    else:
                        register_index[-1] = fields[field_to_inject]['index']
                        start_bit_index = \
                            fields[field_to_inject]['bit_indicies'][0]
                        end_bit_index = \
                            fields[field_to_inject]['bit_indicies'][1]
                    num_bits_to_inject = 32
                    bit_to_inject = randrange(start_bit_index, end_bit_index+1)
                else:
                    if 'bits' in self.targets[target]['registers'][register]:
                        num_bits_to_inject = \
                            self.targets[target]['registers'][register]['bits']
                    else:
                        num_bits_to_inject = 32
                    bit_to_inject = randrange(num_bits_to_inject)
                    if 'adjust_bit' in \
                            self.targets[target]['registers'][register]:
                        bit_to_inject = (self.targets[target]['registers']
                                                     [register]['adjust_bit']
                                                     [bit_to_inject])
                    if 'actualBits' in \
                            self.targets[target]['registers'][register]:
                        num_bits_to_inject = \
                            (self.targets[target]['registers']
                                         [register]['actualBits'])
                    if 'fields' in self.targets[target]['registers'][register]:
                        for field_name, field_bounds in \
                            (self.targets[target]['registers']
                                         [register]['fields'].items()):
                            if bit_to_inject in range(field_bounds[0],
                                                      field_bounds[1]+1):
                                field_to_inject = field_name
                                break
                        else:
                            with self.db as db:
                                db.log_event('Warning', 'Simics',
                                             'Error finding register field '
                                             'name',
                                             'target: '+target +
                                             ', register: '+register +
                                             ', bit: '+str(bit_to_inject))
                        injection['field'] = field_to_inject
                    else:
                        injection['field'] = None
                injection['bit'] = bit_to_inject
                if register_index is not None:
                    injection['register_index'] = ''
                    for index in register_index:
                        injection['register_index'] += str(index)+':'
                    injection['register_index'] = \
                        injection['register_index'][:-1]
                else:
                    injection['register_index'] = None
            else:
                # use previous injection data
                config_object = previous_injection['config_object']
                register = previous_injection['register']
                register_index = previous_injection['register_index']
                if register_index is not None:
                    register_index = [int(index) for index
                                      in register_index.split(':')]
                injection = {}
                injected_value = previous_injection['injected_value']
            # perform checkpoint injection
            with simics_config(injected_checkpoint) as config:
                gold_value = config.get(config_object, register)
                if register_index is None:
                    if previous_injection is None:
                        injected_value = flip_bit(
                            gold_value, num_bits_to_inject, bit_to_inject)
                    config.set(config_object, register, injected_value)
                else:
                    register_list_ = register_list = gold_value
                    if previous_injection is None:
                        for index in register_index:
                            gold_value = gold_value[index]
                        injected_value = flip_bit(
                            gold_value, num_bits_to_inject, bit_to_inject)
                    for index in range(len(register_index)-1):
                        register_list_ = register_list_[register_index[index]]
                    register_list_[register_index[-1]] = injected_value
                    config.set(config_object, register, register_list)
                config.save()
            injection['gold_value'] = gold_value
            injection['injected_value'] = injected_value
            return injection

    # def __inject_checkpoint(self, injection_number, checkpoint_number,
    #                         previous_injection=None):
        if injection_number == 1:
            gold_checkpoint = ('simics-workspace/gold-checkpoints/' +
                               str(self.db.campaign['id'])+'/' +
                               str(checkpoint_number))
        else:
            gold_checkpoint = ('simics-workspace/injected-checkpoints/' +
                               str(self.db.campaign['id'])+'/' +
                               str(self.db.result['id'])+'/' +
                               str(checkpoint_number))
        injected_checkpoint = ('simics-workspace/injected-checkpoints/' +
                               str(self.db.campaign['id'])+'/' +
                               str(self.db.result['id'])+'/' +
                               str(checkpoint_number)+'_injected')
        makedirs(injected_checkpoint)
        # copy gold checkpoint files
        checkpoint_files = listdir(gold_checkpoint)
        for checkpoint_file in checkpoint_files:
            copyfile(gold_checkpoint+'/'+checkpoint_file,
                     injected_checkpoint+'/'+checkpoint_file)
        if previous_injection is None:
            # choose injection target
            target = choose_target(self.options.selected_targets, self.targets)
            register = choose_register(target, self.targets)
            injection = {'result_id': self.db.result['id'],
                         'injection_number': injection_number,
                         'checkpoint_number': checkpoint_number,
                         'register': register,
                         'success': False,
                         'target': target,
                         'timestamp': None}
            with self.db as db:
                db.insert('injection', injection)
            try:
                # perform fault injection
                injection.update(inject_register(
                    injected_checkpoint, register, target))
            except:
                raise DrSEUsError('Error injecting fault')
            else:
                injection['success'] = True
                with self.db as db:
                    db.update('injection', injection)
                    db.log_event('Information', 'Simics', 'Fault injected',
                                 success=True)
            if self.options.debug:
                print(colored('result id: '+str(self.db.result['id']),
                              'magenta'))
                print(colored('injection number: '+str(injection_number),
                              'magenta'))
                print(colored('checkpoint number: '+str(checkpoint_number),
                              'magenta'))
                print(colored('target: '+injection['target'], 'magenta'))
                print(colored('register: '+injection['register'],
                              'magenta'))
                print(colored('gold value: '+injection['gold_value'],
                              'magenta'))
                print(colored('injected value: ' +
                              injection['injected_value'], 'magenta'))
        else:
            inject_register(injected_checkpoint, None, None)
        return injected_checkpoint.replace('simics-workspace/', '')

    def __compare_checkpoints(self, checkpoint_number, last_checkpoint):

        def compare_registers(checkpoint_number, gold_checkpoint,
                              monitored_checkpoint):
            """
            Compares the register values of the checkpoint_number for iteration
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
                        if target != 'TLB':
                            if 'count' in self.targets[target]:
                                count = self.targets[target]['count']
                            else:
                                count = 1
                            for target_index in range(count):
                                config_object = ('DUT_'+self.board +
                                                 self.targets[target]['OBJECT'])
                                if count > 1:
                                    config_object += '['+str(target_index)+']'
                                if target == 'GPR':
                                    target_key = config_object+':gprs'
                                else:
                                    target_key = config_object
                                registers[target_key] = {}
                                for register in (self.targets[target]
                                                             ['registers']):
                                    registers[target_key][register] = \
                                        config.get(config_object, register)
                return registers

            # watch out! we're gonna use recursion
            # keep your arms and legs inside the stack frame at all times
            def log_diffs(db, config_object, register, gold_value,
                          monitored_value):
                if isinstance(gold_value, list):
                    for index in range(len(gold_value)):
                        log_diffs(db, config_object, register+':'+str(index),
                                  gold_value[index], monitored_value[index])
                else:
                    if int(monitored_value, base=0) != int(gold_value, base=0):
                        register_diff = {
                            'result_id': self.db.result['id'],
                            'checkpoint_number': checkpoint_number,
                            'config_object': config_object,
                            'register': register,
                            'gold_value': gold_value,
                            'monitored_value': monitored_value}
                        db.insert('simics_register_diff', register_diff)

        # def compare_registers(checkpoint_number, gold_checkpoint,
        #                       monitored_checkpoint):
            gold_registers = get_registers(gold_checkpoint)
            monitored_registers = get_registers(monitored_checkpoint)
            with self.db as db:
                for config_object in gold_registers:
                    for register in gold_registers[config_object]:
                        log_diffs(db, config_object, register,
                                  gold_registers[config_object][register],
                                  monitored_registers[config_object][register])
                diffs = db.get_count('simics_register_diff')
            return diffs

        def compare_memory(checkpoint_number, gold_checkpoint,
                           monitored_checkpoint):
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
                    mkdir(incremental_checkpoint+'/memory-blocks')
                    for address in addresses:
                        gold_block = (incremental_checkpoint+'/memory-blocks/' +
                                      hex(address)+'_gold.raw')
                        monitored_block = (incremental_checkpoint +
                                           '/memory-blocks/'+hex(address) +
                                           '_monitored.raw')
                        check_call([getcwd()+'/simics-workspace/bin/craff',
                                    gold_ram, '--extract='+hex(address),
                                    '--extract-block-size='+str(block_size),
                                    '--output='+gold_block])
                        check_call([getcwd()+'/simics-workspace/bin/craff',
                                    monitored_ram, '--extract='+hex(address),
                                    '--extract-block-size='+str(block_size),
                                    '--output='+monitored_block])

        # def compare_memory(checkpoint_number, gold_checkpoint,
        #                    monitored_checkpoint):
            if self.board == 'p2020rdb':
                gold_rams = [gold_checkpoint+'/DUT_'+self.board +
                             '.soc.ram_image['+str(index)+'].craff'
                             for index in range(1)]
                monitored_rams = [monitored_checkpoint+'/DUT_'+self.board +
                                  '.soc.ram_image['+str(index)+'].craff'
                                  for index in range(1)]
            elif self.board == 'a9x2':
                gold_rams = [gold_checkpoint+'/DUT_'+self.board +
                             '.coretile.ddr_image['+str(index)+'].craff'
                             for index in range(2)]
                monitored_rams = [monitored_checkpoint+'/DUT_'+self.board +
                                  '.coretile.ddr_image['+str(index)+'].craff'
                                  for index in range(2)]
            ram_diffs = [ram+'.diff' for ram in monitored_rams]
            diff_content_maps = [diff+'.content_map' for diff in ram_diffs]
            diffs = 0
            memory_diff = {'result_id': self.db.result['id'],
                           'checkpoint_number': checkpoint_number}
            with self.db as db:
                for (memory_diff['image_index'], gold_ram, monitored_ram,
                     ram_diff, diff_content_map) in zip(
                        range(len(monitored_rams)), gold_rams, monitored_rams,
                        ram_diffs, diff_content_maps):
                    check_call([getcwd()+'/simics-workspace/bin/craff',
                                '--diff', gold_ram, monitored_ram,
                                '--output='+ram_diff],
                               cwd=getcwd()+'/simics-workspace',
                               stdout=DEVNULL)
                    check_call([getcwd()+'/simics-workspace/bin/craff',
                                '--content-map', ram_diff,
                                '--output='+diff_content_map],
                               cwd=getcwd()+'/simics-workspace',
                               stdout=DEVNULL)
                    craff_output = check_output(
                        [getcwd()+'/simics-workspace/bin/craff', '--info',
                         ram_diff], cwd=getcwd()+'/simics-workspace',
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

    # def __compare_checkpoints(self, checkpoint_number, last_checkpoint):
        reg_errors = 0
        mem_errors = 0
        for checkpoint_number in range(checkpoint_number+1, last_checkpoint+1):
            self.__command('run-cycles ' +
                           str(self.db.campaign['cycles_between']))
            incremental_checkpoint = (
                'injected-checkpoints/'+str(self.db.campaign['id'])+'/' +
                str(self.db.result['id'])+'/'+str(checkpoint_number))
            monitor = self.options.compare_all or \
                checkpoint_number == self.db.campaign['num_checkpoints']
            if monitor or checkpoint_number == last_checkpoint:
                self.__command('write-configuration '+incremental_checkpoint)
            if monitor:
                monitored_checkpoint = \
                    self.__merge_checkpoint(incremental_checkpoint)
                gold_incremental_checkpoint = ('gold-checkpoints/' +
                                               str(self.db.campaign['id']) +
                                               '/'+str(checkpoint_number))
                gold_checkpoint = gold_incremental_checkpoint+'_merged'
                if not exists('simics-workspace/'+gold_checkpoint):
                    self.__merge_checkpoint(gold_incremental_checkpoint)
                errors = compare_registers(
                    checkpoint_number, gold_checkpoint, monitored_checkpoint)
                if errors > reg_errors:
                    reg_errors = errors
                errors = compare_memory(
                    checkpoint_number, gold_checkpoint, monitored_checkpoint)
                if errors > reg_errors:
                    mem_errors = errors
        return reg_errors + mem_errors
