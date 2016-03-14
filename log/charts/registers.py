from django.db.models import Case, IntegerField, Sum, Value, When
from django.db.models.functions import Concat
from json import dumps
from time import time

from log import fix_sort, fix_sort_list
from log.charts import colors, colors_extra


def outcomes(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    start = time()
    injections = injections.exclude(target='TLB')
    registers = injections.annotate(
        register_name=Concat('register', Value(' '), 'register_index')
    ).values_list('register_name', flat=True).distinct(
    ).order_by('register_name')
    if len(registers) < 1:
        return
    registers = sorted(registers, key=fix_sort)
    registers = [reg.replace('gprs ', 'r') for reg in registers]
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'registers_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'registers_chart',
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
                        'click': 'click_function'
                    }
                },
                'stacking': True
            }
        },
        'series': [],
        'xAxis': {
            'categories': registers,
            'labels': {
                'align': 'right',
                'rotation': -60,
                'step': 1,
                'x': 5,
                'y': 15
            },
            'title': {
                'text': 'Injected Register'
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
        data = injections.annotate(
            register_name=Concat('register', Value(' '), 'register_index')
        ).values_list('register_name').distinct().order_by('register_name'
                                                           ).annotate(
            count=Sum(Case(When(**when_kwargs),
                           default=0, output_field=IntegerField()))
        ).values_list('register_name', 'count')
        data = sorted(data, key=fix_sort_list)
        chart['series'].append({'data': list(zip(*data))[1],
                                'name': str(outcome)})
    chart = dumps(chart, indent=4).replace('\"click_function\"', """
    function(event) {
        var reg = this.category.split(':');
        var register = reg[0];
        var index = reg[1];
        if (index) {
            window.location.assign('results?outcome='+this.series.name+
                                   '&injection__register='+register+
                                   '&injection__register_index='+index);
        } else {
            window.location.assign('results?outcome='+this.series.name+
                                   '&injection__register='+register);
        }
    }
    """.replace('\n    ', '\n                        '))
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append({
        'id': 'registers_chart',
        'order': order,
        'title': 'Registers'})
    print('registers_chart:', round(time()-start, 2), 'seconds')


def bits(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    start = time()
    injections = injections.exclude(target='TLB')
    bits = list(injections.values_list('bit', flat=True).distinct().order_by(
        '-bit'))
    if len(bits) < 1:
        return
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'register_bits_chart',
            'type': 'column',
            'zoomType': 'y'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'register_bits_chart',
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
            'categories': bits,
            'title': {
                'text': 'Injected Bit (MSB=' +
                        ('31' if max(bits) < 32 else '63')+')'
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
        data = list(injections.values_list('bit').distinct().order_by(
            '-bit').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': str(outcome)})
    chart = dumps(chart, indent=4).replace('\"click_function\"', """
    function(event) {
        window.location.assign('results?outcome='+this.series.name+
                               '&injection__bit='+this.category);
    }
    """.replace('\n    ', '\n                        '))
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append({
        'id': 'register_bits_chart',
        'order': order,
        'title': 'Register Bits'})
    print('register_bits_chart:', round(time()-start, 2), 'seconds')
