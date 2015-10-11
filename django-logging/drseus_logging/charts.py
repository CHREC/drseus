from copy import deepcopy
from django.db.models import (Avg, Case, Count, IntegerField, Sum, TextField,
                              Value, When)
from django.db.models.functions import Concat, Length, Substr
import numpy
from simplejson import dumps
from threading import Thread
from .models import result
import sys
sys.path.append('../')
from simics_targets import devices


def json_campaigns(queryset):
    campaigns = queryset.values_list('campaign__campaign_number',
                                     'campaign__command').distinct().order_by(
        'campaign__campaign_number')
    campaigns = zip(*campaigns)
    if len(campaigns[0]) < 1:
        return '[]'
    campaign_numbers = dumps(campaigns[0])
    campaigns = campaigns[1]
    outcomes = queryset.values_list('outcome_category').distinct().order_by(
        'outcome_category')
    outcomes = list(zip(*outcomes)[0])
    if 'No error' in outcomes:
        outcomes.remove('No error')
        outcomes[:0] = ('No error', )
    chart = {
        'chart': {
            'height': 600,
            'renderTo': 'campaign_chart',
            'type': 'column'
        },
        'exporting': {
            'chartOptions': {
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
            },
            'filename': 'campaigns',
            'sourceWidth': 1024,
            'sourceHeight': 576,
            'scale': 3
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'campaign_chart_click'
                    }
                },
                'stacking': 'percent'
            }
        },
        'title': {
            'text': 'DrSEUS Campaigns'
        },
        'xAxis': {
            'categories': campaigns,
            'title': {
                'text': 'Campaigns'
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
        data = queryset.values_list('campaign__command').distinct().order_by(
            'campaign__command').annotate(
                count=Sum(Case(When(outcome_category=outcome, then=1),
                               default=0, output_field=IntegerField()))
            ).values_list('count')
        chart['series'].append({'data': zip(*data)[0], 'name': outcome})
    chart = dumps(chart)
    chart = chart.replace('\"campaign_chart_click\"', """
    function(event) {
        var campaign_numbers = campaign_number_list;
        window.location.assign(''+campaign_numbers[this.x]+'/results/?'+
                               'outcome_category='+this.series.name);
    }
    """.replace('campaign_number_list', campaign_numbers))
    return '['+chart+']'


def json_campaign(campaign_data):
    if not campaign_data.use_simics:
        return '[]'
    if campaign_data.architecture == 'p2020':
        targets = devices['p2020rdb']
    elif campaign_data.architecture == 'a9':
        targets = devices['a9x2']
    else:
        return '[]'
    target_list = sorted(targets.keys())
    chart = {
        'chart': {
            'renderTo': 'device_bit_chart',
            'type': 'column'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'chartOptions': {
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
            },
            'filename': campaign_data.architecture+' targets',
            'sourceWidth': 512,
            'sourceHeight': 384,
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
    chart['series'] = [{'data': bits, }, ]
    return '['+dumps(chart)+']'


def outcome_chart(queryset, campaign_data, outcomes, group_categories,
                  chart_array):
    chart = {
        'chart': {
            'renderTo': 'outcome_chart',
            'type': 'pie'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'chartOptions': {
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
            },
            'filename': campaign_data.application+' overview',
            'sourceWidth': 640,
            'sourceHeight': 480,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'outcome_chart_click'
                    }
                }
            }
        },
        'series': [
            {
                'data': [],
                'dataLabels': {
                    'formatter': 'outcome_percentage_formatter',
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
    chart = dumps(chart).replace('\"outcome_chart_click\"', """
    function(event) {
        var outcomes = outcome_list;
        window.location.assign('../results/?outcome='+outcomes[this.x]);
    }
    """.replace('outcome_list', outcome_list))
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart = chart.replace('\"outcome_percentage_formatter\"', """
    function() {
        var outcomes = outcome_list;
        return ''+outcomes[parseInt(this.point.x)]+' '+
        Highcharts.numberFormat(this.percentage, 1)+'%';
    }
    """.replace('outcome_list', outcome_list))
    chart_array.append(chart)


def target_chart(queryset, campaign_data, outcomes, group_categories,
                 chart_array):
    targets = queryset.values_list('target').distinct().order_by('target')
    if len(targets) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'target_chart',
            'type': 'column',
            'zoomType': 'y'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'chartOptions': {
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
            },
            'filename': campaign_data.application+' targets',
            'sourceWidth': 512,
            'sourceHeight': 384,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'target_chart_click'
                    }
                }
            }
        },
        'series': [],
        'title': {
            'text': 'Targets'
        },
        'xAxis': {
            'categories': zip(*targets)[0],
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
        data = queryset.values_list('target').distinct().order_by('target'
                                                                  ).annotate(
            count=Sum(Case(When(**when_kwargs), default=0,
                           output_field=IntegerField()))
        ).values_list('count')
        chart['series'].append({'data': zip(*data)[0], 'name': outcome,
                                'stacking': True})
    chart = dumps(chart).replace('\"target_chart_click\"', """
    function(event) {
        window.location.assign('../results/?outcome='+this.series.name+
                               '&injection__target='+this.category);
    }
    """)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_array.append(chart)


def diff_target_chart(queryset, campaign_data, outcomes, group_categories,
                      chart_array):
    if not campaign_data.use_simics:
        return
    targets = queryset.values_list('target').distinct().order_by('target')
    targets = zip(*targets)[0]
    if len(targets) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'diff_target_chart',
            'type': 'column',
            'zoomType': 'y'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'chartOptions': {
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
            },
            'filename': campaign_data.application+' target diffs',
            'sourceWidth': 512,
            'sourceHeight': 384,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'target_chart_click'
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
            }
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
    chart['series'].append({'data': mem_diff_list, 'name': 'Memory Blocks',
                            'stacking': True})
    chart['series'].append({'data': reg_diff_list, 'name': 'Registers',
                            'stacking': True})
    chart_array.append(dumps(chart))


def data_diff_target_chart(queryset, campaign_data, outcomes, group_categories,
                           chart_array):
    targets = queryset.values_list('target').distinct().order_by('target')
    if len(targets) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'data_diff_target_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'chartOptions': {
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
            },
            'filename': campaign_data.application+' data errors by target',
            'sourceWidth': 1024,
            'sourceHeight': 576,
            'scale': 3
        },
        'legend': {
            'enabled': False
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'diff_time_chart_click'
                    }
                },
            }
        },
        'series': [],
        'title': {
            'text': 'Data Diff By Target'
        },
        'xAxis': {
            'categories': zip(*targets)[0],
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
                'text': 'Average Data Diff'
            }
        }
    }
    data = queryset.values_list('target').distinct().order_by(
        'target').annotate(
            avg=Avg(Case(When(result__data_diff=-1.0, then=0),
                         When(result__data_diff__isnull=True, then=0),
                         default='result__data_diff'))
        ).values_list('avg')
    data = [x*100 for x in zip(*data)[0]]
    chart['series'].append({'data': data, })
    if campaign_data.use_simics:
        chart = dumps(chart).replace('\"diff_time_chart_click\"', """
        function(event) {
            window.location.assign('../results/?injection__checkpoint_number='+
                                   this.category);
        }
        """)
    else:
        chart = dumps(chart).replace('\"diff_time_chart_click\"', """
        function(event) {
            var time = parseFloat(this.category)
            window.location.assign('../results/?injection__time_rounded='+
                                   time.toFixed(1));
        }
        """)
    chart_array.append(chart)


