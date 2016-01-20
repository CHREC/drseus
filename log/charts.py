from copy import deepcopy
from django.db.models import (Avg, Case, Count, IntegerField, Sum, TextField,
                              Value, When)
from django.db.models.functions import Concat, Length, Substr
import numpy
from simplejson import dumps
from threading import Thread

from filters import fix_sort, fix_sort_list
from models import result
from simics_targets import devices as simics_devices
from jtag_targets import devices as hardware_devices

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


export_options = {
    'chart': {
        'backgroundColor': '#FFFFFF',
        'borderWidth': 0,
        'plotBackgroundColor': '#FFFFFF',
        'plotShadow': False,
        'plotBorderWidth': 0
    },
    'title': {
        'text': None
    }
}


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
        'exporting': {
            'chartOptions': export_options,
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
        'title': {
            'text': 'DrSEUs Campaigns'
        },
        'xAxis': {
            'categories': campaigns,
            'title': {
                'text': 'Campaign IDs'
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
    chart['series'] = []
    for outcome in outcomes:
        data = list(queryset.values_list('campaign_id').distinct(
            ).order_by('campaign_id').annotate(
                count=Sum(Case(When(outcome_category=outcome, then=1),
                               default=0, output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': outcome})
    chart = dumps(chart)
    chart = chart.replace('\"chart_click\"', """
    function(event) {
        window.location.assign('/campaign/'+this.category+'/results?'+
                               'result__outcome_category='+this.series.name);
    }
    """)
    return '['+chart+']'


def target_bits_chart(campaign_data):
    if campaign_data.use_simics:
        if campaign_data.architecture == 'p2020':
            targets = simics_devices['p2020rdb']
        elif campaign_data.architecture == 'a9':
            targets = simics_devices['a9x2']
        else:
            return '[]'
    else:
        targets = hardware_devices[campaign_data.architecture]
    target_list = sorted(targets.keys())
    chart = {
        'chart': {
            'renderTo': 'target_bits_chart',
            'type': 'column'
        },
        'exporting': {
            'chartOptions': export_options,
            'filename': campaign_data.architecture+' targets',
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'legend': {
            'enabled': False
        },
        'title': {
            'text': campaign_data.architecture.upper()+' Targets'
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


def results_charts(queryset, campaign_data, group_categories):
    charts = (overview_chart, targets_charts, propagation_chart,
              diff_targets_chart, registers_chart, tlbs_chart, tlb_fields_chart,
              bits_chart, times_charts, diff_times_chart, counts_chart)
    if group_categories:
        outcomes = list(queryset.values_list(
            'result__outcome_category', flat=True).distinct(
            ).order_by('result__outcome_category'))
    else:
        outcomes = list(queryset.values_list(
            'result__outcome', flat=True).distinct(
            ).order_by('result__outcome'))
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
    chart_array = []
    threads = []
    for chart in charts:
        thread = Thread(target=chart,
                        args=(queryset, campaign_data, outcomes,
                              group_categories, chart_array))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    return '['+','.join(chart_array)+']'


def overview_chart(queryset, campaign_data, outcomes, group_categories,
                   chart_array):
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
        'exporting': {
            'chartOptions': export_options,
            'filename': campaign_data.application+' overview',
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
                'data': [],
                'dataLabels': {
                    'formatter': 'chart_formatter',
                },
                'name': 'Outcomes'
            }
        ],
        'title': {
            'text': 'Overview'
        }
    }
    qs_result_ids = queryset.values('result__id').distinct()
    filter_kwargs = {'id__in': qs_result_ids}
    for outcome in outcomes:
        filter_kwargs['outcome_category' if group_categories
                      else 'outcome'] = outcome
        chart['series'][0]['data'].append(
            (outcome, result.objects.filter(**filter_kwargs).count()))
    outcome_list = dumps(outcomes)
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        var outcomes = outcome_list;
        window.location.assign('results?result__outcome='+outcomes[this.x]);
    }
    """.replace('outcome_list', outcome_list))
    if group_categories:
        chart = chart.replace('?result__outcome=', '?result__outcome_category=')
    chart = chart.replace('\"chart_formatter\"', """
    function() {
        var outcomes = outcome_list;
        return ''+outcomes[parseInt(this.point.x)]+' '+
        Highcharts.numberFormat(this.percentage, 1)+'%';
    }
    """.replace('outcome_list', outcome_list))
    chart_array.append(chart)


def targets_charts(queryset, campaign_data, outcomes, group_categories,
                   chart_array):
    targets = list(queryset.values_list('target', flat=True).distinct(
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
        'exporting': {
            'chartOptions': export_options,
            'filename': campaign_data.application+' targets',
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
        'series': [],
        'title': {
            'text': 'Targets'
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
    for outcome in outcomes:
        when_kwargs = {'then': 1}
        when_kwargs['result__outcome_category' if group_categories
                    else 'result__outcome'] = outcome
        data = list(queryset.values_list('target').distinct(
            ).order_by('target').annotate(
            count=Sum(Case(When(**when_kwargs), default=0,
                           output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': outcome})
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
        window.location.assign('results?result__outcome='+this.series.name+
                               '&target='+this.category);
    }
    """)
    if group_categories:
        chart_percent = chart_percent.replace('?result__outcome=',
                                              '?result__outcome_category=')
    chart_array.append(chart_percent)
    if len(outcomes) == 1:
        chart_log = deepcopy(chart)
        chart_log['chart']['renderTo'] = 'targets_log_chart'
        chart_log['yAxis']['type'] = 'logarithmic'
        chart_log = dumps(chart_log).replace('\"chart_click\"', """
        function(event) {
            window.location.assign('results?result__outcome='+
                                   this.series.name+
                                   '&target='+this.category);
        }
        """)
        if group_categories:
            chart_log = chart_log.replace('?result__outcome=',
                                          '?result__outcome_category=')
        chart_array.append(chart_log)
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?result__outcome='+this.series.name+
                               '&target='+this.category);
    }
    """)
    if group_categories:
        chart = chart.replace('?result__outcome=', '?result__outcome_category=')
    chart_array.append(chart)


def propagation_chart(queryset, campaign_data, outcomes, group_categories,
                      chart_array):
    if not campaign_data.use_simics:
        return
    targets = list(queryset.values_list('target', flat=True).distinct(
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
        'exporting': {
            'chartOptions': export_options,
            'filename': campaign_data.application+' target diffs',
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
            'text': 'Fault Propagation'
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
    reg_diff_list = []
    mem_diff_list = []
    for target in targets:
        count = float(queryset.filter(target=target).count())
        reg_diff_count = queryset.filter(target=target).aggregate(
            reg_count=Count('result__simics_register_diff'))['reg_count']
        mem_diff_count = queryset.filter(target=target).aggregate(
            mem_count=Count('result__simics_memory_diff'))['mem_count']
        reg_diff_list.append(reg_diff_count/count)
        mem_diff_list.append(mem_diff_count/count)
    chart['series'].append({'data': mem_diff_list, 'name': 'Memory Blocks'})
    chart['series'].append({'data': reg_diff_list, 'name': 'Registers'})
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?target='+this.category);
    }
    """)
    chart_array.append(chart)


def diff_targets_chart(queryset, campaign_data, outcomes, group_categories,
                       chart_array):
    targets = list(queryset.values_list('target', flat=True).distinct(
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
        'exporting': {
            'chartOptions': export_options,
            'filename': campaign_data.application+' data errors by target',
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
            'text': 'Data Diff By Target'
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
    data = queryset.values_list('target').distinct().order_by(
        'target').annotate(
            avg=Avg(Case(When(result__data_diff__isnull=True, then=0),
                         default='result__data_diff'))
        ).values_list('avg', flat=True)
    chart['series'].append({'data': [x*100 for x in data]})
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?target='+this.category);
    }
    """)
    chart_array.append(chart)


def registers_chart(queryset, campaign_data, outcomes, group_categories,
                    chart_array):
    registers_tlbs_charts(False, queryset, campaign_data, outcomes,
                          group_categories, chart_array)


def tlbs_chart(queryset, campaign_data, outcomes, group_categories,
               chart_array):
    registers_tlbs_charts(True, queryset, campaign_data, outcomes,
                          group_categories, chart_array)


def registers_tlbs_charts(tlb, queryset, campaign_data, outcomes,
                          group_categories, chart_array):
    if not tlb:
        registers = queryset.exclude(target='TLB').annotate(
            register_name=Concat('register', Value(' '), 'register_index')
        ).values_list('register_name', flat=True).distinct(
        ).order_by('register_name')
    else:
        registers = queryset.filter(target='TLB').annotate(
            tlb_index=Substr('register_index', 1,
                             Length('register_index')-2,
                             output_field=TextField()),
            register_name=Concat('register', Value(' '), 'tlb_index')
        ).values_list('register_name', flat=True).distinct(
        ).order_by('register_name')
    if len(registers) < 1:
        return
    registers = sorted(registers, key=fix_sort)
    if campaign_data.use_simics and not tlb:
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
        'exporting': {
            'chartOptions': export_options,
            'filename': (campaign_data.application+' ' +
                         ('registers' if not tlb else 'tlb entries')),
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'title': {
            'text': 'Registers' if not tlb else 'TLB Entries'
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
                'text': 'Register' if not tlb else 'TLB Entry'
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
        if not tlb:
            data = queryset.exclude(target='TLB').annotate(
                register_name=Concat('register', Value(' '), 'register_index')
            ).values_list('register_name').distinct().order_by('register_name'
                                                               ).annotate(
                count=Sum(Case(When(**when_kwargs),
                               default=0, output_field=IntegerField()))
            ).values_list('register_name', 'count')
        else:
            data = queryset.filter(target='TLB').annotate(
                tlb_index=Substr('register_index', 1,
                                 Length('register_index')-2,
                                 output_field=TextField()),
                register_name=Concat('register', Value(' '), 'tlb_index')
            ).values_list('register_name').distinct().order_by('register_name'
                                                               ).annotate(
                count=Sum(Case(When(**when_kwargs),
                               default=0, output_field=IntegerField()))
            ).values_list('register_name', 'count')
        data = sorted(data, key=fix_sort_list)
        chart['series'].append({'data': zip(*data)[1], 'name': outcome})
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        var reg = this.category.split(':');
        var register = reg[0];
        var index = reg[1];
        if (index) {
            window.location.assign('results?result__outcome='+
                                   this.series.name+
                                   '&register='+register+
                                   '&register_index='+index);
        } else {
            window.location.assign('results?result__outcome='+
                                   this.series.name+
                                   '&register='+register);
        }
    }
    """)
    if group_categories:
        chart = chart.replace('?result__outcome=', '?result__outcome_category=')
    chart_array.append(chart)


def tlb_fields_chart(queryset, campaign_data, outcomes, group_categories,
                     chart_array):
    fields = list(queryset.filter(target='TLB').values_list(
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
        'exporting': {
            'chartOptions': export_options,
            'filename': campaign_data.application+' tlb fields',
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
        'series': [],
        'title': {
            'text': 'TLB Fields'
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
    for outcome in outcomes:
        when_kwargs = {'then': 1}
        when_kwargs['result__outcome_category' if group_categories
                    else 'result__outcome'] = outcome
        data = list(queryset.filter(target='TLB').values_list('field').distinct(
            ).order_by('field').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': outcome})
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?result__outcome='+this.series.name+
                               '&field='+this.category);
    }
    """)
    if group_categories:
        chart = chart.replace('?result__outcome=', '?result__outcome_category=')
    chart_array.append(chart)


def bits_chart(queryset, campaign_data, outcomes, group_categories,
               chart_array):
    bits = list(queryset.exclude(target='TLB').values_list(
        'bit', flat=True).distinct().order_by('bit'))
    if len(bits) < 1:
        return
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'bits_chart',
            'type': 'column',
            'zoomType': 'y'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'exporting': {
            'chartOptions': export_options,
            'filename': campaign_data.application+' register bits',
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
        'series': [],
        'title': {
            'text': 'Register Bits'
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
    for outcome in outcomes:
        when_kwargs = {'then': 1}
        when_kwargs['result__outcome_category' if group_categories
                    else 'result__outcome'] = outcome
        data = list(queryset.exclude(target='TLB').values_list('bit').distinct(
            ).order_by('bit').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': outcome})
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?result__outcome='+this.series.name+
                               '&bit='+this.category);
    }
    """)
    if group_categories:
        chart = chart.replace('?result__outcome=', '?result__outcome_category=')
    chart_array.append(chart)


def times_charts(queryset, campaign_data, outcomes, group_categories,
                 chart_array):
    if campaign_data.use_simics:
        times = list(queryset.values_list(
            'checkpoint_number', flat=True).distinct().order_by(
            'checkpoint_number'))
    else:
        xaxis_length = queryset.count() / 25
        times = numpy.linspace(0, campaign_data.exec_time, xaxis_length,
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
        'exporting': {
            'chartOptions': export_options,
            'filename': campaign_data.application+' injections over time',
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
        'series': [],
        'title': {
            'text': 'Injections Over Time'
        },
        'xAxis': {
            'categories': times,
            'title': {
                'text': 'Checkpoint' if campaign_data.use_simics else 'Seconds'
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
    chart_smoothed['title']['text'] += (' (Moving Average Window Size = ' +
                                        str(window_size)+')')
    for outcome in outcomes:
        if campaign_data.use_simics:
            when_kwargs = {'then': 1}
            when_kwargs['result__outcome_category' if group_categories
                        else 'result__outcome'] = outcome
            data = list(queryset.values_list('checkpoint_number').distinct(
                ).order_by('checkpoint_number').annotate(
                    count=Sum(Case(When(**when_kwargs),
                                   default=0, output_field=IntegerField()))
                ).values_list('count', flat=True))
        else:
            filter_kwargs = {}
            filter_kwargs['result__outcome_category' if group_categories
                          else 'result__outcome'] = outcome
            data = []
            for i in xrange(len(times)):
                if i+1 < len(times):
                    data.append(queryset.filter(time__gte=times[i],
                                                time__lt=times[i+1],
                                                **filter_kwargs).count())
                else:
                    data.append(queryset.filter(time__gte=times[i],
                                                **filter_kwargs).count())
        chart['series'].append({'data': data, 'name': outcome})
        chart_smoothed['series'].append({
            'data': numpy.convolve(data,
                                   numpy.ones(window_size)/window_size,
                                   'same').tolist(),
            'name': outcome,
            'stacking': True})
        chart_array.append(dumps(chart_smoothed))
    if campaign_data.use_simics:
        chart = dumps(chart).replace('\"chart_click\"', """
        function(event) {
            window.location.assign('results?result__outcome='+
                                   this.series.name+
                                   '&checkpoint_number='+
                                   this.category);
        }
        """)
    else:
        # chart = dumps(chart).replace('\"chart_click\"', """
        # function(event) {
        #     var time = parseFloat(this.category)
        #     window.location.assign('results?result__outcome='+
        #                            this.series.name+
        #                            '&time_rounded='+time.toFixed(2));
        # }
        # """)
        chart = dumps(chart)
    if group_categories:
        chart = chart.replace('?result__outcome=', '?result__outcome_category=')
    chart_array.append(chart)


def diff_times_chart(queryset, campaign_data, outcomes, group_categories,
                     chart_array):
    if campaign_data.use_simics:
        times = list(queryset.values_list(
            'checkpoint_number', flat=True).distinct().order_by(
            'checkpoint_number'))
    else:
        xaxis_length = queryset.count() / 25
        times = numpy.linspace(0, campaign_data.exec_time, xaxis_length,
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
        'exporting': {
            'chartOptions': export_options,
            'filename': campaign_data.application+' data errors over time',
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
            'text': 'Data Diff Over Time'
        },
        'xAxis': {
            'categories': times,
            'title': {
                'text': 'Checkpoint' if campaign_data.use_simics else 'Seconds'
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
    if campaign_data.use_simics:
        data = queryset.values_list('checkpoint_number').distinct().order_by(
            'checkpoint_number').annotate(
                avg=Avg(Case(When(result__data_diff__isnull=True, then=0),
                             default='result__data_diff'))
            ).values_list('avg', flat=True)
    else:
        data = []
        for i in xrange(len(times)):
            if i+1 < len(times):
                data.append(queryset.filter(time__gte=times[i],
                                            time__lt=times[i+1]).aggregate(
                    avg=Avg(Case(When(result__data_diff__isnull=True, then=0),
                                 default='result__data_diff')))['avg'])
            else:
                data.append(queryset.filter(time__gte=times[i]).aggregate(
                    avg=Avg(Case(When(result__data_diff__isnull=True, then=0),
                                 default='result__data_diff')))['avg'])
    chart['series'].append({'data': [x*100 if x is not None else 0
                                     for x in data]})
    if campaign_data.use_simics:
        chart = dumps(chart).replace('\"chart_click\"', """
        function(event) {
            window.location.assign('results?checkpoint_number='+
                                   this.category);
        }
        """)
    else:
        # chart = dumps(chart).replace('\"chart_click\"', """
        # function(event) {
        #     var time = parseFloat(this.category)
        #     window.location.assign('results?time_rounded='+
        #                            time.toFixed(2));
        # }
        # """)
        chart = dumps(chart)
    chart_array.append(chart)


def counts_chart(queryset, campaign_data, outcomes, group_categories,
                 chart_array):
    qs_result_ids = queryset.values('result__id').distinct()
    injection_counts = list(result.objects.filter(
        id__in=qs_result_ids).values_list('num_injections', flat=True).distinct(
        ).order_by('num_injections'))
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
        'exporting': {
            'chartOptions': export_options,
            'filename': campaign_data.application+' injection quantity',
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
        'series': [],
        'title': {
            'text': 'Injection Quantity'
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
    filter_kwargs = {'id__in': qs_result_ids}
    for outcome in outcomes:
        chart_data = []
        filter_kwargs['outcome_category' if group_categories
                      else 'outcome'] = outcome
        for injection_count in injection_counts:
            filter_kwargs['num_injections'] = injection_count
            chart_data.append(result.objects.filter(**filter_kwargs).count())
        chart['series'].append({'data': chart_data, 'name': outcome})
    chart_percent = deepcopy(chart)
    chart_percent['chart']['renderTo'] = 'counts_percent_chart'
    chart_percent['plotOptions']['series']['stacking'] = 'percent'
    chart_percent['yAxis']['labels'] = {'format': '{value}%'}
    chart_percent['yAxis']['title']['text'] = 'Percent of Results'
    chart_array.append(dumps(chart_percent))
    chart = dumps(chart).replace('\"chart_click\"', """
    function(event) {
        window.location.assign('results?result__outcome='+this.series.name+
                               '&result__num_injections='+this.category);
    }
    """)
    if group_categories:
        chart = chart.replace('?result__outcome=', '?result__outcome_category=')
    chart_array.append(chart)
