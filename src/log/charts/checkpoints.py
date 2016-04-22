from django.db.models import Avg, Case, When
from json import dumps
from time import time

from . import get_chart


def outcomes(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    injections = kwargs['injections']
    group_categories = kwargs['group_categories']
    order = kwargs['order']
    outcomes = kwargs['outcomes']

    start = time()
    chart_id = 'checkpoints_chart'
    injections = injections.exclude(checkpoint__isnull=True)
    checkpoints = list(injections.values_list(
        'checkpoint', flat=True).distinct().order_by('checkpoint'))
    if len(checkpoints) < 1:
        return
    chart = get_chart(chart_id, injections, 'Injected Checkpoint', 'Checkpoint',
                      'checkpoint', checkpoints, outcomes, group_categories,
                      smooth=True)
    chart_data.extend(chart)
    chart_list.append({'id': chart_id, 'order': order, 'smooth': True,
                       'title': 'Injections Over Time'})
    print(chart_id, round(time()-start, 2), 'seconds')


def data_diff(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    injections = kwargs['injections']
    order = kwargs['order']

    start = time()
    injections = injections.exclude(checkpoint__isnull=True)
    checkpoints = list(injections.values_list(
        'checkpoint', flat=True).distinct().order_by('checkpoint'))
    if len(checkpoints) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'diff_checkpoints_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': ('#008080', ),
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'diff_checkpoints_chart',
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
                        'click': '__click_function__'
                    }
                },
            }
        },
        'series': [],
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': checkpoints,
            'title': {
                'text': 'Injected Checkpoint'
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
    data = injections.values_list(
        'checkpoint').distinct().order_by('checkpoint').annotate(
            avg=Avg(Case(When(result__data_diff__isnull=True, then=0),
                         default='result__data_diff'))
        ).values_list('avg', flat=True)
    chart['series'].append({'data': [x*100 if x is not None else 0
                                     for x in data]})
    chart = dumps(chart, indent=4).replace('\"__click_function__\"', """
    function(event) {
        var filter;
        if (window.location.href.indexOf('?') > -1) {
            filter = window.location.href.replace(/.*\?/g, '&');
        } else {
            filter = '';
        }
        window.open('results?injection__checkpoint='+this.category+filter);
    }
    """.replace('\n    ', '\n                        '))
    chart_data.append(chart)
    chart_list.append({
        'id': 'diff_checkpoints_chart',
        'order': order,
        'title': 'Data Diff Over Time'})
    print('diff_checkpoints_chart:', round(time()-start, 2), 'seconds')