def register_tlb_chart(tlb, queryset, campaign_data, outcomes, group_categories,
                       chart_array):
    if not tlb:
        registers = queryset.exclude(target='TLB').annotate(
            register_name=Concat('register', Value(' '), 'register_index')
        ).values_list('register_name').distinct().order_by('register_name')
    else:
        registers = queryset.filter(target='TLB').annotate(
            tlb_index=Substr('register_index', 1,
                             Length('register_index')-2,
                             output_field=TextField()),
            register_name=Concat('register', Value(' '), 'tlb_index')
        ).values_list('register_name').distinct().order_by('register_name')
    if len(registers) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'register_chart' if not tlb else 'tlb_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'chartOptions': {
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
            },
            'filename': (campaign_data.application+' ' +
                         ('registers' if not tlb else 'tlb entries')),
            'scale': 3,
            'sourceHeight': 576,
            'sourceWidth': 1024
        },
        'title': {
            'text': 'Registers' if not tlb else 'TLB Entries'
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'register_chart_click'
                    }
                }
            }
        },
        'series': [],
        'xAxis': {
            'categories': zip(*registers)[0],
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
            ).values_list('count')
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
            ).values_list('count')
        chart['series'].append({'data': zip(*data)[0], 'name': outcome,
                                'stacking': True})
    chart = dumps(chart).replace('\"register_chart_click\"', """
    function(event) {
        var reg = this.category.split(':');
        var register = reg[0];
        var index = reg[1];
        if (index) {
            window.location.assign('../results/?outcome='+this.series.name+
                                   '&injection__register='+register+
                                   '&injection__register_index='+index);
        } else {
            window.location.assign('../results/?outcome='+this.series.name+
                                   '&injection__register='+register);
        }
    }
    """)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_array.append(chart)


