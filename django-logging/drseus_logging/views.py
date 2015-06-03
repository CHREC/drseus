from django.shortcuts import render_to_response
from django.db.models import Sum
from chartit import PivotChart, PivotDataPool
from .models import simics_results


def register_chart(request, title, sidebar_items):
    datasource = PivotDataPool(
        series=[
            {
                'options': {
                    'source': simics_results.objects.all(),
                    'categories': [
                        'register',
                        'register_index',
                    ],
                    'legend_by': 'outcome'
                },
                'terms': {
                    'injections': Sum('qty')
                }
            }
        ],
        sortf_mapf_mts=(lambda x: int(x[1]), None, False)
    )

    chart = PivotChart(
        datasource=datasource,
        series_options=[
            {
                'options': {
                    'type': 'column',
                    'stacking': True,
                    'xAxis': 0,
                    'yAxis': 0
                },
                'terms': ['injections']
            }
        ],
        chart_options={
            'chart': {
                'title': {
                    'text': 'Weather Chart'
                }
            },
            'xAxis': {
                'title': 'month'
            },
            'yAxis': {
                'title': 'temperature'
            }
        }
    )

    return render_to_response(
        'chart.html',
        {
            'chart_list': chart,
            'title': title,
            'sidebar_items': sidebar_items
        }
    )
