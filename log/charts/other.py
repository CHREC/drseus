from copy import deepcopy
from django.db.models import Case, IntegerField, Sum, When
from json import dumps
from time import time

from log.charts import colors, colors_extra


def overview(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    results = kwargs['results']

    start = time()
    if len(outcomes) < 1:
        return
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'overview_chart',
            'type': 'pie'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'overview_chart',
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'click_function'
                    }
                }
            }
        },
        'series': [
            {
                'data': [],
                'dataLabels': {
                    'formatter': 'chart_formatter',
                },
                'name': 'Outcomes'
            }
        ],
        'title': {
            'text': None
        }
    }
    for outcome in outcomes:
        filter_kwargs = {}
        filter_kwargs['outcome_category' if group_categories
                      else 'outcome'] = outcome
        chart['series'][0]['data'].append((
            outcome, results.filter(**filter_kwargs).count()))
    outcome_list = dumps(outcomes)
    chart = dumps(chart, indent=4).replace('\"click_function\"', """
    function(event) {
        var outcomes = outcome_list;
        window.location.assign('results?outcome='+outcomes[this.x]);
    }
    """.replace('\n    ', '\n                        ').replace(
        'outcome_list', outcome_list))
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart = chart.replace('\"chart_formatter\"', """
    function() {
        var outcomes = outcome_list;
        return ''+outcomes[parseInt(this.point.x)]+' '+
        Highcharts.numberFormat(this.percentage, 1)+'%';
    }
    """.replace('\n    ', '\n                    ').replace(
        'outcome_list', outcome_list))
    chart_data.append(chart)
    chart_list.append({
        'id': 'overview_chart',
        'order': order,
        'title': 'Overview'})
    print('overview_chart:', round(time()-start, 2), 'seconds')


def num_injections(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    results = kwargs['results']

    start = time()
    results = results.exclude(
        num_injections__isnull=True).exclude(num_injections=0)
    injection_counts = list(results.values_list(
        'num_injections', flat=True).distinct().order_by('num_injections'))
    if len(injection_counts) <= 1:
        return
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'counts_chart',
            'type': 'column'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'counts_chart',
            'sourceWidth': 480,
            'sourceHeight': 360,
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
            'categories': injection_counts,
            'title': {
                'text': 'Injections Per Execution'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Total Results'
            }
        }
    }
    for outcome in outcomes:
        when_kwargs = {'then': 1}
        when_kwargs['outcome_category' if group_categories
                    else 'outcome'] = outcome
        data = list(results.values_list('num_injections').distinct().order_by(
            'num_injections').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': outcome})
    chart_percent = deepcopy(chart)
    chart_percent['chart']['renderTo'] = 'counts_chart_percent'
    chart_percent['plotOptions']['series']['stacking'] = 'percent'
    chart_percent['yAxis']['labels'] = {'format': '{value}%'}
    chart_percent['yAxis']['title']['text'] = 'Percent of Results'
    chart_data.append(dumps(chart_percent, indent=4))
    chart = dumps(chart, indent=4).replace('\"click_function\"', """
    function(event) {
        window.location.assign('results?outcome='+this.series.name+
                               '&num_injections='+this.category);
    }
    """.replace('\n    ', '\n                        '))
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append({
        'id': 'counts_chart',
        'order': order,
        'percent': True,
        'title': 'Injection Quantity'})
    print('counts_chart:', round(time()-start, 2), 'seconds')
