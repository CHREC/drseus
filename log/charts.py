from copy import deepcopy
from django.db.models import (Avg, Case, Count, IntegerField, Max, Q, Sum,
                              TextField, Value, When)
from django.db.models.functions import Concat, Length, Substr
from numpy import convolve, linspace, ones
from json import dumps
from threading import Thread
from time import time

from .filters import fix_sort, fix_sort_list
from . import models
from jtag_targets import devices as hardware_devices
from simics_targets import devices as simics_devices

colors = {
    'Data error': '#ba79f2',
    'Detected data error': '#7f6600',
    'Silet data error': '#162859',

    'Execution error': '#cc3333',
    'Hanging': '#c200f2',
    'Illegal instruction': '#ff4400',
    'Kernel error': '#591643',
    'Segmentation fault': '#f2a200',
    'Signal SIGILL': '#9fbf60',
    'Signal SIGIOT': '#88ff00',
    'Signal SIGSEGV': '#7c9da6',
    'Signal SIGTRAP': '#ff83ff',

    'No error': '#33cc70',
    'Latent faults': '#a18069',
    'Masked faults': '#185900',
    'Persistent faults': '#0099e6',

    'Post execution error': '#0061f2',

    'SCP error': '#d4a017',
    'Missing output': '#f75d59',

    'Simics error': '#006652',
    'Address not mapped': '#992645',
    'Dropping memop': '#bf6600'
}

colors_extra = ['#7cb5ec', '#434348', '#90ed7d', '#f7a35c', '#8085e9',
                '#f15c80', '#e4d354', '#2b908f', '#f45b5b', '#91e8e1']*5


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
            targets = simics_devices['p2020rdb']
        elif campaign.architecture == 'a9':
            targets = simics_devices['a9x2']
        else:
            return '[]'
    else:
        targets = hardware_devices[campaign.architecture]
    target_list = sorted(targets.keys())
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
        bits.append(targets[target]['total_bits'])
    chart['series'] = [{'data': bits}]
    return ('['+dumps(chart, indent=4)+']').replace(
        '\n', '\n                        ')


def results_charts(results, group_categories):
    charts = (overview_chart, targets_charts, propagation_chart,
              diff_targets_chart, registers_chart, tlbs_chart, tlb_fields_chart,
              register_bits_chart, execution_times_charts,
              simulated_execution_times_charts, times_charts, diff_times_chart,
              checkpoints_charts, diff_checkpoints_chart, counts_chart)
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


def overview_chart(results, injections, outcomes, group_categories, chart_data,
                   chart_list, order):
    start = time()
    if len(outcomes) <= 1:
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
    chart_list.append(('overview_chart', 'Overview', order))
    print('overview_chart:', round(time()-start, 2), 'seconds')


