import django_tables2 as tables
from .models import (campaign, result, injection, simics_register_diff,
                     simics_memory_diff)


class campaign_table(tables.Table):
    id = tables.TemplateColumn(
        '<a href="/{{record.id}}/results">{{record.id}}</a>')
    results = tables.Column()
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = campaign
        exclude = ('aux_output', 'aux_paramiko_output', 'debugger_output',
                   'dut_output', 'paramiko_output')


class result_table(tables.Table):
    injections = tables.Column()
    iteration = tables.TemplateColumn(
        '<a href="../result/{{record.iteration}}">{{record.iteration}}</a>')
    timestamp = tables.DateTimeColumn(format='m/d/Y H:i:s.u')

    class Meta:
        attrs = {"class": "paleblue"}
        model = result
        exclude = ('aux_output', 'aux_paramiko_output', 'campaign',
                   'debugger_output', 'dut_output',  'paramiko_output')


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
        exclude = ('core', 'id', 'result', 'time', 'time_rounded')


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
