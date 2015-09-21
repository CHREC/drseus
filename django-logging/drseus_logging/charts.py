from collections import OrderedDict
from django.db.models import Case, Count, IntegerField, Sum, Value, When
from django.db.models.functions import Concat
from re import split
from simplejson import dumps
from threading import Thread
from .models import result


def fix_sort(string):
    return ''.join([text.zfill(5) if text.isdigit() else text.lower() for
                    text in split('([0-9]+)', str(string))])


def fix_reg_sort(register):
    if register[1]:
        return fix_sort(register[0]+register[1])
    else:
        return fix_sort(register[0])


def campaign_chart(queryset):
    campaigns = list(
        queryset.values_list('campaign__campaign_number',
                             'campaign__command').distinct())
    campaigns = zip(*campaigns)
    if len(campaigns) <= 1:
        return None, None
    campaign_numbers = campaigns[0]
    campaigns = campaigns[1]
    outcomes = list(
        queryset.values_list('outcome').distinct().order_by('outcome'))
    outcomes = zip(*outcomes)[0]
    chart = {
        'chart': {
            'height': 600,
            'renderTo': 'campaign_chart',
            'type': 'column'
        },
        'exporting': {
            'filename': ('campaigns'),
            'sourceWidth': 1024,
            'sourceHeight': 576,
            'scale': 3,
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
                        'click': 'campaign_chart_click'
                    }
                },
                'stacking': 'percent'
            }
        },
        'title': {
            'text': 'Outcomes By Campaign'
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
        data = []
        for campaign in campaigns:
            data.append(queryset.filter(campaign__command=campaign,
                                        outcome=outcome).count())
        chart['series'].append({'data': data, 'name': outcome})
    return chart, campaign_numbers


def json_campaigns(queryset):
    chart, campaign_number_list = campaign_chart(queryset)
    campaign_number_list = dumps(campaign_number_list)
    campaign_chart_click = """
    function(event) {
        var campaign_numbers = campaign_number_list;
        window.location.assign(''+campaign_numbers[this.x]+'/results/?outcome='+
                               this.series.name);
    }
    """.replace('campaign_number_list', campaign_number_list)
    chart_array = [chart]
    chart_array = dumps(chart_array, indent=4).replace(
        '\"campaign_chart_click\"', campaign_chart_click)
    return chart_array


def outcome_category_chart(queryset, campaign_data, chart_array):
    outcomes = sorted(queryset.filter(injection_number=0).values_list(
        'result__outcome_category', 'result__outcome').annotate(
        count=Count('result__outcome_category')), key=lambda x: x[1])
    outcome_categories = OrderedDict()
    for outcome in outcomes:
        if outcome[0] in outcome_categories:
            outcome_categories[outcome[0]] += outcome[2]
        else:
            outcome_categories[outcome[0]] = outcome[2]
    outcome_categories = outcome_categories.items()
    chart = {
        'chart': {
            'renderTo': 'outcome_category_chart',
            'type': 'pie'
        },
        'exporting': {
            'filename': campaign_data.application+' outcome categories',
            'scale': 3,
            'sourceHeight': 480,
            'sourceWidth': 640
        },
        'plotOptions': {
            'pie': {
                'dataLabels': {
                    'style': {
                        'textShadow': False
                    }
                }
            },
            'series': {
                'point': {
                    'events': {
                        'click': 'outcome_category_chart_click'
                    }
                }
            }
        },
        'series': [
            {
                'colors': ['#f45b5b', '#8085e9', '#8d4654', '#7798BF',
                           '#aaeeee', '#ff0066', '#eeaaee', '#55BF3B',
                           '#DF5353', '#7798BF', '#aaeeee'],
                'data': outcome_categories,
                'dataLabels': {
                    'formatter': 'outcome_category_percentage_formatter',
                },
                'name': 'Outcome Categories'
            }
        ],
        'title': {
            'text': 'Outcome Categories'
        }
    }
    outcome_category_list = dumps(zip(*outcome_categories)[0])
    chart = dumps(chart)
    chart = chart.replace('\"outcome_category_chart_click\"', """
    function(event) {
        var outcome_categories = outcome_category_list;
        window.location.assign('../results/?outcome_category='+
                               outcome_categories[this.x]);
    }
    """.replace('outcome_category_list', outcome_category_list))
    chart = chart.replace('\"outcome_category_percentage_formatter\"',  """
    function() {
        var outcome_categories = outcome_category_list;
        return ''+outcome_categories[parseInt(this.point.x)]+' '+
        Highcharts.numberFormat(this.percentage, 1)+'%';
    }
    """.replace('outcome_category_list', outcome_category_list))
    chart_array.append(chart)


def outcome_chart(queryset, campaign_data, chart_array):
    outcomes = list(queryset.filter(injection_number=0).values_list(
        'result__outcome').annotate(count=Count('result__outcome')))
    chart = {
        'chart': {
            'renderTo': 'outcome_chart',
            'type': 'pie'
        },
        'exporting': {
            'filename': campaign_data.application+' outcomes',
            'scale': 3,
            'sourceHeight': 480,
            'sourceWidth': 640
        },
        'plotOptions': {
            'pie': {
                'dataLabels': {
                    'style': {
                        'textShadow': False
                    }
                }
            },
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
                'data': outcomes,
                'dataLabels': {
                    'formatter': 'outcome_percentage_formatter',
                },
                'name': 'Outcomes'
            }
        ],
        'title': {
            'text': 'Outcomes'
        }

    }
    outcome_list = dumps(zip(*outcomes)[0])
    chart = dumps(chart)
    chart = chart.replace('\"outcome_chart_click\"', """
    function(event) {
        var outcomes = outcome_list;
        window.location.assign('../results/?outcome='+outcomes[this.x]);
    }
    """.replace('outcome_list', outcome_list))
    chart = chart.replace('\"outcome_percentage_formatter\"', """
    function() {
        var outcomes = outcome_list;
        return ''+outcomes[parseInt(this.point.x)]+' '+
        Highcharts.numberFormat(this.percentage, 1)+'%';
    }
    """.replace('outcome_list', outcome_list))
    chart_array.append(chart)