def targets_charts(results, injections, outcomes, group_categories, chart_data,
                   chart_list, order, success=False):
    start = time()
    targets = list(injections.values_list('target', flat=True).distinct(
        ).order_by('target'))
    if len(targets) < 1:
        return
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'targets_chart',
            'type': 'column',
            'zoomType': 'y'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'targets_chart',
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
            'categories': targets,
            'title': {
                'text': 'Injected Target'
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
        data = list(injections.values_list('target').distinct(
            ).order_by('target').annotate(
            count=Sum(Case(When(**when_kwargs), default=0,
                           output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': str(outcome)})
    chart_percent = deepcopy(chart)
    chart_percent['chart']['renderTo'] = 'targets_percent_chart'
    chart_percent['plotOptions']['series']['stacking'] = 'percent'
    chart_percent['yAxis'] = {
        'labels': {
            'format': '{value}%'
        },
        'title': {
            'text': 'Percent of Injections'
        }
    }
    chart_percent = dumps(chart_percent, indent=4).replace('\"click_function\"', """
    function(event) {
        window.location.assign('results?outcome='+this.series.name+
                               '&injection__target='+this.category);
    }
    """.replace('\n    ', '\n                        '))
    if group_categories:
        chart_percent = chart_percent.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart_percent)
    chart_list.append(('targets_percent_chart', 'Targets (Percentage Scale)',
                       2))
    if len(outcomes) == 1 and not success:
        chart_log = deepcopy(chart)
        chart_log['chart']['renderTo'] = 'targets_log_chart'
        chart_log['yAxis']['type'] = 'logarithmic'
        chart_log = dumps(chart_log, indent=4).replace('\"click_function\"', """
        function(event) {
            window.location.assign('results?outcome='+this.series.name+
                                   '&injection__target='+this.category);
        }
        """.replace('\n    ', '\n                        '))
        if group_categories:
            chart_log = chart_log.replace('?outcome=', '?outcome_category=')
        chart_data.append(chart_log)
        chart_list.append(('targets_log_chart', 'Targets (Log Scale)', 3))
    chart = dumps(chart, indent=4).replace('\"click_function\"', """
    function(event) {
        window.location.assign('results?outcome='+this.series.name+
                               '&injection__target='+this.category);
    }
    """.replace('\n    ', '\n                        '))
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('targets_chart', 'Targets', order))
    print('targets_charts:', round(time()-start, 2), 'seconds')


def propagation_chart(results, injections, outcomes, group_categories,
                      chart_data, chart_list, order):
    start = time()
    injections = injections.filter(
        Q(result_id__in=models.simics_register_diff.objects.values(
            'result_id').distinct()) |
        Q(result_id__in=models.simics_memory_diff.objects.values(
            'result_id').distinct()))
    targets = list(injections.values_list('target', flat=True).distinct(
        ).order_by('target'))
    if len(targets) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'propagation_chart',
            'type': 'column',
            'zoomType': 'y'
        },
        'colors': ('#77bfc7', '#a74ac7'),
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'propagation_chart',
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
        'series': [],
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': targets,
            'title': {
                'text': 'Injected Target'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Average Items Affected'
            },
            'type': 'logarithmic'
        }
    }
    reg_diff_list = []
    mem_diff_list = []
    for target in targets:
        count = injections.filter(target=target).count()
        reg_diff_count = injections.filter(target=target).aggregate(
            reg_count=Count('result__simics_register_diff'))['reg_count']
        mem_diff_count = injections.filter(target=target).aggregate(
            mem_count=Count('result__simics_memory_diff'))['mem_count']
        reg_diff_list.append(reg_diff_count/count)
        mem_diff_list.append(mem_diff_count/count)
    chart['series'].append({'data': mem_diff_list, 'name': 'Memory Blocks'})
    chart['series'].append({'data': reg_diff_list, 'name': 'Registers'})
    chart = dumps(chart, indent=4).replace('\"click_function\"', """
    function(event) {
        window.location.assign('results?injection__target='+this.category);
    }
    """.replace('\n    ', '\n                        '))
    chart_data.append(chart)
    chart_list.append(('propagation_chart', 'Fault Propagation', order))
    print('propagation_chart:', round(time()-start, 2), 'seconds')


def diff_targets_chart(results, injections, outcomes, group_categories,
                       chart_data, chart_list, order):
    start = time()
    targets = list(injections.values_list('target', flat=True).distinct(
        ).order_by('target'))
    if len(targets) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'diff_targets_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': ('#008080', ),
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'diff_targets_chart',
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
                        'click': 'click_function'
                    }
                }
            }
        },
        'series': [],
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': targets,
            'title': {
                'text': 'Injected Target'
            }
        },
        'yAxis': {
            'labels': {
                'format': '{value}%'
            },
            'max': 100,
            'title': {
                'text': 'Average Data Match'
            }
        }
    }
    data = injections.values_list('target').distinct().order_by(
        'target').annotate(
            avg=Avg(Case(When(result__data_diff__isnull=True, then=0),
                         default='result__data_diff'))
        ).values_list('avg', flat=True)
    chart['series'].append({'data': [x*100 for x in data]})
    chart = dumps(chart, indent=4).replace('\"click_function\"', """
    function(event) {
        window.location.assign('results?injection__target='+this.category);
    }
    """.replace('\n    ', '\n                        '))
    chart_data.append(chart)
    chart_list.append(('diff_targets_chart', 'Data Diff By Target', order))
    print('diff_targets_chart:', round(time()-start, 2), 'seconds')


