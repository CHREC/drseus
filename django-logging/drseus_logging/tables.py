import django_tables2 as tables
from .models import (hw_result, simics_result, simics_register_diff,
                     simics_memory_diff, supervisor_result)


class hw_result_table(tables.Table):
    injection_number = tables.Column(accessor='injection.injection_number')
    time = tables.Column(accessor='injection.time')
    core = tables.Column(accessor='injection.core')
    register = tables.Column(accessor='injection.register')
    bit = tables.Column(accessor='injection.bit')
    outcome = tables.TemplateColumn(
        '<a href="/injection/{{record.injection.injection_number}}">'
        '{{record.outcome}}</a>')

    class Meta:
        model = hw_result
        attrs = {"class": "paleblue"}
        exclude = ('injection', 'debugger_output', 'dut_output', 'aux_output',
                   'qty')


class simics_result_table(tables.Table):
    injection_number = tables.Column(accessor='injection.injection_number')
    checkpoint_number = tables.Column(accessor='injection.checkpoint_number')
    target = tables.Column(accessor='injection.target')
    target_index = tables.Column(accessor='injection.target_index')
    register = tables.Column(accessor='injection.register')
    register_index = tables.Column(accessor='injection.register_index')
    bit = tables.Column(accessor='injection.bit')
    register_errors = tables.Column()
    memory_errors = tables.Column()
    outcome = tables.TemplateColumn(
        '<a href="/injection/{{record.injection.injection_number}}">'
        '{{record.outcome}}</a>')

    class Meta:
        model = simics_result
        attrs = {"class": "paleblue"}
        exclude = ('injection', 'debugger_output', 'dut_output', 'aux_output',
                   'qty')


class simics_register_diff_table(tables.Table):
    class Meta:
        attrs = {"class": "paleblue"}
        exclude = ('id', 'injection')
        model = simics_register_diff


class simics_memory_diff_table(tables.Table):
    class Meta:
        attrs = {"class": "paleblue"}
        exclude = ('id', 'injection')
        model = simics_memory_diff


class supervisor_result_table(tables.Table):
    iteration = tables.TemplateColumn(
        '<a href="/iteration/{{record.iteration}}">'
        '{{record.iteration}}</a>')

    class Meta:
        model = supervisor_result
        attrs = {"class": "paleblue"}
        exclude = ('dut_output', 'aux_output', 'qty')
