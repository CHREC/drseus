import django_tables2 as tables
from .models import simics_results


class results_table(tables.Table):
    register = tables.Column()
    register_index = tables.Column()
    bit = tables.Column()
    outcome = tables.TemplateColumn(
        '<a href="/injection/{{record.id}}">{{record.outcome}}</a>')

    class Meta:
        model = simics_results
        attrs = {"class": "paleblue"}
        fields = ('register', 'register_index', 'bit', 'outcome')
        order_by = ('register', 'register_index', 'bit', 'outcome')
