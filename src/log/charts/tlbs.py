from django.db.models import TextField, Value
from django.db.models.functions import Concat, Length, Substr
from time import time

from .. import fix_sort
from . import get_chart


def outcomes(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']

    start = time()
    chart_id = 'tlbs_chart'
    injections = injections.filter(target='TLB').annotate(
        temp=Concat('register', Value(':'), 'register_index',
                    output_field=TextField())).annotate(
        tlb_entry=Concat(Substr('temp', 1, Length('temp')-3), Value('}'),
                         output_field=TextField()))
    tlb_entries = sorted(injections.values_list(
        'tlb_entry', flat=True).distinct().order_by('tlb_entry'), key=fix_sort)
    if len(tlb_entries) < 1:
        return
    chart = get_chart(chart_id, injections, 'Injected TLB Entry', 'TLB Entry',
                      'tlb_entry', tlb_entries, outcomes, group_categories,
                      rotate_labels=True)
    chart_data.extend(chart)
    chart_list.append({'id': chart_id, 'order': order, 'title': 'TLB Entries'})
    print(chart_id, round(time()-start, 2), 'seconds')


def fields(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']

    start = time()
    chart_id = 'tlb_fields_chart'
    injections = injections.filter(target='TLB')
    fields = list(injections.values_list(
        'field', flat=True).distinct().order_by('field'))
    if len(fields) < 1:
        return
    chart = get_chart(chart_id, injections, 'Injected TLB Field', 'TLB Field',
                      'field', fields, outcomes, group_categories)
    chart_data.extend(chart)
    chart_list.append({'id': chart_id, 'order': order, 'title': 'TLB Fields'})
    print(chart_id, round(time()-start, 2), 'seconds')