def register_chart(queryset, campaign_data, outcomes, group_categories,
                   chart_array):
    register_tlb_chart(False, queryset, campaign_data, outcomes,
                       group_categories, chart_array)


def tlb_chart(queryset, campaign_data, outcomes, group_categories, chart_array):
    register_tlb_chart(True, queryset, campaign_data, outcomes,
                       group_categories, chart_array)


def field_chart(queryset, campaign_data, outcomes, group_categories,
                chart_array):
    fields = queryset.filter(target='TLB').values_list('field').distinct(
        ).order_by('field')
    if len(fields) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'field_chart',
            'type': 'column',
            'zoomType': 'y'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'chartOptions': {
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
            },
            'filename': campaign_data.application+' tlb fields',
            'sourceWidth': 512,
            'sourceHeight': 384,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'field_chart_click'
                    }
                }
            }
        },
        'series': [],
        'title': {
            'text': 'TLB Fields'
        },
        'xAxis': {
            'categories': zip(*fields)[0],
            'title': {
                'text': 'Field'
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
        data = queryset.filter(target='TLB').values_list('field').distinct(
            ).order_by('field').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
        ).values_list('count')
        chart['series'].append({'data': zip(*data)[0], 'name': outcome,
                                'stacking': True})
    chart = dumps(chart).replace('\"field_chart_click\"', """
    function(event) {
        window.location.assign('../results/?outcome='+this.series.name+
                               '&injection__field='+this.category);
    }
    """)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_array.append(chart)


def bit_chart(queryset, campaign_data, outcomes, group_categories, chart_array):
    bits = queryset.exclude(target='TLB').values_list('bit').distinct(
        ).order_by('bit')
    if len(bits) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'bit_chart',
            'type': 'column',
            'zoomType': 'y'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'chartOptions': {
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
            },
            'filename': campaign_data.application+' register bits',
            'sourceWidth': 1024,
            'sourceHeight': 576,
            'scale': 3
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'bit_chart_click'
                    }
                }
            }
        },
        'series': [],
        'title': {
            'text': 'Register Bits'
        },
        'xAxis': {
            'categories': zip(*bits)[0],
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
        data = queryset.exclude(target='TLB').values_list('bit').distinct(
            ).order_by('bit').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
        ).values_list('count')
        chart['series'].append({'data': zip(*data)[0], 'name': outcome,
                                'stacking': True})
    chart = dumps(chart).replace('\"bit_chart_click\"', """
    function(event) {
        window.location.assign('../results/?outcome='+this.series.name+
                               '&injection__bit='+this.category);
    }
    """)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_array.append(chart)


