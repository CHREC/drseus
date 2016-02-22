from django_tables2 import (BooleanColumn, CheckBoxColumn, Column,
                            DateTimeColumn, Table, TemplateColumn)
from .models import (campaign, event, injection, result, simics_memory_diff,
                     simics_register_diff)

datetime_format = 'M j, Y h:i:s A'


class campaigns_table(Table):
    id_ = TemplateColumn(
        '<a href="/campaign/{{ value }}/results">{{ value }}</a>',
        accessor='id')
    results = Column(empty_values=(), orderable=False)
    timestamp = DateTimeColumn(format=datetime_format)

    def render_num_cycles(self, record):
        return '{:,}'.format(record.num_cycles)

    def render_results(self, record):
        return '{:,}'.format(
            result.objects.filter(campaign=record.id).count())

    class Meta:
        attrs = {'class': 'table table-bordered table-striped'}
        fields = ('id_', 'results', 'command', 'architecture', 'simics',
                  'exec_time', 'sim_time', 'num_cycles', 'timestamp')
        model = campaign
        order_by = 'id_'
        template = 'django_tables2/bootstrap.html'


class campaign_table(campaigns_table):
    results = Column(empty_values=(), orderable=False)
    timestamp = DateTimeColumn(format=datetime_format)

    def render_num_checkpoints(self, record):
        return '{:,}'.format(record.num_checkpoints)

    def render_cycles_between(self, record):
        return '{:,}'.format(record.cycles_between)

    class Meta:
        attrs = {'class': 'table table-bordered table-striped'}
        exclude = ('id_',)
        fields = ('id', 'timestamp', 'results', 'command', 'aux_command',
                  'description', 'architecture', 'simics', 'aux', 'exec_time',
                  'sim_time', 'num_cycles', 'output_file', 'num_checkpoints',
                  'cycles_between')
        model = campaign
        orderable = False
        template = 'django_tables2/bootstrap.html'


class results_table(Table):
    events = Column(empty_values=(), orderable=False)
    id_ = TemplateColumn(  # LinkColumn()
        '<a href="./result/{{ value }}">{{ value }}</a>', accessor='id')
    registers = Column(empty_values=(), orderable=False)
    select_box = CheckBoxColumn(
        accessor='id',
        attrs={'th__input': {'onclick': 'update_selection(this)'}})
    injection_success = Column(empty_values=(), orderable=False)
    timestamp = DateTimeColumn(format=datetime_format)
    targets = Column(empty_values=(), orderable=False)

    def render_data_diff(self, record):
        return '{0:.2f}%'.format(result.objects.get(id=record.id).data_diff*100)

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
                    success = '\u2714'
                    break
                else:
                    success = '\u2718'
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
        attrs = {'class': 'table table-bordered table-striped'}
        fields = ('select_box', 'id_', 'dut_serial_port', 'timestamp',
                  'outcome_category', 'outcome', 'data_diff', 'events',
                  'targets', 'registers', 'injection_success')
        model = result
        order_by = '-id_'
        template = 'django_tables2/bootstrap.html'


class result_table(Table):
    delete = TemplateColumn(
        '<input type="button" value="Delete" onclick="delete_click()">',
        orderable=False)
    edit = TemplateColumn(
        '<input type="button" value="Save" onclick="save_click()">',
        orderable=False)
    outcome = TemplateColumn(
        '<input id="edit_outcome" type="text" value="{{ value }}" />')
    outcome_category = TemplateColumn(
        '<input id="edit_outcome_category" type="text" value="{{ value }}" />')
    timestamp = DateTimeColumn(format=datetime_format)

    def render_data_diff(self, record):
        return '{0:.2f}%'.format(result.objects.get(id=record.id).data_diff*100)

    class Meta:
        attrs = {'class': 'table table-bordered table-striped'}
        fields = ('dut_serial_port', 'timestamp', 'outcome_category', 'outcome',
                  'num_injections', 'data_diff', 'detected_errors', 'edit',
                  'delete')
        model = result
        orderable = False
        template = 'django_tables2/bootstrap.html'


class event_table(Table):
    description = TemplateColumn(
        '{% if value %}<code class="console">{{ value }}</code>{% endif %}')
    success_ = TemplateColumn(
        '{% if value == None %}-'
        '{% elif value %}<span class="true">\u2714</span>'
        '{% else %}<span class="false">\u2718</span>{% endif %}',
        accessor='success')
    timestamp = DateTimeColumn(format=datetime_format)

    class Meta:
        attrs = {'class': 'table table-bordered table-striped'}
        fields = ('timestamp', 'level', 'source', 'event_type', 'success_',
                  'description')
        model = event
        template = 'django_tables2/bootstrap.html'


class injections_table(Table):
    success_ = Column(accessor='success')

    class Meta:
        attrs = {'class': 'table table-bordered table-striped'}
        fields = ('target', 'target_index', 'register', 'bit',
                  'register_access', 'processor_mode', 'gold_value',
                  'injected_value', 'success_')
        model = injection
        order_by = ('target', 'target_index', 'register', 'bit', 'success')
        template = 'django_tables2/bootstrap.html'


class hw_injection_table(Table):
    success_ = BooleanColumn(accessor='success')
    timestamp = DateTimeColumn(format=datetime_format)

    class Meta:
        attrs = {'class': 'table table-bordered table-striped'}
        fields = ('timestamp', 'target', 'target_index', 'register',
                  'register_index', 'bit', 'field', 'gold_value',
                  'injected_value', 'success_')
        model = injection
        template = 'django_tables2/bootstrap.html'


class simics_injection_table(Table):
    success_ = BooleanColumn(accessor='success')
    timestamp = DateTimeColumn(format=datetime_format)

    class Meta:
        attrs = {'class': 'table table-bordered table-striped'}
        fields = ('timestamp', 'checkpoint_number', 'target', 'target_index',
                  'register', 'register_index', 'bit', 'field', 'gold_value',
                  'injected_value', 'success_')
        model = injection
        template = 'django_tables2/bootstrap.html'


class simics_register_diff_table(Table):
    class Meta:
        attrs = {'class': 'table table-bordered table-striped'}
        exclude = ('id', 'result')
        model = simics_register_diff
        template = 'django_tables2/bootstrap.html'


class simics_memory_diff_table(Table):
    class Meta:
        attrs = {'class': 'table table-bordered table-striped'}
        exclude = ('id', 'result')
        model = simics_memory_diff
        template = 'django_tables2/bootstrap.html'
