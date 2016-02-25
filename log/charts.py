from copy import deepcopy
from django.db.models import (Avg, Case, Count, IntegerField, Sum, TextField,
                              Value, When)
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
                        'click': 'chart_click'
                    }
                },
                'stacking': 'percent'
            }
        },
        'series': [None]*len(outcomes),
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

    def plot_outcome(i):
        data = list(queryset.values_list('campaign_id').distinct(
            ).order_by('campaign_id').annotate(
                count=Sum(Case(When(outcome_category=outcomes[i], then=1),
                               default=0, output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'][i] = {'data': data, 'name': outcomes[i]}
    # threads = []
    for i in range(len(outcomes)):
        plot_outcome(i)
    #     thread = Thread(target=plot_outcome, args=[i])
    #     thread.start()
    #     threads.append(thread)
    # for thread in threads:
    #     thread.join()
    chart = dumps(chart)
    chart = chart.replace('\"chart_click\"', """
    function(event) {
        window.location.assign('/campaign/'+this.category+
                               '/results?outcome_category='+this.series.name);
    }
    """)
    return '['+chart+']'


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
                'text': 'Target'
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
    return '['+dumps(chart)+']'


def results_charts(result_ids, campaign, group_categories):
    charts = (overview_chart, targets_charts, propagation_chart,
              diff_targets_chart, registers_chart, tlbs_chart, tlb_fields_chart,
              register_bits_chart, times_charts, diff_times_chart, counts_chart)
    results = models.result.objects.filter(id__in=result_ids)
    injections = models.injection.objects.filter(result__id__in=result_ids)
    if group_categories:
        outcomes = list(models.result.objects.filter(
            id__in=result_ids).values_list(
                'outcome_category', flat=True).distinct(
                    ).order_by('outcome_category'))
    else:
        outcomes = list(models.result.objects.filter(
            id__in=result_ids).values_list('outcome', flat=True).distinct(
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
    for chart in charts:
        thread = Thread(target=chart,
                        args=(campaign, results, injections, outcomes,
                              group_categories, chart_data, chart_list))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    return '['+','.join(chart_data)+']', chart_list


def overview_chart(campaign, results, injections, outcomes,
                   group_categories, chart_data, chart_list):
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
            'filename': str(campaign.id)+' overview',
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'chart_click'
                    }
                }
            }
        },
        'series': [
            {
                'data': [None]*len(outcomes),
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

    def plot_outcome(i):
        filter_kwargs = {}
        filter_kwargs['outcome_category' if group_categories
                      else 'outcome'] = outcomes[i]
        chart['series'][0]['data'][i] = (
            outcomes[i], results.filter(**filter_kwargs).count())
    # threads = []
    for i in range(len(outcomes)):
        plot_outcome(i)
    #     thread = Thread(target=plot_outcome, args=[i])
    #     thread.start()
    #     threads.append(thread)
    # for thread in threads:
    #     thread.join()
    outcome_list = dumps(outcomes)
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        var outcomes = outcome_list;
        window.location.assign('results?outcome='+outcomes[this.x]);
    }
    """.replace('outcome_list', outcome_list))
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart = chart.replace('\"chart_formatter\"', """
    function() {
        var outcomes = outcome_list;
        return ''+outcomes[parseInt(this.point.x)]+' '+
        Highcharts.numberFormat(this.percentage, 1)+'%';
    }
    """.replace('outcome_list', outcome_list))
    chart_data.append(chart)
    chart_list.append(('overview_chart', 'Overview', 0))
    print('overview_chart:', round(time()-start, 2), 'seconds')


def targets_charts(campaign, results, injections, outcomes,
                   group_categories, chart_data, chart_list, success=False):
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
            'filename': str(campaign.id)+' targets',
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'chart_click'
                    }
                },
                'stacking': True
            }
        },
        'series': [None]*len(outcomes),
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': targets,
            'title': {
                'text': 'Target'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Total Injections'
            }
        }
    }

    def plot_outcome(i):
        when_kwargs = {'then': 1}
        if success:
            when_kwargs['success'] = outcomes[i]
        else:
            when_kwargs['result__outcome_category' if group_categories
                        else 'result__outcome'] = outcomes[i]
        data = list(injections.values_list('target').distinct(
            ).order_by('target').annotate(
            count=Sum(Case(When(**when_kwargs), default=0,
                           output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'][i] = {'data': data, 'name': str(outcomes[i])}
    # threads = []
    for i in range(len(outcomes)):
        plot_outcome(i)
    #     thread = Thread(target=plot_outcome, args=[i])
    #     thread.start()
    #     threads.append(thread)
    # for thread in threads:
    #     thread.join()
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
    chart_percent = dumps(chart_percent).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?outcome='+this.series.name+
                               '&injection__target='+this.category);
    }
    """)
    if group_categories:
        chart_percent = chart_percent.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart_percent)
    chart_list.append(('targets_percent_chart', 'Targets (Percentage Scale)',
                       2))
    if len(outcomes) == 1 and not success:
        chart_log = deepcopy(chart)
        chart_log['chart']['renderTo'] = 'targets_log_chart'
        chart_log['yAxis']['type'] = 'logarithmic'
        chart_log = dumps(chart_log).replace('\"chart_click\"', """
        function(event) {
            window.location.assign('results?outcome='+this.series.name+
                                   '&injection__target='+this.category);
        }
        """)
        if group_categories:
            chart_log = chart_log.replace('?outcome=', '?outcome_category=')
        chart_data.append(chart_log)
        chart_list.append(('targets_log_chart', 'Targets (Log Scale)', 3))
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?outcome='+this.series.name+
                               '&injection__target='+this.category);
    }
    """)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('targets_chart', 'Targets', 1))
    print('targets_charts:', round(time()-start, 2), 'seconds')


def propagation_chart(campaign, results, injections,
                      outcomes, group_categories, chart_data, chart_list):
    start = time()
    if not campaign.simics:
        return
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
            'filename': str(campaign.id)+' target diffs',
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'chart_click'
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
                'text': 'Target'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Average Items Affected'
            },
            'type': 'logarithmic'
        }
    }
    reg_diff_list = [None]*len(targets)
    mem_diff_list = [None]*len(targets)

    def plot_target(i):
        count = float(injections.filter(target=targets[i]).count())
        reg_diff_count = injections.filter(target=targets[i]).aggregate(
            reg_count=Count('result__simics_register_diff'))['reg_count']
        mem_diff_count = injections.filter(target=targets[i]).aggregate(
            mem_count=Count('result__simics_memory_diff'))['mem_count']
        reg_diff_list[i] = reg_diff_count/count
        mem_diff_list[i] = mem_diff_count/count
    # threads = []
    for i in range(len(targets)):
        plot_target(i)
    #     thread = Thread(target=plot_target, args=[i])
    #     thread.start()
    #     threads.append(thread)
    # for thread in threads:
    #     thread.join()
    chart['series'].append({'data': mem_diff_list, 'name': 'Memory Blocks'})
    chart['series'].append({'data': reg_diff_list, 'name': 'Registers'})
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?injection__target='+this.category);
    }
    """)
    chart_data.append(chart)
    chart_list.append(('propagation_chart', 'Fault Propagation', 4))
    print('propagation_chart:', round(time()-start, 2), 'seconds')


