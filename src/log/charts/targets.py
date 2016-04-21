from collections import OrderedDict
from copy import deepcopy
from django.db.models import Avg, Case, Count, F, TextField, Value, When
from django.db.models.functions import Concat
from json import dumps
from time import time

from . import colors, default_chart


def outcomes(**kwargs):
    campaigns = kwargs['campaigns']
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    indices = kwargs['indices'] if 'indices' in kwargs else False
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    start = time()
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
    chart = default_chart(chart_id, 'Injected Target', targets)
    if success:
        outcome = 'success'
    elif group_categories:
        outcome = 'result__outcome_category'
    else:
        outcome = 'result__outcome'
    series = {campaign: OrderedDict([
        (str(outcome), [0]*len(targets)) for outcome in outcomes])
        for campaign in campaigns}
    for campaign, outcome, target, count in injections.values_list(
            'result__campaign_id', outcome,
            'target_name' if indices else 'target').distinct().annotate(
                count=Count('result')
            ).values_list(
                'result__campaign_id', outcome,
                'target_name' if indices else 'target', 'count'):
        series[campaign][outcome][targets.index(target)] = count
    for campaign in series:
        for outcome, data in series[campaign].items():
            series_data = {'data': data, 'name': outcome, 'stack': campaign}
            if campaign == campaigns[0]:
                series_data['id'] = outcome
            else:
                series_data['linkedTo'] = outcome
            if outcome in colors:
                series_data['color'] = colors[outcome]
            chart['series'].append(series_data)
    charts = [dumps(chart, indent=4)]
    chart_percent = deepcopy(chart)
    chart_percent['chart']['renderTo'] = '{}_percent'.format(chart_id)
    chart_percent['plotOptions']['series']['stacking'] = 'percent'
    chart_percent['yAxis']['labels'] = {'format': '{value}%'}
    charts.append(dumps(chart_percent, indent=4))
    if len(outcomes) == 1 and not success:
        chart_log = deepcopy(chart)
        chart_log['chart']['renderTo'] = '{}_log'.format(chart_id)
        chart_log['yAxis']['type'] = 'logarithmic'
        charts.append(dumps(chart_log, indent=4))
    for chart in charts:
        chart = chart.replace('\"__series_click__\"', """
        function(event) {
            var filter;
            if (window.location.href.indexOf('?') > -1) {
                filter = window.location.href.replace(/.*\?/g, '&');
            } else {
                filter = '';
            }
            var outcome;
            if (this.series.name == 'True') {
                outcome = '1';
            } else if (this.series.name == 'False') {
                outcome = '0';
            } else {
                outcome = this.series.name;
            }
            window.open('/campaign/'+this.series.options.stack+
                        '/results?outcome='+outcome+
                        '&injection__target='+this.category+filter);
        }
        """)
        chart = chart.replace('\"__tooltip_formatter__\"', """
            function () {
                return this.series.name+': <b>'+this.y+'</b><br/>'+
                       'Target: '+this.x+'<br/>'+
                       'Campaign: '+this.series.options.stack;
            }
        """)
        chart = chart.replace('\n    ', '\n                        ')
        if success:
            chart = chart.replace('?outcome=', '?injection__success=')
        elif group_categories:
            chart = chart.replace('?outcome=', '?outcome_category=')
        chart_data.append(chart)
    chart_list.append({
        'id': chart_id,
        'log': len(outcomes) == 1 and not success,
        'order': order,
        'percent': True,
        'title': 'Targets{}'.format(' (With Indices)' if indices else '')})
    print(chart_id, round(time()-start, 2), 'seconds')


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
    injections = injections.exclude(checkpoint__isnull=True)
    targets = list(injections.values_list('target', flat=True).distinct(
        ).order_by('target'))
    if len(targets) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'propagation_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': ('#77bfc7', '#a74ac7'),
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'propagation_chart',
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
    """.replace('\n    ', '\n                        '))
    chart_data.append(chart)
    chart_list.append({
        'id': 'propagation_chart',
        'order': order,
        'title': 'Fault Propagation'})
    print('propagation_chart:', round(time()-start, 2), 'seconds')


def data_diff(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    injections = kwargs['injections']
    order = kwargs['order']

    start = time()
    targets = list(injections.values_list('target', flat=True).distinct(
        ).order_by('target'))
    if len(targets) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'diff_targets_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': ('#008080', ),
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'diff_targets_chart',
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'legend': {
            'enabled': False
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
            'labels': {
                'format': '{value}%'
            },
            'max': 100,
            'title': {
                'text': 'Average Data Match'
            }
        }
    }
    data = injections.values_list('target').distinct().order_by(
        'target').annotate(
            avg=Avg(Case(When(result__data_diff__isnull=True, then=0),
                         default='result__data_diff'))
        ).values_list('avg', flat=True)
    chart['series'].append({'data': [x*100 for x in data]})
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
    """.replace('\n    ', '\n                        '))
    chart_data.append(chart)
    chart_list.append({
        'id': 'diff_targets_chart',
        'order': order,
        'title': 'Data Destruction By Target'})
    print('diff_targets_chart:', round(time()-start, 2), 'seconds')


def execution_time(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    injections = kwargs['injections']
    order = kwargs['order']

    start = time()
    injections = injections.exclude(result__execution_time__isnull=True).filter(
        result__returned=True)
    targets = list(injections.values_list('target', flat=True).distinct(
        ).order_by('target'))
    if len(targets) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'execution_time_targets_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': ('#008080', ),
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'execution_time_targets_chart',
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'legend': {
            'enabled': False
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
                'text': 'Average Execution Time'
            }
        }
    }
    data = list(injections.values_list('target').distinct().order_by(
        'target').annotate(avg=Avg('result__execution_time')).values_list(
            'avg', flat=True))
    chart['series'].append({'data': data})
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
    """.replace('\n    ', '\n                        '))
    chart_data.append(chart)
    chart_list.append({
        'id': 'execution_time_targets_chart',
        'order': order,
        'title': 'Average Execution Time By Target'})
    print('execution_time_targets_chart:', round(time()-start, 2), 'seconds')