def register_chart(queryset, campaign_data, chart_array):
    registers = queryset.annotate(
        register_name=Concat('register', Value(':'), 'register_index')
    ).values_list('register_name').distinct().order_by('register_name')
    if len(registers) <= 1:
        return
    outcomes = list(queryset.values_list('result__outcome').distinct().order_by(
        'result__outcome'))
    outcomes = zip(*outcomes)[0]
    chart = {
        'chart': {
            'renderTo': 'register_chart',
            'type': 'column'
        },
        'exporting': {
            'filename': campaign_data.application+' outcomes by register',
            'scale': 3,
            'sourceHeight': 576,
            'sourceWidth': 1024
        },
        'title': {
            'text': 'Outcomes By Register'
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
                        'click': 'register_chart_click'
                    }
                }
            }
        },
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
                'text': 'Register'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Injections'
            }
        }
    }
    chart['series'] = []
    for outcome in outcomes:
        data = queryset.annotate(
            register_name=Concat('register', Value(':'), 'register_index')
        ).values_list('register_name').distinct().order_by('register_name'
                                                           ).annotate(
            count=Sum(Case(When(result__outcome=outcome, then=1),
                           default=0, output_field=IntegerField()))
        ).values_list('register_name', 'count')
        chart['series'].append({'data': zip(*data)[1], 'name': outcome,
                                'stacking': True})
    chart_array.append(dumps(chart).replace('\"register_chart_click\"', """
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
    """))


def bit_chart(queryset, campaign_data, chart_array):
    bits = sorted(queryset.values_list('bit').distinct(), key=fix_sort)
    bits = zip(*bits)[0]
    if len(bits) <= 1:
        return
    outcomes = list(queryset.values_list('result__outcome').distinct().order_by(
        'result__outcome'))
    outcomes = zip(*outcomes)[0]
    chart = {
        'chart': {
            'renderTo': 'bit_chart',
            'type': 'column'
        },
        'exporting': {
            'filename': campaign_data.application+' outcomes by bit',
            'sourceWidth': 1024,
            'sourceHeight': 576,
            'scale': 3,
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
                        'click': 'bit_chart_click'
                    }
                }
            }
        },
        'title': {
            'text': 'Outcomes By Bit'
        },
        'xAxis': {
            'categories': bits,
            'title': {
                'text': 'Bit Index'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Injections'
            }
        }
    }
    chart['series'] = []
    for outcome in outcomes:
        data = []
        for bit in bits:
            data.append(queryset.filter(result__outcome=outcome,
                                        bit=bit).count())
        chart['series'].append({'data': data, 'name': outcome,
                                'stacking': True})
    chart_array.append(dumps(chart).replace('\"bit_chart_click\"', """
    function(event) {
        window.location.assign('../results/?outcome='+this.series.name+
                               '&injection__bit='+this.category);
    }
    """))


