from copy import deepcopy
from django.db.models import Avg, Max, StdDev
from numpy import convolve, linspace, ones
from json import dumps
from time import time

from . import colors, colors_extra, count_intervals


def outcomes(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']

    start = time()
    injections = injections.exclude(time__isnull=True)
    if injections.count() <= 1:
        return
    xaxis_length = min(injections.count() / 10, 1000)
    times = linspace(0, injections.aggregate(Max('time'))['time__max'],
                     xaxis_length, endpoint=False).tolist()[1:]
    if len(times) <= 1:
        return
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'times_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'times_chart',
            'sourceWidth': 960,
            'sourceHeight': 540,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                # 'point': {
                #     'events': {
                #         'click': '__click_function__'
                #     }
                # },
                'stacking': True
            }
        },
        'series': [],
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': times,
            'labels': {
                'formatter': '__format_function__'
            },
            'title': {
                'text': 'Injection Time (Seconds)'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Injections'
            }
        }
    }
    window_size = 10
    chart_smooth = deepcopy(chart)
    chart_smooth['chart']['type'] = 'area'
    chart_smooth['chart']['renderTo'] = 'times_chart_smooth'
    for outcome in outcomes:
        filter_kwargs = {}
        filter_kwargs['result__outcome_category' if group_categories
                      else 'result__outcome'] = outcome
        data = count_intervals(
            injections.filter(**filter_kwargs).values_list('time', flat=True),
            times)
        chart['series'].append({'data': data, 'name': outcome})
        chart_smooth['series'].append({
            'data': convolve(
                data, ones(window_size)/window_size, 'same').tolist(),
            'name': outcome,
            'stacking': True})
    chart_data.append(dumps(chart, indent=4).replace(
        '\"__format_function__\"', """
    function() {
        return this.value.toFixed(4);
    }
    """.replace('\n    ', '\n                    ')))
    chart_data.append(dumps(chart_smooth, indent=4).replace(
        '\"__format_function__\"', """
    function() {
        return this.value.toFixed(4);
    }
    """.replace('\n    ', '\n                    ')))
    chart_list.append({
        'id': 'times_chart',
        'order': order,
        'smooth': True,
        'title': 'Injections Over Time'})
    print('times_charts', round(time()-start, 2), 'seconds')


def data_diff(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    injections = kwargs['injections']
    order = kwargs['order']

    start = time()
    injections = injections.exclude(time__isnull=True)
    if injections.count() <= 1:
        return
    xaxis_length = min(injections.count() / 10, 1000)
    times = linspace(0, injections.aggregate(Max('time'))['time__max'],
                     xaxis_length, endpoint=False).tolist()[1:]
    if len(times) <= 1:
        return
    chart = {
        'chart': {
            'renderTo': 'diff_times_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': ('#008080', ),
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'diff_times_chart',
            'sourceWidth': 960,
            'sourceHeight': 540,
            'scale': 2
        },
        'legend': {
            'enabled': False
        },
        # 'plotOptions': {
        #     'series': {
        #         'point': {
        #             'events': {
        #                 'click': '__click_function__'
        #             }
        #         }
        #     }
        # },
        'series': [{'data': []}],
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': times,
            'labels': {
                'formatter': '__format_function__'
            },
            'title': {
                'text': 'Injection Time (Seconds)'
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
    chart['series'][0]['data'] = count_intervals(
        injections.values_list('time', 'result__data_diff'), times,
        data_diff=True)
    chart_data.append(dumps(chart, indent=4).replace(
        '\"__format_function__\"', """
    function() {
        return this.value.toFixed(4);
    }
    """.replace('\n    ', '\n                    ')))
    chart_list.append({
        'id': 'diff_times_chart',
        'order': order,
        'title': 'Data Destruction Over Time'})
    print('diff_times_chart:', round(time()-start, 2), 'seconds')


def execution_times(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    results = kwargs['results']

    start = time()
    results = results.exclude(execution_time__isnull=True).filter(returned=True)
    if results.count() < 1:
        return
    avg = results.aggregate(Avg('execution_time'))['execution_time__avg']
    std_dev = results.aggregate(
        StdDev('execution_time'))['execution_time__stddev']
    std_dev_range = 3
    times = linspace(
        max(0, avg-(std_dev*std_dev_range)), avg+(std_dev*std_dev_range), 1000,
        endpoint=False).tolist()
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'execution_times_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'execution_times_chart',
            'sourceWidth': 960,
            'sourceHeight': 540,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                # 'point': {
                #     'events': {
                #         'click': '__click_function__'
                #     }
                # },
                'stacking': True
            }
        },
        'series': [],
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': times,
            'labels': {
                'formatter': '__format_function__'
            },
            'title': {
                'text': 'Execution Time (Seconds) for '
                        '(\u03bc-{0}\u03c3, \u03bc+{0}\u03c3), '
                        '\u03bc={1:.2f} & \u03c3={2:.2f}'.format(
                            std_dev_range, avg, std_dev)
            }
        },
        'yAxis': {
            'title': {
                'text': 'Results'
            }
        }
    }
    window_size = 10
    chart_smooth = deepcopy(chart)
    chart_smooth['chart']['type'] = 'area'
    chart_smooth['chart']['renderTo'] = 'execution_times_chart_smooth'
    for outcome in outcomes:
        filter_kwargs = {}
        filter_kwargs['outcome_category' if group_categories
                      else 'outcome'] = outcome
        data = count_intervals(
            results.filter(**filter_kwargs).values_list('execution_time',
                                                        flat=True),
            times)
        chart['series'].append({'data': data, 'name': outcome})
        chart_smooth['series'].append({
            'data': convolve(
                data, ones(window_size)/window_size, 'same').tolist(),
            'name': outcome,
            'stacking': True})
    chart_data.append(dumps(chart, indent=4).replace(
        '\"__format_function__\"', """
    function() {
        return this.value.toFixed(4);
    }
    """.replace('\n    ', '\n                    ')))
    chart_data.append(dumps(chart_smooth, indent=4).replace(
        '\"__format_function__\"', """
    function() {
        return this.value.toFixed(4);
    }
    """.replace('\n    ', '\n                    ')))
    chart_list.append({
        'id': 'execution_times_chart',
        'order': order,
        'smooth': True,
        'title': 'Execution Times'})
    print('execution_times_charts', round(time()-start, 2), 'seconds')
