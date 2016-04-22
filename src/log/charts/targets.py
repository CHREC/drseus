from django.db.models import Case, Count, F, TextField, Value, When
from django.db.models.functions import Concat
from json import dumps
from time import time

from . import create_chart


def outcomes(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    indices = kwargs['indices'] if 'indices' in kwargs else False
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    if indices:
        chart_id = 'target_indices_chart'
        injections = injections.annotate(target_name=Case(
            When(target_index__isnull=True, then=F('target')),
            default=Concat('target', Value('['),  'target_index', Value(']'),
                           output_field=TextField())))
        targets = list(injections.values_list(
            'target_name', flat=True).distinct().order_by('target_name'))
    else:
        chart_id = 'targets_chart'
        targets = list(injections.values_list(
            'target', flat=True).distinct().order_by('target'))
    if len(targets) < 1:
        return
    create_chart(chart_list, chart_data,
                 'Targets (With Indices)' if indices else 'Targets', order,
                 chart_id, injections, 'Injected Target', 'Target',
                 'target_name' if indices else 'target', targets, outcomes,
                 group_categories, success, percent=True, log=True)


def indices(**kwargs):
    kwargs['indices'] = True
    outcomes(**kwargs)


def propagation(**kwargs):
    return
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    injections = kwargs['injections']
    order = kwargs['order']

    start = time()
    chart_id = 'propagation_chart'
    injections = injections.exclude(checkpoint__isnull=True)
    targets = list(injections.values_list('target', flat=True).distinct(
        ).order_by('target'))
    if len(targets) < 1:
        return
    chart = {
        'chart': {
            'renderTo': chart_id,
            'type': 'column',
            'zoomType': 'xy'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': chart_id,
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': '__series_click__'
                    }
                }
            }
        },
        'series': [],
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': targets,
            'title': {
                'text': 'Injected Target'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Average Items Affected'
            },
            'type': 'logarithmic'
        }
    }
    reg_diff_list = []
    mem_diff_list = []
    for target in targets:
        count = injections.filter(target=target).count()
        if count:
            reg_diff_count = injections.filter(target=target).aggregate(
                reg_count=Count('result__simics_register_diff'))['reg_count']
            if reg_diff_count:
                reg_diff_list.append(reg_diff_count/count)
            else:
                reg_diff_list.append(None)
            mem_diff_count = injections.filter(target=target).aggregate(
                mem_count=Count('result__simics_memory_diff'))['mem_count']
            if mem_diff_count:
                mem_diff_list.append(mem_diff_count/count)
            else:
                mem_diff_list.append(None)
        else:
            reg_diff_list.append(None)
            mem_diff_list.append(None)
    chart['series'].append({'data': mem_diff_list, 'name': 'Memory Blocks'})
    chart['series'].append({'data': reg_diff_list, 'name': 'Registers'})
    chart = dumps(chart, indent=4).replace('\"__series_click__\"', """
    function(event) {
        var filter;
        if (window.location.href.indexOf('?') > -1) {
            filter = window.location.href.replace(/.*\?/g, '&');
        } else {
            filter = '';
        }
        window.open('results?injection__target='+this.category+filter);
    }
    """)
    chart_data.append(chart)
    chart_list.append({'id': chart_id, 'order': order,
                       'title': 'Fault Propagation'})
    print(chart_id, round(time()-start, 2), 'seconds')


def data_diff(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    indices = kwargs['indices'] if 'indices' in kwargs else False
    injections = kwargs['injections']
    order = kwargs['order']

    chart_id = 'diff_targets_chart'
    targets = list(injections.values_list('target', flat=True).distinct(
        ).order_by('target'))
    if len(targets) < 1:
        return
    create_chart(chart_list, chart_data,
                 'Data Destruction By Target (With Indices)' if indices
                 else 'Data Destruction By Target', order, chart_id, injections,
                 'Injected Target', 'Target',
                 'target_name' if indices else 'target', targets,
                 ['Data Match'], average='result__data_diff')


def execution_time(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    indices = kwargs['indices'] if 'indices' in kwargs else False
    injections = kwargs['injections']
    order = kwargs['order']

    chart_id = 'execution_time_targets_chart'
    injections = injections.exclude(result__execution_time__isnull=True).filter(
        result__returned=True)
    targets = list(injections.values_list('target', flat=True).distinct(
        ).order_by('target'))
    if len(targets) < 1:
        return
    create_chart(chart_list, chart_data,
                 'Average Execution Time By Target (With Indices)' if indices
                 else 'Average Execution Time By Target', order, chart_id,
                 injections, 'Injected Target', 'Target',
                 'target_name' if indices else 'target', targets,
                 ['Execution Time'], average='result__execution_time')
