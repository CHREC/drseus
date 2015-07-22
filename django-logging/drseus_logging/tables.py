import django_tables2 as tables
from .models import (campaign, result, injection, simics_register_diff,
                     simics_memory_diff)


class campaign_table(tables.Table):
    results = tables.Column()
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')
    last_injection = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = campaign
        exclude = ('application', 'aux_output', 'aux_paramiko_output',
                   'cycles_between', 'debugger_output', 'dut_output',
                   'num_cycles', 'paramiko_output', 'use_aux', 'use_aux_output')


class campaigns_table(tables.Table):
    campaign_number = tables.TemplateColumn(
        '{% if record.results > 0 %}'
        '<a href="/{{ value}}/charts">'
        '{% else %}'
        '<a href="/{{ value }}/campaign">'
        '{% endif %}'
        '{{ value }}'
        '</a>')
    results = tables.Column()
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')
    last_injection = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = campaign
        exclude = ('application', 'aux_application', 'aux_output',
                   'aux_paramiko_output', 'cycles_between', 'debugger_output',
                   'dut_output', 'output_file', 'num_cycles', 'num_checkpoints',
                   'paramiko_output', 'use_aux', 'use_aux_output')


class result_table(tables.Table):
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = result
        exclude = ('aux_output', 'aux_paramiko_output', 'campaign',
                   'debugger_output', 'dut_output', 'id', 'iteration',
                   'paramiko_output')


class results_table(tables.Table):
    injections = tables.Column()
    iteration = tables.TemplateColumn(
        '<a href="../result/{{ value }}">{{ value }}</a>')
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = result
        exclude = ('aux_output', 'aux_paramiko_output', 'campaign',
                   'debugger_output', 'dut_output', 'id', 'paramiko_output')


class hw_injection_table(tables.Table):
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = injection
        exclude = ('config_object', 'config_type', 'checkpoint_number', 'field',
                   'id', 'register_index', 'result', 'target', 'target_index')


class simics_injection_table(tables.Table):
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = injection
        exclude = ('config_object', 'config_type', 'core', 'id', 'result',
                   'time', 'time_rounded')


class simics_register_diff_table(tables.Table):
    class Meta:
        attrs = {"class": "paleblue"}
        exclude = ('id', 'result')
        model = simics_register_diff


class simics_memory_diff_table(tables.Table):
    class Meta:
        attrs = {"class": "paleblue"}
        exclude = ('id', 'result')
        model = simics_memory_diff