def diff_targets_chart(campaign, results, injections,
                       outcomes, group_categories, chart_data, chart_list):
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
            'filename': str(campaign.id)+' data errors by target',
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
                        'click': 'chart_click'
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
                'text': 'Target'
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
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?injection__target='+this.category);
    }
    """)
    chart_data.append(chart)
    chart_list.append(('diff_targets_chart', 'Data Diff By Target', 5))
    print('diff_targets_chart:', round(time()-start, 2), 'seconds')


def registers_chart(campaign, results, injections, outcomes,
                    group_categories, chart_data, chart_list, success=False):
    registers_tlbs_charts(False, campaign, results,
                          injections, outcomes, group_categories,
                          chart_data, chart_list, success)


def tlbs_chart(campaign, results, injections, outcomes,
               group_categories, chart_data, chart_list, success=False):
    registers_tlbs_charts(True, campaign, results,
                          injections, outcomes, group_categories,
                          chart_data, chart_list, success)


def registers_tlbs_charts(tlb, campaign, results, injections,
                          outcomes, group_categories, chart_data,
                          chart_list, success):
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
    if campaign.simics and not tlb:
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
            'filename': (str(campaign.id)+' ' +
                         ('registers' if not tlb else 'tlb entries')),
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
                        'click': 'chart_click'
                    }
                },
                'stacking': True
            }
        },
        'series': [None]*len(outcomes),
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
                'text': 'Register' if not tlb else 'TLB Entry'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Total Injections'
            }
        }
    }

    def plot_outcome(i):
        when_kwargs = {'then': 1}
        if success:
            when_kwargs['success'] = outcomes[i]
        else:
            when_kwargs['result__outcome_category' if group_categories
                        else 'result__outcome'] = outcomes[i]
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
        chart['series'][i] = {'data': list(zip(*data))[1],
                              'name': str(outcomes[i])}
    # threads = []
    for i in range(len(outcomes)):
        plot_outcome(i)
    #     thread = Thread(target=plot_outcome, args=[i])
    #     thread.start()
    #     threads.append(thread)
    # for thread in threads:
    #     thread.join()
    chart = dumps(chart).replace('\"chart_click\"', """
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
    """)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('registers_chart' if not tlb else 'tlbs_chart',
                       'Registers' if not tlb else 'TLB Entries',
                       6 if not tlb else 7))
    print('tlbs_chart:' if tlb else 'registers_chart:',
          round(time()-start, 2), 'seconds')


def tlb_fields_chart(campaign, results, injections, outcomes,
                     group_categories, chart_data, chart_list):
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
            'filename': str(campaign.id)+' tlb fields',
            'sourceWidth': 512,
            'sourceHeight': 384,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'chart_click'
                    }
                },
                'stacking': True
            }
        },
        'series': [None]*len(outcomes),
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': fields,
            'title': {
                'text': 'TLB Field'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Total Injections'
            }
        }
    }

    def plot_outcome(i):
        when_kwargs = {'then': 1}
        when_kwargs['result__outcome_category' if group_categories
                    else 'result__outcome'] = outcomes[i]
        data = list(injections.filter(target='TLB').values_list(
            'field').distinct().order_by('field').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'][i] = {'data': data, 'name': outcomes[i]}
    # threads = []
    for i in range(len(outcomes)):
        plot_outcome(i)
    #     thread = Thread(target=plot_outcome, args=[i])
    #     thread.start()
    #     threads.append(thread)
    # for thread in threads:
    #     thread.join()
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?outcome='+this.series.name+
                               '&injection__field='+this.category);
    }
    """)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('tlb_fields_chart', 'TLB Fields', 8))
    print('tlb_fields_chart:', round(time()-start, 2), 'seconds')


