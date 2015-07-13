import django_tables2 as tables
from .models import (result, hw_injection, simics_injection,
                     simics_register_diff, simics_memory_diff)


class result_table(tables.Table):
    iteration = tables.TemplateColumn(
        '<a href="/result/{{record.iteration}}">{{record.iteration}}</a>')

    class Meta:
        model = result
        attrs = {"class": "paleblue"}
        exclude = ('debugger_output', 'dut_output', 'aux_output',
                   'paramiko_output', 'aux_paramiko_output')


class hw_injection_table(tables.Table):
    class Meta:
        model = hw_injection
        attrs = {"class": "paleblue"}


class simics_injection_table(tables.Table):
    class Meta:
        model = simics_injection
        attrs = {"class": "paleblue"}


class simics_register_diff_table(tables.Table):
    class Meta:
        attrs = {"class": "paleblue"}
        exclude = ('id')
        model = simics_register_diff


class simics_memory_diff_table(tables.Table):
    class Meta:
        attrs = {"class": "paleblue"}
        exclude = ('id')
        model = simics_memory_diff
