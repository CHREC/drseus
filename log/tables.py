from django_tables2 import Column, DateTimeColumn, Table, TemplateColumn

from .models import (campaign, event, injection, result, simics_memory_diff,
                     simics_register_diff)

datetime_format = 'M j, Y h:i:s A'


class campaigns_table(Table):
    id_ = TemplateColumn(
        '<a href="/campaign/{{ value }}/results">{{ value }}</a>',
        accessor='id')
    num_cycles = Column()
    results = Column(empty_values=(), orderable=False)
    timestamp = DateTimeColumn(format=datetime_format)

    def render_num_cycles(self, record):
        return '{:,}'.format(record.num_cycles)

    def render_results(self, record):
        return '{:,}'.format(
            result.objects.filter(campaign=record.id).count())

    class Meta:
        attrs = {"class": "paleblue"}
        model = campaign
        fields = ('id_', 'results', 'command', 'aux_command', 'description',
                  'architecture', 'simics', 'exec_time', 'sim_time',
                  'num_cycles', 'timestamp')
        order_by = 'id_'


class campaign_table(campaigns_table):
    cycles_between = Column()
    num_checkpoints = Column()
    results = Column(empty_values=(), orderable=False)
    timestamp = DateTimeColumn(format=datetime_format)

    def render_num_checkpoints(self, record):
        return '{:,}'.format(record.num_checkpoints)

    def render_cycles_between(self, record):
        return '{:,}'.format(record.cycles_between)

    class Meta:
        attrs = {"class": "paleblue"}
        model = campaign
        exclude = ('id_',)
        fields = ('id', 'timestamp', 'results', 'command', 'aux_command',
                  'description', 'architecture', 'simics', 'aux', 'exec_time',
                  'sim_time', 'num_cycles', 'output_file', 'num_checkpoints',
                  'cycles_between')


class results_table(Table):
    events = Column(empty_values=(), orderable=False)
    id_ = TemplateColumn(  # LinkColumn()
        '<a href="./result/{{ value }}">{{ value }}</a>', accessor='id')
    registers = Column(empty_values=(), orderable=False)
    select = TemplateColumn(
        '<input type="checkbox" name="select_box" value="{{ record.id }}">',
        verbose_name='', orderable=False)
    injection_success = Column(empty_values=(), orderable=False)
    timestamp = DateTimeColumn(format=datetime_format)
    targets = Column(empty_values=(), orderable=False)

    def render_events(self, record):
        return '{:,}'.format(
            event.objects.filter(result_id=record.id).count())

    def render_registers(self, record):
        if record is not None:
            registers = [injection_.register for injection_
                         in injection.objects.filter(result=record.id)]
        else:
            registers = []
        for index in range(len(registers)):
            if registers[index] is None:
                registers[index] = '-'
        if len(registers) > 0:
            return ', '.join(registers)
        else:
            return '-'

    def render_injection_success(self, record):
        success = '-'
        if record is not None:
            for injection_ in injection.objects.filter(result=record.id):
                if injection_.success is None:
                    success = '-'
                elif not injection_.success:
                    success = False
                    break
                else:
                    success = True
        return success

    def render_targets(self, record):
        if record is not None:
            targets = [injection_.target for injection_
                       in injection.objects.filter(result=record.id)]
        else:
            targets = []
        for index in range(len(targets)):
            if targets[index] is None:
                targets[index] = '-'
        if len(targets) > 0:
            return ', '.join(targets)
        else:
            return '-'

    class Meta:
        attrs = {"class": "paleblue"}
        model = result
        fields = ('select', 'id_', 'dut_serial_port', 'timestamp',
                  'outcome_category', 'outcome', 'data_diff', 'detected_errors',
                  'events', 'num_injections', 'targets', 'registers',
                  'injection_success')
        order_by = '-id_'


class result_table(results_table):
    delete = TemplateColumn(
        '<input type="submit" name="delete" value="Delete" onclick="return '
        'confirm("Are you sure you want to delete this result?")" />')
    edit = TemplateColumn(
        '<input type="submit" name="save" value="Save" onclick="return confirm('
        '"Are you sure you want to edit this result?")"/>')
    outcome = TemplateColumn(
        '<input name="outcome" type="text" value="{{ value }}" />')
    outcome_category = TemplateColumn(
        '<input name="outcome_category" type="text" value="{{ value }}" />')
    timestamp = DateTimeColumn(format=datetime_format)

    class Meta:
        attrs = {"class": "paleblue"}
        model = result
        exclude = ('id_', 'select', 'targets')
        fields = ('id', 'dut_serial_port', 'timestamp', 'outcome_category',
                  'outcome', 'num_injections', 'data_diff', 'detected_errors')


class event_table(Table):
    description = TemplateColumn(
        '{% if value %}<code class="console">{{ value }}</code>{% endif %}')
    timestamp = DateTimeColumn(format=datetime_format)

    class Meta:
        attrs = {"class": "paleblue"}
        model = event
        fields = ('timestamp', 'level', 'source', 'event_type', 'description',
                  'success')


class injections_table(Table):
    class Meta:
        attrs = {"class": "paleblue"}
        model = injection
        order_by = ('target', 'target_index', 'register', 'bit', 'success')
        fields = ('target', 'target_index', 'register', 'bit',
                  'register_access', 'processor_mode', 'gold_value',
                  'injected_value', 'success')


class hw_injection_table(Table):
    timestamp = DateTimeColumn(format=datetime_format)

    class Meta:
        attrs = {"class": "paleblue"}
        model = injection
        exclude = ('config_object', 'config_type', 'checkpoint_number', 'field',
                   'id', 'register_index', 'result')


class simics_injection_table(Table):
    timestamp = DateTimeColumn(format=datetime_format)

    class Meta:
        attrs = {"class": "paleblue"}
        model = injection
        fields = ('injection_number', 'timestamp', 'checkpoint_number',
                  'target', 'target_index', 'register', 'register_index', 'bit',
                  'field', 'gold_value', 'injected_value', 'success')


class simics_register_diff_table(Table):
    class Meta:
        attrs = {"class": "paleblue"}
        model = simics_register_diff
        exclude = ('id', 'result')


class simics_memory_diff_table(Table):
    class Meta:
        attrs = {"class": "paleblue"}
        model = simics_memory_diff
        exclude = ('id', 'result')
