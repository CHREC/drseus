from copy import deepcopy
from django.db.models import Avg, Case, Count, IntegerField, Sum, When
from json import dumps
from time import time

from . import colors, colors_extra


def outcomes(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    start = time()
    targets = list(injections.values_list('target', flat=True).distinct(
        ).order_by('target'))
    if len(targets) < 1:
        return
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'targets_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'targets_chart',
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': '__click_function__'
                    }
                },
                'stacking': True
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
                'text': 'Injections'
            }
        }
    }
    for outcome in outcomes:
        when_kwargs = {'then': 1}
        if success:
            when_kwargs['success'] = outcome
        else:
            when_kwargs['result__outcome_category' if group_categories
                        else 'result__outcome'] = outcome
        data = list(injections.values_list('target').distinct(
            ).order_by('target').annotate(
            count=Sum(Case(When(**when_kwargs), default=0,
                           output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': str(outcome)})
    chart_percent = deepcopy(chart)
    chart_percent['chart']['renderTo'] = 'targets_chart_percent'
    chart_percent['plotOptions']['series']['stacking'] = 'percent'
    chart_percent['yAxis'] = {
        'labels': {
            'format': '{value}%'
        },
        'title': {
            'text': 'Percent of Injections'
        }
    }
    chart_percent = dumps(chart_percent, indent=4)
    chart_percent = chart_percent.replace('\"__click_function__\"', """
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
        window.open('results?outcome='+outcome+
                    '&injection__target='+this.category+filter);
    }
    """.replace('\n    ', '\n                        '))
    if success:
        chart_percent = chart_percent.replace('?outcome=',
                                              '?injection__success=')
    elif group_categories:
        chart_percent = chart_percent.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart_percent)
    if len(outcomes) == 1 and not success:
        chart_log = deepcopy(chart)
        chart_log['chart']['renderTo'] = 'targets_chart_log'
        chart_log['yAxis']['type'] = 'logarithmic'
        chart_log = dumps(chart_log, indent=4).replace(
            '\"__click_function__\"', """
        function(event) {
            var filter;
            if (window.location.href.indexOf('?') > -1) {
                filter = window.location.href.replace(/.*\?/g, '&');
            } else {
                filter = '';
            }
            window.open('results?outcome='+this.series.name+
                        '&injection__target='+this.category+filter);
        }
        """.replace('\n    ', '\n                        '))
        if group_categories:
            chart_log = chart_log.replace('?outcome=', '?outcome_category=')
        chart_data.append(chart_log)
    chart = dumps(chart, indent=4)
    chart = chart.replace('\"__click_function__\"', """
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
        window.open('results?outcome='+outcome+
                    '&injection__target='+this.category+filter);
    }
    """.replace('\n    ', '\n                        '))
    if success:
        chart = chart.replace('?outcome=', '?injection__success=')
    elif group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append({
        'id': 'targets_chart',
        'log': len(outcomes) == 1 and not success,
        'order': order,
        'percent': True,
        'title': 'Targets'})
    print('targets_charts:', round(time()-start, 2), 'seconds')


def propagation(**kwargs):
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
                        'click': '__click_function__'
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
    chart = dumps(chart, indent=4).replace('\"__click_function__\"', """
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
                        'click': '__click_function__'
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
    chart = dumps(chart, indent=4).replace('\"__click_function__\"', """
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
                        'click': '__click_function__'
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
    chart = dumps(chart, indent=4).replace('\"__click_function__\"', """
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