def register_bits_chart(campaign, results, injections,
                        outcomes, group_categories, chart_data, chart_list,
                        success=False):
    start = time()
    bits = list(injections.exclude(target='TLB').values_list(
        'bit', flat=True).distinct().order_by('bit'))
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
            'filename': str(campaign.id)+' register bits',
            'sourceWidth': 960,
            'sourceHeight': 540,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'chart_click'
                    }
                },
                'stacking': True
            }
        },
        'series': [None]*len(outcomes),
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': bits,
            'title': {
                'text': 'Bit Index'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Total Injections'
            }
        }
    }

    def plot_outcome(i):
        when_kwargs = {'then': 1}
        if success:
            when_kwargs['success'] = outcomes[i]
        else:
            when_kwargs['result__outcome_category' if group_categories
                        else 'result__outcome'] = outcomes[i]
        data = list(injections.exclude(target='TLB').values_list(
            'bit').distinct().order_by('bit').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'][i] = {'data': data, 'name': str(outcomes[i])}
    # threads = []
    for i in range(len(outcomes)):
        plot_outcome(i)
    #     thread = Thread(target=plot_outcome, args=[i])
    #     thread.start()
    #     threads.append(thread)
    # for thread in threads:
    #     thread.join()
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?outcome='+this.series.name+
                               '&injection__bit='+this.category);
    }
    """)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('register_bits_chart', 'Register Bits', 9))
    print('register_bits_chart:', round(time()-start, 2), 'seconds')


def times_charts(campaign, results, injections, outcomes,
                 group_categories, chart_data, chart_list):
    start = time()
    if campaign.simics:
        times = list(injections.values_list(
            'checkpoint_number', flat=True).distinct().order_by(
            'checkpoint_number'))
    else:
        xaxis_length = min(injections.count() / 25, 50)
        times = linspace(0, campaign.exec_time, xaxis_length,
                         endpoint=False).tolist()
        times = [round(time, 4) for time in times]
    if len(times) < 1:
        return
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
            'filename': str(campaign.id)+' injections over time',
            'sourceWidth': 960,
            'sourceHeight': 540,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'chart_click'
                    }
                },
                'stacking': True
            }
        },
        'series': [None]*len(outcomes),
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': times,
            'title': {
                'text': 'Checkpoint' if campaign.simics else 'Seconds'
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

    def plot_outcome(i):
        if campaign.simics:
            when_kwargs = {'then': 1}
            when_kwargs['result__outcome_category' if group_categories
                        else 'result__outcome'] = outcomes[i]
            data = list(injections.values_list(
                'checkpoint_number').distinct().order_by(
                'checkpoint_number').annotate(
                    count=Sum(Case(When(**when_kwargs),
                                   default=0, output_field=IntegerField()))
                ).values_list('count', flat=True))
        else:
            filter_kwargs = {}
            filter_kwargs['result__outcome_category' if group_categories
                          else 'result__outcome'] = outcomes[i]
            data = []
            for j in range(len(times)):
                if j+1 < len(times):
                    data.append(injections.filter(
                        time__gte=times[j], time__lt=times[j+1],
                        **filter_kwargs).count())
                else:
                    data.append(injections.filter(
                        time__gte=times[j], **filter_kwargs).count())
        chart['series'][i] = {'data': data, 'name': outcomes[i]}
        chart_smoothed['series'][i] = {
            'data': convolve(
                data, ones(window_size)/window_size, 'same').tolist(),
            'name': outcomes[i],
            'stacking': True}
    # threads = []
    for i in range(len(outcomes)):
        plot_outcome(i)
    #     thread = Thread(target=plot_outcome, args=[i])
    #     thread.start()
    #     threads.append(thread)
    # for thread in threads:
    #     thread.join()
    chart_data.append(dumps(chart_smoothed))
    chart_list.append(('times_smoothed_chart',
                       'Injections Over Time (Moving Average Window Size = ' +
                       str(window_size)+')', 11))
    if campaign.simics:
        chart = dumps(chart).replace('\"chart_click\"', """
        function(event) {
            window.location.assign('results?outcome='+this.series.name+
                                   '&injection__checkpoint_number='+
                                   this.category);
        }
        """)
    else:
        # chart = dumps(chart).replace('\"chart_click\"', """
        # function(event) {
        #     var time = parseFloat(this.category)
        #     window.location.assign('results?outcome='+this.series.name+
        #                            '&injection__time_rounded='+
        #                            time.toFixed(2));
        # }
        # """)
        chart = dumps(chart)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('times_chart', 'Injections Over Time', 10))
    print('times_charts', round(time()-start, 2), 'seconds')


