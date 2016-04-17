from django.db.models import Case, IntegerField, Sum, TextField, Value, When
from django.db.models.functions import Concat
from json import dumps
from time import time

from .. import fix_sort, fix_sort_list
from . import colors, colors_extra


def outcomes(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']

    start = time()
    injections = injections.filter(target='TLB').annotate(
        register_name=Concat('register', Value(' '), 'register_index',
                             output_field=TextField()))
    tlb_entries = injections.values_list('register_name', flat=True).distinct(
    ).order_by('register_name')
    if len(tlb_entries) < 1:
        return
    tlb_entries = sorted(tlb_entries, key=fix_sort)
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'tlbs_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'tlbs_chart',
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'title': {
            'text': None
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
        'xAxis': {
            'categories': tlb_entries,
            'labels': {
                'align': 'right',
                'rotation': -60,
                'step': 1,
                'x': 5,
                'y': 15
            },
            'title': {
                'text': 'Injected TLB Entry'
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
        when_kwargs['result__outcome_category' if group_categories
                    else 'result__outcome'] = outcome
        data = injections.values_list('register_name').distinct().order_by(
            'register_name').annotate(
                count=Sum(Case(When(**when_kwargs),
                               default=0, output_field=IntegerField()))
            ).values_list('register_name', 'count')
        data = sorted(data, key=fix_sort_list)
        chart['series'].append({'data': list(zip(*data))[1],
                                'name': str(outcome)})
    chart = dumps(chart, indent=4).replace('\"__click_function__\"', """
    function(event) {
        var reg = this.category.split(':');
        var register = reg[0];
        var index = reg[1];
        var filter;
        if (window.location.href.indexOf('?') > -1) {
            filter = window.location.href.replace(/.*\?/g, '&');
        } else {
            filter = '';
        }
        if (index) {
            window.open('results?outcome='+this.series.name+
                        '&injection__register='+register+
                        '&injection__register_index='+index+filter);
        } else {
            window.open('results?outcome='+this.series.name+
                        '&injection__register='+register+filter);
        }
    }
    """.replace('\n    ', '\n                        '))
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append({
        'id': 'tlbs_chart',
        'order': order,
        'title': 'TLB Entries'})
    print('tlbs_chart:', round(time()-start, 2), 'seconds')


def fields(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']

    start = time()
    injections = injections.filter(target='TLB')
    fields = list(injections.values_list(
        'field', flat=True).distinct().order_by('field'))
    if len(fields) < 1:
        return
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'tlb_fields_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'tlb_fields_chart',
            'sourceWidth': 512,
            'sourceHeight': 384,
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
            'categories': fields,
            'title': {
                'text': 'Injected TLB Field'
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
        when_kwargs['result__outcome_category' if group_categories
                    else 'result__outcome'] = outcome
        data = list(injections.values_list('field').distinct().order_by(
            'field').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': outcome})
    chart = dumps(chart, indent=4).replace('\"__click_function__\"', """
    function(event) {
        var filter;
        if (window.location.href.indexOf('?') > -1) {
            filter = window.location.href.replace(/.*\?/g, '&');
        } else {
            filter = '';
        }
        window.open('results?outcome='+this.series.name+
                    '&injection__field='+this.category+filter);
    }
    """.replace('\n    ', '\n                        '))
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append({
        'id': 'tlb_fields_chart',
        'order': order,
        'title': 'TLB Fields'})
    print('tlb_fields_chart:', round(time()-start, 2), 'seconds')
