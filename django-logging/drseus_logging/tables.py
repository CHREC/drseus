import django_tables2 as tables
from .models import simics_result, simics_register_diff, simics_memory_diff


class simics_result_table(tables.Table):
    injection_number = tables.Column(accessor='injection.injection_number')
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
        exclude = ('injection', 'debugger_output', 'dut_output', 'qty')


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
