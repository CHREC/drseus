from django.db.models import Case, IntegerField, Sum, When
from json import dumps
from threading import Thread

from ...targets import get_targets
from .. import models
from . import (checkpoints, colors, colors_extra, other, registers, targets,
               times, tlbs)


def campaigns_chart(queryset):
    campaigns = list(queryset.values_list('campaign_id', flat=True).distinct(
        ).order_by('campaign_id'))
    if len(campaigns) < 1:
        return None
    outcomes = list(queryset.values_list(
        'outcome_category', flat=True).distinct().order_by('outcome_category'))
    if 'No error' in outcomes:
        outcomes.remove('No error')
        outcomes[:0] = ('No error', )
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'height': 600,
            'renderTo': 'campaigns_chart',
            'type': 'column'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'campaigns',
            'sourceWidth': 960,
            'sourceHeight': 540,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': '__click_function__'
                    }
                },
                'stacking': 'percent'
            }
        },
        'series': [],
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': campaigns,
            'title': {
                'text': 'Campaign ID'
            }
        },
        'yAxis': {
            'labels': {
                'format': '{value}%'
            },
            'title': {
                'text': None
            }
        }
    }
    for outcome in outcomes:
        data = list(queryset.values_list('campaign_id').distinct(
            ).order_by('campaign_id').annotate(
                count=Sum(Case(When(outcome_category=outcome, then=1),
                               default=0, output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': outcome})
    chart = dumps(chart, indent=4)
    chart = chart.replace('\"__click_function__\"', """
    function(event) {
        window.open('/campaign/'+this.category+
                    '/results?outcome_category='+this.series.name);
    }
    """.replace('\n    ', '\n                        '))
    return '[{}]'.format(chart).replace('\n', '\n                        ')


def target_bits_chart(campaign):
    if campaign.architecture not in ['a9', 'p2020']:
        return None
    injection_targets = get_targets(campaign.architecture,
                                    'simics' if campaign.simics else 'jtag',
                                    None, None)
    target_list = sorted(injection_targets.keys())
    chart = {
        'chart': {
            'renderTo': 'target_bits_chart',
            'type': 'column'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': '{} targets'.format(campaign.architecture),
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
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': target_list,
            'title': {
                'text': 'Injected Target'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Bits'
            }
        }
    }
    bits = []
    for target in target_list:
        bits.append(injection_targets[target]['total_bits'])
    chart['series'] = [{'data': bits}]
    return '[{}]'.format(dumps(chart, indent=4)).replace(
        '\"__click_function__\"', """
    function(event) {
        window.open('/campaign/__campaign_id__'+
                    '/results?injection__target='+this.category);
    }
    """).replace('__campaign_id__', str(campaign.id)).replace(
        '\n', '\n                        ')


def results_charts(results, group_categories):
    charts = (other.overview, targets.outcomes, targets.indices,
              targets.propagation, targets.execution_time, targets.data_diff,
              registers.outcomes, registers.fields, registers.bits,
              registers.access, tlbs.outcomes, tlbs.fields,
              times.execution_times, times.outcomes, times.data_diff,
              checkpoints.outcomes, checkpoints.data_diff, other.num_injections)
    injections = models.injection.objects.filter(
        result_id__in=results.values('id'))
    if group_categories:
        outcomes = list(results.values_list(
            'outcome_category', flat=True).distinct(
                    ).order_by('outcome_category'))
    else:
        outcomes = list(results.values_list('outcome', flat=True).distinct(
            ).order_by('outcome'))
    if 'Latent faults' in outcomes:
        outcomes.remove('Latent faults')
        outcomes[:0] = ('Latent faults', )
    if 'Persistent faults' in outcomes:
        outcomes.remove('Persistent faults')
        outcomes[:0] = ('Persistent faults', )
    if 'Masked faults' in outcomes:
        outcomes.remove('Masked faults')
        outcomes[:0] = ('Masked faults', )
    if 'No error' in outcomes:
        outcomes.remove('No error')
        outcomes[:0] = ('No error', )
    chart_data = []
    chart_list = []
    threads = []
    for order, chart in enumerate(charts):
        thread = Thread(target=chart, kwargs={
            'chart_data': chart_data, 'chart_list': chart_list,
            'group_categories': group_categories, 'injections': injections,
            'order': order, 'outcomes': outcomes, 'results': results,
            'success': False})
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    return (
        '[{}]'.format(',\n'.join(chart_data)).replace(
            '\n', '\n                        '),
        chart_list)


def injections_charts(injections):
    charts = (other.overview, targets.outcomes, targets.indices,
              registers.outcomes, registers.fields, registers.bits,
              registers.access)
    results = models.result.objects.filter(
        id__in=injections.values('result_id'))
    outcomes = list(injections.values_list(
        'success', flat=True).distinct().order_by('success'))
    chart_data = []
    chart_list = []
    threads = []
    for order, chart in enumerate(charts):
        thread = Thread(target=chart, kwargs={
            'chart_data': chart_data, 'chart_list': chart_list,
            'group_categories': False, 'injections': injections, 'order': order,
            'outcomes': outcomes, 'results': results, 'success': True})
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    return (
        '[{}]'.format(',\n'.join(chart_data)).replace(
            '\n', '\n                        '),
        chart_list)
