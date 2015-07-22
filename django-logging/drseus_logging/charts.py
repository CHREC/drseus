from collections import OrderedDict
from django.db.models import Count
from re import split
from simplejson import dumps
from .models import result


def fix_sort(string):
    return ''.join([text.zfill(5) if text.isdigit() else text.lower() for
                    text in split('([0-9]+)', str(string))])


def fix_reg_sort(register):
    if register[1]:
        return fix_sort(register[0]+register[1])
    else:
        return fix_sort(register[0])


def outcome_category_chart(queryset, campaign_data):
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
    return chart, zip(*outcome_categories)[0]


def outcome_chart(queryset, campaign_data):
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
    return chart, zip(*outcomes)[0]


def register_chart(queryset, campaign_data):
    registers = sorted(queryset.values_list('register',
                                            'register_index').distinct(),
                       key=fix_reg_sort)
    if len(registers) <= 1:
        return None
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
            'categories': [
                reg[0] + (':'+reg[1] if reg[1] else '') for reg in registers
            ],
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
        data = []
        for register in registers:
            data.append(queryset.filter(result__outcome=outcome,
                                        register=register[0],
                                        register_index=register[1]).count())
        chart['series'].append({'data': data, 'name': outcome,
                                'stacking': True})
    return chart


def bit_chart(queryset, campaign_data):
    bits = sorted(queryset.values_list('bit').distinct(), key=fix_sort)
    bits = zip(*bits)[0]
    if len(bits) <= 1:
        return None
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
    return chart


def time_chart(queryset, campaign_data):
    if campaign_data.use_simics:
        times = sorted(queryset.values_list('checkpoint_number').distinct(),
                       key=fix_sort)
    else:
        times = sorted(queryset.values_list('time_rounded').distinct(),
                       key=fix_sort)
    times = zip(*times)[0]
    if len(times) <= 1:
        return None
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
    return chart


def injection_count_chart(queryset, campaign_data):
    injection_counts = list(
        queryset.filter().annotate(
            injection_count=Count('result__injection')
        ).values_list('injection_count').distinct())
    injection_counts = sorted(zip(*injection_counts)[0])
    if len(injection_counts) <= 1:
        return None
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
    print data
    for outcome in outcomes:
        chart_data = []
        for injection_count in injection_counts:
            if injection_count in data[outcome]:
                chart_data.append(data[outcome][injection_count])
            else:
                chart_data.append(0)
        chart['series'].append({'data': chart_data, 'name': outcome,
                                'stacking': True})
    return chart


def json_charts(queryset, campaign_data):
    outcome_categories, outcome_category_list = \
        outcome_category_chart(queryset, campaign_data)
    outcome_category_list = dumps(outcome_category_list)
    outcomes, outcome_list = outcome_chart(queryset, campaign_data)
    outcome_list = dumps(outcome_list)
    registers = register_chart(queryset, campaign_data)
    bits = bit_chart(queryset, campaign_data)
    times = time_chart(queryset, campaign_data)
    counts = injection_count_chart(queryset, campaign_data)
    outcome_category_chart_click = """
    function(event) {
        var outcome_categories = outcome_category_list;
        window.location.assign('../results/?outcome_category='+
                               outcome_categories[this.x]);
    }
    """.replace('outcome_category_list', outcome_category_list)
    outcome_category_percentage_formatter = """
    function() {
        var outcome_categories = outcome_category_list;
        return ''+outcome_categories[parseInt(this.point.x)]+' '+
        Highcharts.numberFormat(this.percentage, 1)+'%';
    }
    """.replace('outcome_category_list', outcome_category_list)
    outcome_chart_click = """
    function(event) {
        var outcomes = outcome_list;
        window.location.assign('../results/?outcome='+outcomes[this.x]);
    }
    """.replace('outcome_list', outcome_list)
    outcome_percentage_formatter = """
    function() {
        var outcomes = outcome_list;
        return ''+outcomes[parseInt(this.point.x)]+' '+
        Highcharts.numberFormat(this.percentage, 1)+'%';
    }
    """.replace('outcome_list', outcome_list)
    register_chart_click = """
    function(event) {
        var reg = this.category.split(':');
        var register = reg[0];
        var index = reg[1];
        window.location.assign('../results/?outcome='+this.series.name+
                               '&injection__register='+register+
                               '&injection__register_index='+index);
    }
    """
    bit_chart_click = """
    function(event) {
        window.location.assign('../results/?outcome='+this.series.name+
                               '&injection__bit='+this.category);
    }
    """
    simics_time_chart_click = """
    function(event) {
        window.location.assign('../results/?outcome='+this.series.name+
                               '&injection__checkpoint_number='+this.category);
    }
    """
    hw_time_chart_click = """
    function(event) {
        var time = parseFloat(this.category)
        window.location.assign('../results/?outcome='+this.series.name+
                               '&injection__time_rounded='+time.toFixed(1));
    }
    """
    count_chart_click = """
    function(event) {
        window.location.assign('../results/?outcome='+this.series.name+
                               '&injections='+this.category);
    }
    """
    chart_array = [outcome_categories, outcomes, registers, bits, times,
                   counts]
    chart_array = [chart for chart in chart_array if chart]
    chart_array = dumps(chart_array, indent=4)
    replacements = [('\"outcome_category_chart_click\"',
                     outcome_category_chart_click),
                    ('\"outcome_category_percentage_formatter\"',
                     outcome_category_percentage_formatter),
                    ('\"outcome_chart_click\"', outcome_chart_click),
                    ('\"outcome_percentage_formatter\"',
                     outcome_percentage_formatter),
                    ('\"register_chart_click\"', register_chart_click),
                    ('\"bit_chart_click\"', bit_chart_click),
                    ('\"time_chart_click\"',
                     (simics_time_chart_click if campaign_data.use_simics
                      else hw_time_chart_click)),
                    ('\"count_chart_click\"', count_chart_click)]
    for replacement in replacements:
        chart_array = chart_array.replace(replacement[0], replacement[1])
    return chart_array
