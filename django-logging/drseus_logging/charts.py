import re
from django.db.models import Count


def fix_sort(string):
    return ''.join([text.zfill(5) if text.isdigit() else text.lower() for
                    text in re.split('([0-9]+)', str(string))])


def fix_reg_sort(register):
    if register[1]:
        return fix_sort(register[0]+register[1])
    else:
        return fix_sort(register[0])


def outcome_category_chart(queryset):
    outcome_categories = list(queryset.filter(injection_number=0).values_list(
        'result__outcome_category').annotate(
        count=Count('result__outcome_category')))
    chart = {
        'chart': {
            'renderTo': 'outcome_category_chart',
            'type': 'pie'
        },
        'exporting': {
            'filename': 'DrSEUS Outcome Categories',
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
                'colors': ['#7cb5ec', '#434348', '#90ed7d', '#f7a35c',
                           '#8085e9', '#f15c80', '#e4d354', '#2b908f',
                           '#f45b5b', '#91e8e1'],
                'data': outcome_categories,
                'dataLabels': {
                    'formatter': 'outcome_category_percentage_formatter',
                    'style': {
                        'width': 125
                    }
                },
                'name': 'Outcome Categories'
            }
        ],
        'title': {
            'text': 'Outcome Categories'
        }
    }
    return chart, zip(*outcome_categories)[0]


def outcome_chart(queryset):
    outcomes = list(queryset.filter(injection_number=0).values_list(
        'result__outcome').annotate(count=Count('result__outcome')))
    chart = {
        'chart': {
            'renderTo': 'outcome_chart',
            'type': 'pie'
        },
        'exporting': {
            'filename': 'DrSEUS Outcomes',
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
                    'style': {
                        'width': 125
                    }
                },
                'name': 'Outcomes'
            }
        ],
        'title': {
            'text': 'Outcomes'
        }

    }
    return chart, zip(*outcomes)[0]


def register_chart(queryset):
    registers = sorted(queryset.values_list('register',
                                            'register_index').distinct(),
                       key=fix_reg_sort)
    outcomes = list(queryset.values_list('result__outcome').distinct().order_by(
        'result__outcome'))
    outcomes = zip(*outcomes)[0]
    chart = {
        'chart': {
            'renderTo': 'register_chart',
            'type': 'column'
        },
        'exporting': {
            'filename': 'DrSEUS Outcomes By Register',
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
                reg[0]+(':'+reg[1]) if reg[1] else ''for reg in registers
            ],
            'labels': {
                'align': 'right',
                'rotation': -60,
                'step': 1,
                'x': 5,
                'y': 10
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
        chart['series'].append({
            'data': data, 'name': outcome, 'stacking': True
        })
    return chart


def bit_chart(queryset):
    bits = sorted(queryset.values_list('bit').distinct(), key=fix_sort)
    bits = zip(*bits)[0]
    outcomes = list(queryset.values_list('result__outcome').distinct().order_by(
        'result__outcome'))
    outcomes = zip(*outcomes)[0]
    chart = {
        'chart': {
            'renderTo': 'bit_chart',
            'type': 'column'
        },
        'exporting': {
            'sourceWidth': 1024,
            'sourceHeight': 576,
            'scale': 3,
            'filename': 'DrSEUS Outcomes By Bit'
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
        chart['series'].append({
            'data': data, 'name': outcome, 'stacking': True
        })
    return chart


def time_chart(use_simics, queryset):
    if use_simics:
        times = sorted(queryset.values_list('checkpoint_number').distinct(),
                       key=fix_sort)
    else:
        times = sorted(queryset.values_list('time_rounded').distinct(),
                       key=fix_sort)
    times = zip(*times)[0]
    outcomes = list(queryset.values_list('result__outcome').distinct().order_by(
        'result__outcome'))
    outcomes = zip(*outcomes)[0]
    chart = {
        'chart': {
            'renderTo': 'time_chart',
            'type': 'column'
        },
        'exporting': {
            'filename': 'DrSEUS Outcomes Over Time',
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
                'text': 'Checkpoint' if use_simics else 'Bit Index'
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
            if use_simics:
                data.append(queryset.filter(result__outcome=outcome,
                                            checkpoint_number=time).count())
            else:
                data.append(queryset.filter(result__outcome=outcome,
                                            time_rounded=time).count())
        chart['series'].append({
            'data': data, 'name': outcome, 'stacking': True
        })
    return chart
