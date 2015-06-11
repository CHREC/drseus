import django_tables2 as tables
from .models import simics_result


class simics_result_table(tables.Table):
    register = tables.Column(accessor='injection.register')
    register_index = tables.Column(accessor='injection.register_index')
    bit = tables.Column(accessor='injection.bit')
    outcome = tables.TemplateColumn(
        '<a href="/injection/{{record.injection.injection_number}}">'
        '{{record.outcome}}</a>')

    class Meta:
        model = simics_result
        attrs = {"class": "paleblue"}
        fields = ('register', 'register_index', 'bit', 'outcome')
        order_by = ('register', 'register_index', 'bit', 'outcome')


class simics_register_diff_table(tables.Table):
    monitored_checkpoint_number = tables.Column()
    config_object = tables.Column()
    register = tables.Column()
    gold_value = tables.Column()
    monitored_value = tables.Column()

    class Meta:
        model = simics_result
        attrs = {"class": "paleblue"}
        fields = ('monitored_checkpoint_number', 'config_object', 'register',
                  'gold_value', 'monitored_value')
        order_by = ('monitored_checkpoint_number', 'config_object', 'register',
                    'gold_value', 'monitored_value')
