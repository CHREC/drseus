from django.db.models import Case, IntegerField, Sum, TextField, Value, When
from django.db.models.functions import Concat, Length, Substr
from json import dumps
from time import time

from log.charts import colors, colors_extra
from log.filters import fix_sort, fix_sort_list


def outcomes(results, injections, outcomes, group_categories, chart_data,
             chart_list, order, success=False):
    start = time()
    injections = injections.filter(target='TLB')
    tlb_entries = injections.annotate(
        tlb_index=Substr('register_index', 1,
                         Length('register_index')-2,
                         output_field=TextField())).annotate(
        register_name=Concat('register', Value(' '), 'tlb_index')
    ).values_list('register_name', flat=True).distinct(
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
                        'click': 'click_function'
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
                'text': 'Total Injections'
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
            tlb_index=Substr('register_index', 1,
                             Length('register_index')-2,
                             output_field=TextField())).annotate(
            register_name=Concat('register', Value(' '), 'tlb_index')
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
    chart_list.append(('tlbs_chart', 'TLB Entries', order))
    print('tlbs_chart:', round(time()-start, 2), 'seconds')


def fields(results, injections, outcomes, group_categories, chart_data,
           chart_list, order):
    start = time()
    fields = list(injections.filter(target='TLB').values_list(
        'field', flat=True).distinct().order_by('field'))
    if len(fields) < 1:
        return
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'tlb_fields_chart',
            'type': 'column',
            'zoomType': 'y'
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
            'categories': fields,
            'title': {
                'text': 'Injected TLB Field'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Total Injections'
            }
        }
    }
    for outcome in outcomes:
        when_kwargs = {'then': 1}
        when_kwargs['result__outcome_category' if group_categories
                    else 'result__outcome'] = outcome
        data = list(injections.filter(target='TLB').values_list(
            'field').distinct().order_by('field').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': outcome})
    chart = dumps(chart, indent=4).replace('\"click_function\"', """
    function(event) {
        window.location.assign('results?outcome='+this.series.name+
                               '&injection__field='+this.category);
    }
    """.replace('\n    ', '\n                        '))
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('tlb_fields_chart', 'TLB Fields', order))
    print('tlb_fields_chart:', round(time()-start, 2), 'seconds')