def registers_chart(results, injections, outcomes,
                    group_categories, chart_data, chart_list, order,
                    success=False):
    registers_tlbs_charts(False, results, injections, outcomes,
                          group_categories, chart_data, chart_list, order,
                          success)


def tlbs_chart(results, injections, outcomes, group_categories, chart_data,
               chart_list, order, success=False):
    registers_tlbs_charts(True, results, injections, outcomes, group_categories,
                          chart_data, chart_list, order, success)


def registers_tlbs_charts(tlb, results, injections, outcomes, group_categories,
                          chart_data, chart_list, order, success):
    start = time()
    if not tlb:
        registers = injections.exclude(target='TLB').annotate(
            register_name=Concat('register', Value(' '), 'register_index')
        ).values_list('register_name', flat=True).distinct(
        ).order_by('register_name')
    else:
        registers = injections.filter(target='TLB').annotate(
            tlb_index=Substr('register_index', 1,
                             Length('register_index')-2,
                             output_field=TextField())).annotate(
            register_name=Concat('register', Value(' '), 'tlb_index')
        ).values_list('register_name', flat=True).distinct(
        ).order_by('register_name')
    if len(registers) < 1:
        return
    registers = sorted(registers, key=fix_sort)
    if not tlb:
        registers = [reg.replace('gprs ', 'r') for reg in registers]
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'registers_chart' if not tlb else 'tlbs_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'registers_chart' if not tlb else 'tlbs_chart',
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
                'text': 'Injected '+('Register' if not tlb else 'TLB Entry')
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
        if not tlb:
            data = injections.exclude(target='TLB').annotate(
                register_name=Concat('register', Value(' '), 'register_index')
            ).values_list('register_name').distinct().order_by('register_name'
                                                               ).annotate(
                count=Sum(Case(When(**when_kwargs),
                               default=0, output_field=IntegerField()))
            ).values_list('register_name', 'count')
        else:
            data = injections.filter(target='TLB').annotate(
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
    chart_list.append(('registers_chart' if not tlb else 'tlbs_chart',
                       'Registers' if not tlb else 'TLB Entries', order))
    print('tlbs_chart:' if tlb else 'registers_chart:',
          round(time()-start, 2), 'seconds')


def tlb_fields_chart(results, injections, outcomes, group_categories,
                     chart_data, chart_list, order):
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


def register_bits_chart(results, injections, outcomes, group_categories,
                        chart_data, chart_list, order, success=False):
    start = time()
    bits = list(injections.exclude(target='TLB').values_list(
        'bit', flat=True).distinct().order_by('-bit'))
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
                'text': 'Injected Bit (MSB=63/31)'
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
        data = list(injections.exclude(target='TLB').values_list(
            'bit').distinct().order_by('-bit').annotate(
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
    chart_list.append(('register_bits_chart', 'Register Bits', order))
    print('register_bits_chart:', round(time()-start, 2), 'seconds')


def execution_times_charts(results, injections, outcomes, group_categories,
                           chart_data, chart_list, order):
    start = time()
    results = results.exclude(campaign__simics=True).exclude(outcome='Hanging')
    if results.count() < 1:
        return
    xaxis_length = 50
    times = linspace(
        0, results.aggregate(Max('execution_time'))['execution_time__max'],
        xaxis_length, endpoint=False).tolist()
    times = [round(time, 4) for time in times]
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
                'text': 'Execution Time (Seconds)'
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
        data = []
        for j in range(len(times)):
            if j+1 < len(times):
                data.append(results.filter(
                    execution_time__gte=times[j], execution_time__lt=times[j+1],
                    **filter_kwargs).count())
            else:
                data.append(results.filter(
                    execution_time__gte=times[j], **filter_kwargs).count())
        chart['series'].append({'data': data, 'name': outcome})
        chart_smoothed['series'].append({
            'data': convolve(
                data, ones(window_size)/window_size, 'same').tolist(),
            'name': outcome,
            'stacking': True})
    chart_data.append(dumps(chart_smoothed, indent=4))
    chart_list.append(('execution_times_smoothed_chart',
                       'Execution Times (Moving Average Window Size = ' +
                       str(window_size)+')', order))
    chart = dumps(chart, indent=4)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('execution_times_chart', 'Execution Times', order))
    print('execution_times_charts', round(time()-start, 2), 'seconds')


def simulated_execution_times_charts(results, injections, outcomes,
                                     group_categories, chart_data, chart_list,
                                     order):
    start = time()
    results = results.exclude(campaign__simics=False).exclude(outcome='Hanging')
    if results.count() < 1:
        return
    xaxis_length = 50
    times = linspace(
        0,  results.aggregate(
            Max('simulated_execution_time'))['simulated_execution_time__max'],
        xaxis_length, endpoint=False).tolist()
    times = [round(time, 4) for time in times]
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'simulated_execution_times_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'simulated_execution_times_chart',
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
                'text': 'Simulated Execution Time (Seconds)'
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
    chart_smoothed['chart']['renderTo'] = \
        'simulated_execution_times_smoothed_chart'
    for outcome in outcomes:
        filter_kwargs = {}
        filter_kwargs['outcome_category' if group_categories
                      else 'outcome'] = outcome
        data = []
        for j in range(len(times)):
            if j+1 < len(times):
                data.append(results.filter(
                    simulated_execution_time__gte=times[j],
                    simulated_execution_time__lt=times[j+1],
                    **filter_kwargs).count())
            else:
                data.append(results.filter(
                    simulated_execution_time__gte=times[j],
                    **filter_kwargs).count())
        chart['series'].append({'data': data, 'name': outcome})
        chart_smoothed['series'].append({
            'data': convolve(
                data, ones(window_size)/window_size, 'same').tolist(),
            'name': outcome,
            'stacking': True})
    chart_data.append(dumps(chart_smoothed, indent=4))
    chart_list.append(('simulated_execution_times_smoothed_chart',
                       'Simulated Execution Times (Moving Average Window Size '
                       '= '+str(window_size)+')', order))
    chart = dumps(chart, indent=4)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('simulated_execution_times_chart',
                       'Simulated Execution Times', order))
    print('simulated_execution_times_charts', round(time()-start, 2), 'seconds')


def times_charts(results, injections, outcomes, group_categories, chart_data,
                 chart_list, order):
    start = time()
    injections = injections.exclude(time__isnull=True)
    if injections.count() < 1:
        return
    xaxis_length = min(injections.count() / 25, 50)
    times = linspace(0, injections.aggregate(Max('time'))['time__max'],
                     xaxis_length, endpoint=False).tolist()
    times = [round(time, 4) for time in times]
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
        data = []
        for j in range(len(times)):
            if j+1 < len(times):
                data.append(injections.filter(
                    time__gte=times[j], time__lt=times[j+1],
                    **filter_kwargs).count())
            else:
                data.append(injections.filter(
                    time__gte=times[j], **filter_kwargs).count())
        chart['series'].append({'data': data, 'name': outcome})
        chart_smoothed['series'].append({
            'data': convolve(
                data, ones(window_size)/window_size, 'same').tolist(),
            'name': outcome,
            'stacking': True})
    chart_data.append(dumps(chart_smoothed, indent=4))
    chart_list.append(('times_smoothed_chart',
                       'Injections Over Time (Moving Average Window Size = ' +
                       str(window_size)+')', order))
    chart = dumps(chart, indent=4)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('times_chart', 'Injections Over Time', order))
    print('times_charts', round(time()-start, 2), 'seconds')


