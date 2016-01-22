import django_tables2 as tables

from .models import (campaign, event, injection, result, simics_memory_diff,
                     simics_register_diff)


class campaigns_table(tables.Table):
    id_ = tables.TemplateColumn(
        '<a href="/campaign/{{ value }}/results">{{ value }}</a>',
        accessor='id')
    num_cycles = tables.Column()
    results = tables.Column(empty_values=(), orderable=False)

    def render_num_cycles(self, record):
        return '{:,}'.format(record.num_cycles)

    def render_results(self, record):
        return '{:,}'.format(
            result.objects.filter(campaign=record.id).count())

    class Meta:
        attrs = {"class": "paleblue"}
        model = campaign
        fields = ('id_', 'results', 'command', 'aux_command', 'architecture',
                  'use_simics', 'exec_time', 'sim_time', 'num_cycles',
                  'timestamp')
        order_by = 'id_'


class campaign_table(campaigns_table):
    num_checkpoints = tables.Column()
    cycles_between = tables.Column()
    results = tables.Column(empty_values=(), orderable=False)

    def render_num_checkpoints(self, record):
        return '{:,}'.format(record.num_checkpoints)

    def render_cycles_between(self, record):
        return '{:,}'.format(record.cycles_between)

    class Meta:
        attrs = {"class": "paleblue"}
        model = campaign
        exclude = ('id_',)
        fields = ('id', 'timestamp', 'results', 'command', 'aux_command',
                  'architecture', 'use_simics', 'use_aux', 'exec_time',
                  'sim_time', 'num_cycles', 'output_file', 'num_checkpoints',
                  'cycles_between')


class results_table(tables.Table):
    events = tables.Column(empty_values=(), orderable=False)
    id_ = tables.TemplateColumn(  # LinkColumn()
        '<a href="./result/{{ value }}">{{ value }}</a>', accessor='id')
    registers = tables.Column(empty_values=(), orderable=False)
    select = tables.TemplateColumn(
        '<input type="checkbox" name="select_box" value="{{ record.id }}">',
        verbose_name='', orderable=False)
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')
    targets = tables.Column(empty_values=(), orderable=False)

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
        fields = ('select', 'id_', 'timestamp', 'outcome_category', 'outcome',
                  'data_diff', 'detected_errors', 'num_injections', 'targets',
                  'registers')
        order_by = 'id_'


class result_table(results_table):
    outcome = tables.TemplateColumn(
        '<input name="outcome" type="text" value="{{ value }}" />')
    outcome_category = tables.TemplateColumn(
        '<input name="outcome_category" type="text" value="{{ value }}" />')
    edit = tables.TemplateColumn(
        '<input type="submit" name="save" value="Save" onclick="return confirm('
        '"Are you sure you want to edit this result?")"/>')
    delete = tables.TemplateColumn(
        '<input type="submit" name="delete" value="Delete" onclick="return '
        'confirm("Are you sure you want to delete this result?")" />')

    class Meta:
        attrs = {"class": "paleblue"}
        model = result
        exclude = ('id_', 'select', 'targets')
        fields = ('id', 'timestamp', 'outcome_category', 'outcome',
                  'num_injections', 'data_diff', 'detected_errors')


class event_table(tables.Table):
    description = tables.TemplateColumn(
        '<code class="console">{{ value }}</code>')
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = event
        fields = ('timestamp', 'source', 'event_type', 'description')


class hw_injection_table(tables.Table):
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = injection
        exclude = ('config_object', 'config_type', 'checkpoint_number', 'field',
                   'id', 'register_index', 'result')


class simics_injection_table(tables.Table):
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = injection
        fields = ('injection_number', 'timestamp', 'checkpoint_number',
                  'target', 'target_index', 'register', 'register_index', 'bit',
                  'field', 'gold_value', 'injected_value', 'success')


class simics_register_diff_table(tables.Table):
    class Meta:
        attrs = {"class": "paleblue"}
        model = simics_register_diff
        exclude = ('id', 'result')


class simics_memory_diff_table(tables.Table):
    class Meta:
        attrs = {"class": "paleblue"}
        model = simics_memory_diff
        exclude = ('id', 'result')
