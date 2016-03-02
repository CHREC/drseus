from django.db.models import Case, IntegerField, Sum, When
from json import dumps
from threading import Thread

from log import models
from log.charts import (checkpoints, colors, colors_extra, other, registers,
                        targets, times, tlbs)
from jtag_targets import devices as hardware_devices
from simics_targets import devices as simics_devices


def campaigns_chart(queryset):
    campaigns = list(queryset.values_list('campaign_id', flat=True).distinct(
        ).order_by('campaign_id'))
    if len(campaigns) < 1:
        return '[]'
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
                        'click': 'click_function'
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
    chart = chart.replace('\"click_function\"', """
    function(event) {
        window.location.assign('/campaign/'+this.category+
                               '/results?outcome_category='+this.series.name);
    }
    """.replace('\n    ', '\n                        '))
    return '['+chart+']'.replace(
        '\n', '\n                        ')


def target_bits_chart(campaign):
    if campaign.simics:
        if campaign.architecture == 'p2020':
            injection_targets = simics_devices['p2020rdb']
        elif campaign.architecture == 'a9':
            injection_targets = simics_devices['a9x2']
        else:
            return '[]'
    else:
        injection_targets = hardware_devices[campaign.architecture]
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
            'filename': campaign.architecture+' targets',
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'legend': {
            'enabled': False
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
    return ('['+dumps(chart, indent=4)+']').replace(
        '\n', '\n                        ')


def results_charts(results, group_categories):
    charts = (other.overview, targets.outcomes, targets.propagation,
              targets.execution_time, targets.data_diff, registers.outcomes,
              tlbs.outcomes, tlbs.fields, registers.bits, times.execution_times,
              times.outcomes, times.data_diff, checkpoints.outcomes,
              checkpoints.data_diff, other.num_injections)
    injections = models.injection.objects.filter(
        result__id__in=results.values('id'))
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
        thread = Thread(target=chart,
                        args=(results, injections, outcomes, group_categories,
                              chart_data, chart_list, order))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    return ('['+',\n'.join(chart_data)+']').replace(
        '\n', '\n                        '), chart_list


def injections_charts(injections):
    charts = (targets.outcomes, registers.outcomes, registers.bits)
    results = models.result.objects.filter(
        id__in=injections.values('result_id'))
    outcomes = list(injections.values_list(
        'success', flat=True).distinct().order_by('success'))
    chart_data = []
    chart_list = []
    threads = []
    for order, chart in enumerate(charts):
        thread = Thread(target=chart,
                        args=(results, injections, outcomes, False, chart_data,
                              chart_list, order, True))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    return ('['+',\n'.join(chart_data)+']').replace(
        '\n', '\n                        '), chart_list