def time_chart(queryset, campaign_data, chart_array):
    if campaign_data.use_simics:
        times = sorted(queryset.values_list('checkpoint_number').distinct(),
                       key=fix_sort)
    else:
        times = sorted(queryset.values_list('time_rounded').distinct(),
                       key=fix_sort)
    times = zip(*times)[0]
    if len(times) <= 1:
        return
    outcomes = list(queryset.values_list('result__outcome').distinct().order_by(
        'result__outcome'))
    outcomes = zip(*outcomes)[0]
    chart = {
        'chart': {
            'renderTo': 'time_chart',
            'type': 'column'
        },
        'exporting': {
            'filename': campaign_data.application+' outcomes over time',
            'scale': 3,
            'sourceHeight': 576,
            'sourceWidth': 1024
        },
        'plotOptions': {
            'column': {
                'dataLabels': {
                    'style': {
                        'textShadow': False
                    }
                },
                'marker': {
                    'enabled': False
                }
            },
            'series': {
                'point': {
                    'events': {
                        'click': 'time_chart_click'
                    }
                }
            }
        },
        'title': {
            'text': 'Outcomes Over Time'
        },
        'xAxis': {
            'categories': times,
            'title': {
                'text': 'Checkpoint' if campaign_data.use_simics else 'Seconds'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Injections'
            }
        }
    }
    chart['series'] = []
    for outcome in outcomes:
        data = []
        for time in times:
            if campaign_data.use_simics:
                data.append(queryset.filter(result__outcome=outcome,
                                            checkpoint_number=time).count())
            else:
                data.append(queryset.filter(result__outcome=outcome,
                                            time_rounded=time).count())
        chart['series'].append({'data': data, 'name': outcome,
                                'stacking': True})
    chart = dumps(chart)
    if campaign_data.use_simics:
        chart_array.append(chart.replace('\"time_chart_click\"', """
        function(event) {
            window.location.assign('../results/?outcome='+this.series.name+
                                   '&injection__checkpoint_number='+
                                   this.category);
        }
        """))
    else:
        chart_array.append(chart.replace('\"time_chart_click\"', """
        function(event) {
            var time = parseFloat(this.category)
            window.location.assign('../results/?outcome='+this.series.name+
                                   '&injection__time_rounded='+time.toFixed(1));
        }
        """))


def injection_count_chart(queryset, campaign_data, chart_array):
    injection_counts = list(
        queryset.filter().annotate(
            injection_count=Count('result__injection')
        ).values_list('injection_count').distinct())
    injection_counts = sorted(zip(*injection_counts)[0])
    if len(injection_counts) <= 1:
        return
    outcomes = list(queryset.values_list('result__outcome').distinct().order_by(
        'result__outcome'))
    outcomes = zip(*outcomes)[0]
    result_ids = queryset.values_list('result__id').distinct()
    result_ids = zip(*result_ids)[0]
    data = {}
    for result_id in result_ids:
        result_entry = result.objects.get(id=result_id)
        if result_entry.outcome in data:
            if result_entry.injections in data[result_entry.outcome]:
                data[result_entry.outcome][result_entry.injections] += 1
            else:
                data[result_entry.outcome][result_entry.injections] = 1
        else:
            data[result_entry.outcome] = {result_entry.injections: 1}
    chart = {
        'chart': {
            'renderTo': 'count_chart',
            'type': 'column'
        },
        'exporting': {
            'filename': (campaign_data.application +
                         ' outcomes by injection quantity'),
            'sourceWidth': 1024,
            'sourceHeight': 576,
            'scale': 3,
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
                }
            }
        },
        'title': {
            'text': 'Outcomes By Injection Quantity'
        },
        'xAxis': {
            'categories': injection_counts,
            'title': {
                'text': 'Injections Per Execution'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Iterations'
            }
        }
    }
    chart['series'] = []
    for outcome in outcomes:
        chart_data = []
        for injection_count in injection_counts:
            if injection_count in data[outcome]:
                chart_data.append(data[outcome][injection_count])
            else:
                chart_data.append(0)
        chart['series'].append({'data': chart_data, 'name': outcome,
                                'stacking': True})
    chart_array.append(dumps(chart).replace('\"count_chart_click\"', """
    function(event) {
        window.location.assign('../results/?outcome='+this.series.name+
                               '&injections='+this.category);
    }
    """))


def json_charts(queryset, campaign_data):
    chart_array = []
    outcome_category_thread = Thread(target=outcome_category_chart,
                                     args=(queryset, campaign_data,
                                           chart_array))
    outcome_category_thread.start()
    outcome_thread = Thread(target=outcome_chart,
                            args=(queryset, campaign_data, chart_array))
    outcome_thread.start()
    register_thread = Thread(target=register_chart,
                             args=(queryset, campaign_data, chart_array))
    register_thread.start()
    bit_thread = Thread(target=bit_chart,
                        args=(queryset, campaign_data, chart_array))
    bit_thread.start()
    time_thread = Thread(target=time_chart,
                         args=(queryset, campaign_data, chart_array))
    time_thread.start()
    injection_count_thread = Thread(target=injection_count_chart,
                                    args=(queryset, campaign_data, chart_array))
    injection_count_thread.start()
    outcome_category_thread.join()
    outcome_thread.join()
    register_thread.join()
    bit_thread.join()
    time_thread.join()
    injection_count_thread.join()
    return '['+','.join(chart_array)+']'