def diff_times_chart(campaign, results, injections, outcomes,
                     group_categories, chart_data, chart_list):
    start = time()
    if campaign.simics:
        times = list(injections.values_list(
            'checkpoint_number', flat=True).distinct().order_by(
            'checkpoint_number'))
    else:
        xaxis_length = min(injections.count() / 25, 100)
        times = linspace(0, campaign.exec_time, xaxis_length,
                         endpoint=False).tolist()
        times = [round(time, 4) for time in times]
    if len(times) < 1:
        return
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
            'filename': str(campaign.id)+' data errors over time',
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
                        'click': 'chart_click'
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
                'text': 'Checkpoint' if campaign.simics else 'Seconds'
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
    if campaign.simics:
        data = injections.values_list(
            'checkpoint_number').distinct().order_by(
            'checkpoint_number').annotate(
                avg=Avg(Case(When(result__data_diff__isnull=True, then=0),
                             default='result__data_diff'))
            ).values_list('avg', flat=True)
    else:
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
    if campaign.simics:
        chart = dumps(chart).replace('\"chart_click\"', """
        function(event) {
            window.location.assign('results?injection__checkpoint_number='+
                                   this.category);
        }
        """)
    else:
        # chart = dumps(chart).replace('\"chart_click\"', """
        # function(event) {
        #     var time = parseFloat(this.category)
        #     window.location.assign('results?injection__time_rounded='+
        #                            time.toFixed(2));
        # }
        # """)
        chart = dumps(chart)
    chart_data.append(chart)
    chart_list.append(('diff_times_chart', 'Data Diff Over Time', 12))
    print('diff_times_chart:', round(time()-start, 2), 'seconds')


