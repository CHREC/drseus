from django.shortcuts import render_to_response, render
from django.db.models import Sum
from chartit import PivotChart, PivotDataPool
from django_tables2 import RequestConfig
from .models import simics_results
from .tables import results_table
from .filters import results_filter


def register_chart(request, title, sidebar_items):
    queryset = simics_results.objects.all()
    fltr = results_filter(request.GET, queryset=queryset)
    datasource = PivotDataPool(
        series=[
            {
                'options': {
                    'source': fltr.qs,
                    'categories': [
                        'register_index',
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
    queryset = simics_results.objects.all()
    fltr = results_filter(request.GET, queryset=queryset)
    datasource = PivotDataPool(
        series=[
            {
                'options': {
                    'source': fltr.qs,
                    'categories': [
                        'bit',
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


def table(request, title, sidebar_items):
    queryset = simics_results.objects.all()
    fltr = results_filter(request.GET, queryset=queryset)
    table = results_table(fltr.qs)
    RequestConfig(request, paginate={'per_page': 30}).configure(table)
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