def time_chart(queryset, campaign_data, outcomes, group_categories,
               chart_array):
    if campaign_data.use_simics:
        window_size = 10
        times = queryset.values_list('checkpoint_number').distinct().order_by(
            'checkpoint_number')
    else:
        times = queryset.values_list('time_rounded').distinct().order_by(
            'time_rounded')
    if len(times) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'time_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'chartOptions': {
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
            },
            'filename': campaign_data.application+' injections over time',
            'sourceWidth': 1024,
            'sourceHeight': 576,
            'scale': 3
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'time_chart_click'
                    }
                }
            }
        },
        'series': [],
        'title': {
            'text': 'Injections Over Time'
        },
        'xAxis': {
            'categories': zip(*times)[0],
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
    if campaign_data.use_simics:
        chart_smoothed = deepcopy(chart)
        chart_smoothed['chart']['type'] = 'area'
        chart_smoothed['chart']['renderTo'] += '_smoothed'
        chart_smoothed['title']['text'] += (' (Moving Average Window Size = ' +
                                            str(window_size)+')')
    for outcome in outcomes:
        when_kwargs = {'then': 1}
        when_kwargs['result__outcome_category' if group_categories
                    else 'result__outcome'] = outcome
        if campaign_data.use_simics:
            data = queryset.values_list('checkpoint_number').distinct(
                ).order_by('checkpoint_number').annotate(
                    count=Sum(Case(When(**when_kwargs),
                                   default=0, output_field=IntegerField()))
            ).values_list('count')
            data = zip(*data)[0]
            chart_smoothed['series'].append({
                'data': numpy.convolve(data,
                                       numpy.ones(window_size)/window_size,
                                       'same').tolist(),
                'name': outcome,
                'stacking': True})
        else:
            data = queryset.values_list('time_rounded').distinct(
                ).order_by('time_rounded').annotate(
                    count=Sum(Case(When(**when_kwargs),
                                   default=0, output_field=IntegerField()))
            ).values_list('count')
            data = zip(*data)[0]
        chart['series'].append({'data': data, 'name': outcome,
                                'stacking': True})
    if campaign_data.use_simics:
        chart_array.append(dumps(chart_smoothed))
        chart = dumps(chart).replace('\"time_chart_click\"', """
        function(event) {
            window.location.assign('../results/?outcome='+this.series.name+
                                   '&injection__checkpoint_number='+
                                   this.category);
        }
        """)
    else:
        chart = dumps(chart).replace('\"time_chart_click\"', """
        function(event) {
            var time = parseFloat(this.category)
            window.location.assign('../results/?outcome='+this.series.name+
                                   '&injection__time_rounded='+time.toFixed(1));
        }
        """)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_array.append(chart)


def diff_time_chart(queryset, campaign_data, outcomes, group_categories,
                    chart_array):
    if campaign_data.use_simics:
        times = queryset.values_list('checkpoint_number').distinct().order_by(
            'checkpoint_number')
    else:
        times = queryset.values_list('time_rounded').distinct().order_by(
            'time_rounded')
    if len(times) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'diff_time_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'chartOptions': {
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
            },
            'filename': campaign_data.application+' data errors over time',
            'sourceWidth': 1024,
            'sourceHeight': 576,
            'scale': 3
        },
        'legend': {
            'enabled': False
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': 'diff_time_chart_click'
                    }
                },
            }
        },
        'series': [],
        'title': {
            'text': 'Data Diff Over Time'
        },
        'xAxis': {
            'categories': zip(*times)[0],
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
                avg=Avg(Case(When(result__data_diff=-1.0, then=0),
                             When(result__data_diff__isnull=True, then=0),
                             default='result__data_diff'))
            ).values_list('avg')
        data = [x*100 for x in zip(*data)[0]]
    else:
        data = queryset.values_list('time_rounded').distinct().order_by(
            'time_rounded').annotate(
                avg=Avg(Case(When(result__data_diff=-1.0, then=0),
                             When(result__data_diff__isnull=True, then=0),
                             default='result__data_diff'))
            ).values_list('avg')
        data = [x*100 for x in zip(*data)[0]]
    chart['series'].append({'data': data, })
    if campaign_data.use_simics:
        chart = dumps(chart).replace('\"diff_time_chart_click\"', """
        function(event) {
            window.location.assign('../results/?injection__checkpoint_number='+
                                   this.category);
        }
        """)
    else:
        chart = dumps(chart).replace('\"diff_time_chart_click\"', """
        function(event) {
            var time = parseFloat(this.category)
            window.location.assign('../results/?injection__time_rounded='+
                                   time.toFixed(1));
        }
        """)
    chart_array.append(chart)


def injection_count_chart(queryset, campaign_data, outcomes, group_categories,
                          chart_array):
    qs_result_ids = queryset.values('result__id').distinct()
    injection_counts = result.objects.filter(id__in=qs_result_ids).values_list(
        'num_injections').distinct().order_by('num_injections')
    injection_counts = zip(*injection_counts)[0]
    if len(injection_counts) < 1:
        return
    chart = {
        'chart': {
            'renderTo': 'count_chart',
            'type': 'column'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'chartOptions': {
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
            },
            'filename': campaign_data.application+' injection quantity',
            'sourceWidth': 1024,
            'sourceHeight': 576,
            'scale': 3
        },
        'plotOptions': {
            'column': {
                'dataLabels': {
                    'style': {
                        'textShadow': False
                    }
                }
            },
            'series': {
                'point': {
                    'events': {
                        'click': 'count_chart_click'
                    }
                },
                'stacking': 'percent'
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
            'labels': {
                'format': '{value}%'
            },
            'title': {
                'text': 'Percent of Results'
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
    chart = dumps(chart).replace('\"count_chart_click\"', """
    function(event) {
        window.location.assign('../results/?outcome='+this.series.name+
                               '&num_injections='+this.category);
    }
    """)
    if group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_array.append(chart)


def json_charts(queryset, campaign_data, group_categories):
    charts = (outcome_chart, target_chart, diff_target_chart,
              data_diff_target_chart, register_chart, tlb_chart, field_chart,
              bit_chart, time_chart, diff_time_chart, injection_count_chart)
    if group_categories:
        outcomes = queryset.values_list('result__outcome_category').distinct(
            ).order_by('result__outcome_category')
    else:
        outcomes = queryset.values_list('result__outcome').distinct(
            ).order_by('result__outcome')
    outcomes = list(zip(*outcomes)[0])
    if 'Latent faults' in outcomes:
        outcomes.remove('Latent faults')
        outcomes[:0] = ('Latent faults', )
    if 'Persistent faults' in outcomes:
        outcomes.remove('Persistent faults')
        outcomes[:0] = ('Persistent faults', )
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