def counts_chart(campaign, results, injections, outcomes,
                 group_categories, chart_data, chart_list):
    start = time()
    injection_counts = list(results.exclude(
        num_injections=0).values_list(
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
            'filename': str(campaign.id)+' injection quantity',
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'chart_click'
                    }
                },
                'stacking': True
            }
        },
        'series': [None]*len(outcomes),
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

    def plot_outcome(i):
        when_kwargs = {'then': 1}
        when_kwargs['outcome_category' if group_categories
                    else 'outcome'] = outcomes[i]
        data = list(results.exclude(num_injections=0).values_list(
            'num_injections').distinct().order_by('num_injections').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'][i] = {'data': data, 'name': outcomes[i]}
    # threads = []
    for i in range(len(outcomes)):
        plot_outcome(i)
    #     thread = Thread(target=plot_outcome, args=[i])
    #     thread.start()
    #     threads.append(thread)
    # for thread in threads:
    #     thread.join()
    chart_percent = deepcopy(chart)
    chart_percent['chart']['renderTo'] = 'counts_percent_chart'
    chart_percent['plotOptions']['series']['stacking'] = 'percent'
    chart_percent['yAxis']['labels'] = {'format': '{value}%'}
    chart_percent['yAxis']['title']['text'] = 'Percent of Results'
    chart_data.append(dumps(chart_percent))
    chart_list.append(('counts_percent_chart',
                       'Injection Quantity (Percentage Scale)', 14))
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?outcome='+this.series.name+
                               '&num_injections='+this.category);
    }
    """)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append(('counts_chart', 'Injection Quantity', 13))
    print('counts_chart:', round(time()-start, 2), 'seconds')


def injections_charts(result_ids, campaign):
    charts = (targets_charts, registers_chart, register_bits_chart)
    results = models.result.objects.filter(id__in=result_ids)
    injections = models.injection.objects.filter(
        result__id__in=result_ids)
    outcomes = list(models.injection.objects.filter(
        result_id__in=result_ids).values_list(
        'success', flat=True).distinct().order_by('success'))
    chart_data = []
    chart_list = []
    threads = []
    for chart in charts:
        thread = Thread(target=chart,
                        args=(campaign, results, injections,
                              outcomes, False, chart_data, chart_list, True))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    return '['+','.join(chart_data)+']', chart_list
