from inspect import isfunction, getmembers, getmodule
from json import dumps
from threading import Thread
from time import perf_counter

from ...targets import get_targets
from .. import models
from . import charts, create_chart


def campaigns_chart(results):
    outcomes = list(results.values_list(
        'outcome_category', flat=True).distinct(
                ).order_by('outcome_category'))
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
    create_chart(chart_list, chart_data, outcomes=outcomes,
                 chart_title='Overview',
                 xaxis_title='Campaign ID',
                 xaxis_name='Campaign',
                 xaxis_type='campaign_id',
                 xaxis_model='results',
                 results=results,
                 percent=True)
    return '[{}]'.format(',\n'.join(chart_data)), chart_list


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
    """).replace('__campaign_id__', str(campaign.id))


def results_charts(results, group_categories):
    start = perf_counter()
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
    for chart in [getattr(charts, function[0]) for function in getmembers(
            charts, lambda x: isfunction(x) and getmodule(x) == charts)]:
        thread = Thread(target=chart, kwargs={
            'chart_data': chart_data, 'chart_list': chart_list,
            'group_categories': group_categories, 'injections': injections,
            'outcomes': outcomes, 'results': results})
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    print('charts total', round(perf_counter()-start, 2), 'seconds')
    return '[{}]'.format(',\n'.join(chart_data)), chart_list


def injections_charts(injections):
    start = perf_counter()
    results = models.result.objects.filter(
        id__in=injections.values('result_id'))
    outcomes = [str(outcome) for outcome in injections.values_list(
        'success', flat=True).distinct().order_by('-success')]
    chart_data = []
    chart_list = []
    threads = []
    for chart in [getattr(charts, function[0]) for function in getmembers(
            charts, lambda x: isfunction(x) and getmodule(x) == charts)]:
        thread = Thread(target=chart, kwargs={
            'chart_data': chart_data, 'chart_list': chart_list,
            'group_categories': False, 'injections': injections,
            'outcomes': outcomes, 'results': results, 'success': True})
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    print('charts total', round(perf_counter()-start, 2), 'seconds')
    return '[{}]'.format(',\n'.join(chart_data)), chart_list