def checkpoints_charts(results, injections, outcomes, group_categories,
                       chart_data, chart_list, order):
    start = time()
    injections = injections.exclude(checkpoint__isnull=True)
    checkpoints = list(injections.values_list(
        'checkpoint', flat=True).distinct().order_by('checkpoint'))
    if len(checkpoints) < 1:
        return
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'checkpoints_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'checkpoints_chart',
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
            'categories': checkpoints,
            'title': {
                'text': 'Injected Checkpoint'
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
    chart_smoothed['chart']['renderTo'] = 'checkpoints_smoothed_chart'
    for outcome in outcomes:
        when_kwargs = {'then': 1}
        when_kwargs['result__outcome_category' if group_categories
                    else 'result__outcome'] = outcome
        data = list(injections.values_list(
            'checkpoint').distinct().order_by('checkpoint').annotate(
                count=Sum(Case(When(**when_kwargs),
                               default=0, output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': outcome})
        chart_smoothed['series'].append({
            'data': convolve(
                data, ones(window_size)/window_size, 'same').tolist(),
            'name': outcome,
            'stacking': True})
    chart_data.append(dumps(chart_smoothed, indent=4))
    chart_list.append(('checkpoints_smoothed_chart',
                       'Injections Over Time (Moving Average Window Size = ' +
                       str(window_size)+')', order))
    chart = dumps(chart, indent=4).replace('\"click_function\"', """
    function(event) {
        window.location.assign('results?outcome='+this.series.name+
                               '&injection__checkpoint='+this.category);
    }
    """.replace('\n    ', '\n                        '))
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('checkpoints_chart', 'Injections Over Time', order))
    print('checkpoints_charts', round(time()-start, 2), 'seconds')


def diff_times_chart(results, injections, outcomes, group_categories,
                     chart_data, chart_list, order):
    start = time()
    injections = injections.exclude(time__isnull=True)
    if injections.count() < 1:
        return
    xaxis_length = min(injections.count() / 25, 100)
    times = linspace(0, injections.aggregate(Max('time'))['time__max'],
                     xaxis_length, endpoint=False).tolist()
    times = [round(time, 4) for time in times]
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
            'labels': {
                'format': '{value}%'
            },
            'max': 100,
            'title': {
                'text': 'Average Data Diff'
            }
        }
    }
    data = []
    for i in range(len(times)):
        if i+1 < len(times):
            data.append(injections.filter(
                time__gte=times[i], time__lt=times[i+1]).aggregate(
                avg=Avg(Case(When(result__data_diff__isnull=True, then=0),
                             default='result__data_diff')))['avg'])
        else:
            data.append(injections.filter(
                time__gte=times[i]).aggregate(
                avg=Avg(Case(When(result__data_diff__isnull=True, then=0),
                             default='result__data_diff')))['avg'])
    chart['series'].append({'data': [x*100 if x is not None else 0
                                     for x in data]})
    chart = dumps(chart, indent=4)
    chart_data.append(chart)
    chart_list.append(('diff_times_chart', 'Data Diff Over Time', order))
    print('diff_times_chart:', round(time()-start, 2), 'seconds')


def diff_checkpoints_chart(results, injections, outcomes, group_categories,
                           chart_data, chart_list, order):
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
                        'click': 'click_function'
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
    chart = dumps(chart, indent=4).replace('\"click_function\"', """
    function(event) {
        window.location.assign('results?injection__checkpoint='+this.category);
    }
    """.replace('\n    ', '\n                        '))
    chart_data.append(chart)
    chart_list.append(('diff_checkpoints_chart', 'Data Diff Over Time', order))
    print('diff_checkpoints_chart:', round(time()-start, 2), 'seconds')


def counts_chart(results, injections, outcomes, group_categories, chart_data,
                 chart_list, order):
    start = time()
    results = results.exclude(num_injections__isnull=True)
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
        data = list(results.exclude(num_injections=0).values_list(
            'num_injections').distinct().order_by('num_injections').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': outcome})
    chart_percent = deepcopy(chart)
    chart_percent['chart']['renderTo'] = 'counts_percent_chart'
    chart_percent['plotOptions']['series']['stacking'] = 'percent'
    chart_percent['yAxis']['labels'] = {'format': '{value}%'}
    chart_percent['yAxis']['title']['text'] = 'Percent of Results'
    chart_data.append(dumps(chart_percent, indent=4))
    chart_list.append(('counts_percent_chart',
                       'Injection Quantity (Percentage Scale)', order))
    chart = dumps(chart, indent=4).replace('\"click_function\"', """
    function(event) {
        window.location.assign('results?outcome='+this.series.name+
                               '&num_injections='+this.category);
    }
    """.replace('\n    ', '\n                        '))
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('counts_chart', 'Injection Quantity', order))
    print('counts_chart:', round(time()-start, 2), 'seconds')


def injections_charts(injections):
    charts = (targets_charts, registers_chart, register_bits_chart)
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
