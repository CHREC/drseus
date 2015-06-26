from django.shortcuts import render_to_response, render
from django.db.models import Sum, Count
from chartit import DataPool, Chart, PivotChart, PivotDataPool
from django_tables2 import RequestConfig
from .models import simics_result, simics_register_diff
from .tables import simics_result_table, simics_register_diff_table
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
                        'injection__register_index',
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
                    'text': 'Register Number'
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
    queryset = simics_result.objects.all().annotate(
        register_errors=Count('simics_register_diff'))
    fltr = simics_result_filter(request.GET, queryset=queryset)
    table = simics_result_table(fltr.qs)
    RequestConfig(request, paginate={'per_page': 50}).configure(table)
    return render(
        request,
        'table.html',
        {
            'filter': fltr,
            'table': table,
            'title': title,
            'sidebar_items': sidebar_items
        }
    )


def injection_result(request, injection_number, title, sidebar_items):
    result = simics_result.objects.get(injection_id=injection_number)
    queryset = simics_register_diff.objects.filter(
        injection=injection_number)
    fltr = simics_register_diff_filter(request.GET, queryset=queryset)
    table = simics_register_diff_table(fltr.qs)
    RequestConfig(request, paginate={'per_page': 50}).configure(table)
    return render(
        request,
        'injection_result.html',
        {
            'result': result,
            'filter': fltr,
            'table': table,
            'title': title,
            'sidebar_items': sidebar_items
        }
    )
