from django.shortcuts import render_to_response, render
from django.db.models import Sum, Count
from chartit import DataPool, Chart, PivotChart, PivotDataPool
from django_tables2 import RequestConfig
from .models import (campaign_data, simics_campaign_data, simics_result,
                     simics_register_diff, simics_memory_diff)
from .tables import (simics_result_table, simics_register_diff_table,
                     simics_memory_diff_table)
from .filters import simics_result_filter, simics_register_diff_filter


def register_chart(request, title, sidebar_items):
    queryset = simics_result.objects.all()
    fltr = simics_result_filter(request.GET, queryset=queryset)
    datasource = PivotDataPool(
        series=[
            {
                'options': {
                    'source': fltr.qs,
                    'categories': [
                        'injection__register', 'injection__register_index',
                    ],
                    'legend_by': 'outcome'
                },
                'terms': {
                    'injections': Sum('qty')
                }
            }
        ],
        # sortf_mapf_mts=(lambda x: int(x[0]), None, False)
    )

    chart = PivotChart(
        datasource=datasource,
        series_options=[
            {
                'options': {
                    'type': 'column',
                    'stacking': True
                },
                'terms': ['injections']
            }
        ],
        chart_options={
            'title': {
                'text': ''
            },
            'xAxis': {
                'title': {
                    'text': 'Register'
                },
                'labels': {
                    'align': 'right',
                    'y': 10,
                    'rotation': '-60',
                }
            },
            'yAxis': {
                'title': {
                    'text': 'Number of Injections'
                }
            }
        }
    )

    return render_to_response(
        'chart.html',
        {
            'filter': fltr,
            'chart_list': chart,
            'title': title,
            'sidebar_items': sidebar_items
        }
    )


def bit_chart(request, title, sidebar_items):
    queryset = simics_result.objects.all()
    fltr = simics_result_filter(request.GET, queryset=queryset)
    datasource = PivotDataPool(
        series=[
            {
                'options': {
                    'source': fltr.qs,
                    'categories': [
                        'injection__bit',
                    ],
                    'legend_by': 'outcome'
                },
                'terms': {
                    'injections': Sum('qty')
                }
            }
        ],
        sortf_mapf_mts=(lambda x: int(x[0]), None, False)
    )

    chart = PivotChart(
        datasource=datasource,
        series_options=[
            {
                'options': {
                    'type': 'column',
                    'stacking': True
                },
                'terms': ['injections']
            }
        ],
        chart_options={
            'title': {
                'text': ''
            },
            'xAxis': {
                'title': {
                    'text': 'Bit'
                }
            },
            'yAxis': {
                'title': {
                    'text': 'Number of Injections'
                }
            }
        }
    )

    return render_to_response(
        'chart.html',
        {
            'filter': fltr,
            'chart_list': chart,
            'title': title,
            'sidebar_items': sidebar_items
        }
    )


def outcome_chart(request, title, sidebar_items):
    queryset = simics_result.objects.values('outcome').\
        annotate(qty=Count('outcome'))
    fltr = simics_result_filter(request.GET, queryset=queryset)
    datasource = DataPool(
        series=[
            {
                'options': {
                    'source': fltr.qs
                },
                'terms': ['outcome', 'qty']
            }
        ],
    )

    chart = Chart(
        datasource=datasource,
        series_options=[
            {
                'options': {
                    'type': 'pie',
                },
                'terms': {
                    'outcome': ['qty']
                }
            }
        ],
        chart_options={
            'title': {
                'text': ' '
            },
        }
    )

    return render_to_response(
        'chart.html',
        {
            'filter': fltr,
            'chart_list': chart,
            'title': title,
            'sidebar_items': sidebar_items
        }
    )


def table(request, title, sidebar_items):
    campaign_data_info = campaign_data.objects.get()
    simics_campaign_data_info = simics_campaign_data.objects.get()
    queryset = simics_result.objects.all().annotate(
        register_errors=Count('simics_register_diff'),
        memory_errors=Count('simics_memory_diff')
    )
    fltr = simics_result_filter(request.GET, queryset=queryset)
    table = simics_result_table(fltr.qs)
    RequestConfig(request, paginate={'per_page': 50}).configure(table)
    return render(
        request,
        'table.html',
        {
            'campaign_data': campaign_data_info,
            'simics_campaign_data': simics_campaign_data_info,
            'filter': fltr,
            'table': table,
            'title': title,
            'sidebar_items': sidebar_items
        }
    )


def injection_result(request, injection_number, title, sidebar_items):
    result = simics_result.objects.get(injection_id=injection_number)
    register_queryset = simics_register_diff.objects.filter(
        injection=injection_number)
    register_filter = simics_register_diff_filter(
        request.GET, queryset=register_queryset)
    register_table = simics_register_diff_table(register_filter.qs)
    memory_queryset = simics_memory_diff.objects.filter(
        injection=injection_number)
    memory_table = simics_memory_diff_table(memory_queryset)
    config = RequestConfig(request, paginate={'per_page': 50})
    config.configure(register_table)
    config.configure(memory_table)
    return render(
        request,
        'injection_result.html',
        {
            'result': result,
            'filter': register_filter,
            'register_table': register_table,
            'memory_table': memory_table,
            'title': title,
            'sidebar_items': sidebar_items
        }
    )
