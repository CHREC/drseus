from copy import deepcopy
from django.db.models import Case, IntegerField, Sum, When
from json import dumps
from time import time

from . import colors, colors_extra


def overview(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    results = kwargs['results']
    success = kwargs['success']
    if success:
        results = kwargs['injections']

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
                        'click': '__click_function__'
                    }
                }
            }
        },
        'series': [
            {
                'data': [],
                'dataLabels': {
                    'formatter': '__format_function__',
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
        if success:
            filter_kwargs['success'] = outcome
        else:
            filter_kwargs['outcome_category' if group_categories
                          else 'outcome'] = outcome
        chart['series'][0]['data'].append((
            str(outcome), results.filter(**filter_kwargs).count()))
    outcome_list = dumps(outcomes)
    chart = dumps(chart, indent=4)
    chart = chart.replace('\"__click_function__\"', """
    function(event) {
        var outcomes = __outcome_list__;
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
            outcome = outcomes[this.x];
        }
        window.open('results?outcome='+outcome+filter);
    }
    """.replace('\n    ', '\n                        ').replace(
        '__outcome_list__', outcome_list))
    if success:
        chart = chart.replace('?outcome=', '?injection__success=')
    elif group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart = chart.replace('\"__format_function__\"', """
    function() {
        var outcomes = __outcome_list__;
        return ''+outcomes[parseInt(this.point.x)]+' '+
        Highcharts.numberFormat(this.percentage, 1)+'%';
    }
    """.replace('\n    ', '\n                    ').replace(
        '__outcome_list__', outcome_list))
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
            'categories': injection_counts,
            'title': {
                'text': 'Injections Per Execution'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Results'
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
    chart_percent['yAxis']['title']['text'] = 'Results'
    chart_data.append(dumps(chart_percent, indent=4))
    chart = dumps(chart, indent=4).replace('\"__click_function__\"', """
    function(event) {
        var filter;
        if (window.location.href.indexOf('?') > -1) {
            filter = window.location.href.replace(/.*\?/g, '&');
        } else {
            filter = '';
        }
        window.open('results?outcome='+this.series.name+
                    '&num_injections='+this.category+filter);
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
