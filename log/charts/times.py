from copy import deepcopy
from django.db.models import Avg, Max, StdDev
from numpy import convolve, linspace, ones
from json import dumps
from time import time

from log.charts import colors, colors_extra, count_intervals


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
                     xaxis_length, endpoint=False).tolist()
    times = [round(time, 4) for time in times if time]
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
                'point': {
                    'events': {
                        'click': 'click_function'
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
            'categories': times,
            'title': {
                'text': 'Injection Time (Seconds)'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Total Injections'
            }
        }
    }
    window_size = 10
    chart_smoothed = deepcopy(chart)
    chart_smoothed['chart']['type'] = 'area'
    chart_smoothed['chart']['renderTo'] = 'times_smoothed_chart'
    for outcome in outcomes:
        filter_kwargs = {}
        filter_kwargs['result__outcome_category' if group_categories
                      else 'result__outcome'] = outcome
        data = count_intervals(
            injections.filter(**filter_kwargs).values_list('time', flat=True),
            times)
        chart['series'].append({'data': data, 'name': outcome})
        chart_smoothed['series'].append({
            'data': convolve(
                data, ones(window_size)/window_size, 'same').tolist(),
            'name': outcome,
            'stacking': True})
    chart_data.append(dumps(chart_smoothed, indent=4))
    chart_list.append(('times_smoothed_chart',
                       'Injections Over Time (Window={})'.format(window_size),
                       order))
    chart = dumps(chart, indent=4)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('times_chart', 'Injections Over Time', order))
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
                     xaxis_length, endpoint=False).tolist()
    times = [round(time, 4) for time in times if time]
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
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'click_function'
                    }
                },
            }
        },
        'series': [{'data': []}],
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': times,
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
                'text': 'Average Data Diff'
            }
        }
    }
    chart['series'][0]['data'] = count_intervals(
        injections.values_list('time', 'result__data_diff'), times,
        data_diff=True)
    chart = dumps(chart, indent=4)
    chart_data.append(chart)
    chart_list.append(('diff_times_chart', 'Data Diff Over Time', order))
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
    times = [round(time, 4) for time in times if time]
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
                'point': {
                    'events': {
                        'click': 'click_function'
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
            'categories': times,
            'title': {
                'text': 'Execution Time (Seconds) for '
                        '(\u03bc-{0}\u03c3, \u03bc+{0}\u03c3)'.format(
                            std_dev_range)
            }
        },
        'yAxis': {
            'title': {
                'text': 'Total Results'
            }
        }
    }
    window_size = 10
    chart_smoothed = deepcopy(chart)
    chart_smoothed['chart']['type'] = 'area'
    chart_smoothed['chart']['renderTo'] = 'execution_times_smoothed_chart'
    for outcome in outcomes:
        filter_kwargs = {}
        filter_kwargs['outcome_category' if group_categories
                      else 'outcome'] = outcome
        data = count_intervals(
            results.filter(**filter_kwargs).values_list('execution_time',
                                                        flat=True),
            times)
        chart['series'].append({'data': data, 'name': outcome})
        chart_smoothed['series'].append({
            'data': convolve(
                data, ones(window_size)/window_size, 'same').tolist(),
            'name': outcome,
            'stacking': True})
    chart_data.append(dumps(chart, indent=4))
    chart_list.append(('execution_times_chart', 'Execution Times ('
                       '\u03bc={0:.2f}, \u03c3={1:.2f})'.format(avg, std_dev),
                       order))
    chart_data.append(dumps(chart_smoothed, indent=4))
    chart_list.append(('execution_times_smoothed_chart', 'Execution Times ('
                       '\u03bc={0:.2f}, \u03c3={1:.2f}, Window={2})'.format(
                        avg, std_dev, window_size), order))
    print('execution_times_charts', round(time()-start, 2), 'seconds')
