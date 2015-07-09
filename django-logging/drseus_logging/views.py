import re
from django.shortcuts import render_to_response, render
from django.db.models import Sum, Count
from chartit import DataPool, Chart, PivotChart, PivotDataPool
from django_tables2 import RequestConfig
from .models import (campaign_data, hw_result, simics_result,
                     simics_register_diff, simics_memory_diff,
                     supervisor_result)
from .tables import (hw_result_table, simics_result_table,
                     simics_register_diff_table, simics_memory_diff_table,
                     supervisor_result_table)
from .filters import (hw_result_filter, simics_result_filter,
                      simics_register_diff_filter)


def fix_sort(string):
    return ''.join([text.zfill(5) if text.isdigit() else text.lower() for
                    text in re.split('([0-9]+)', str(string[0]))])


def result_table(request, title, sidebar_items):
    campaign_data_info = campaign_data.objects.get()
    if campaign_data_info.use_simics:
        queryset = simics_result.objects.all().annotate(
            register_errors=Count('simics_register_diff'),
            memory_errors=Count('simics_memory_diff')
        )
        fltr = simics_result_filter(request.GET, queryset=queryset)
        table = simics_result_table(fltr.qs)
        injections = simics_result.objects.count()
    else:
        queryset = hw_result.objects.all()
        fltr = hw_result_filter(request.GET, queryset=queryset)
        table = hw_result_table(fltr.qs)
        injections = hw_result.objects.count() > 0
    supervisor_qs = supervisor_result.objects.all()
    supervisor_table = supervisor_result_table(supervisor_qs)
    iterations = supervisor_result.objects.count() > 0

    RequestConfig(request, paginate={'per_page': 50}).configure(table)
    return render(request, 'table.html',
                  {'campaign_data': campaign_data_info, 'filter': fltr,
                   'table': table, 'injections': injections,
                   'supervisor_table': supervisor_table,
                   'iterations': iterations, 'title': title,
                   'sidebar_items': sidebar_items})


def injection_result(request, injection_number, title, sidebar_items):
    campaign_data_info = campaign_data.objects.get()
    if campaign_data_info.use_simics:
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
        return render(request, 'simics_injection_result.html',
                      {'result': result, 'filter': register_filter,
                       'register_table': register_table,
                       'memory_table': memory_table, 'title': title,
                       'sidebar_items': sidebar_items})
    else:
        result = hw_result.objects.get(injection_id=injection_number)
        # RequestConfig(request)
        return render(request, 'hw_injection_result.html',
                      {'result': result, 'title': title,
                       'sidebar_items': sidebar_items})


def iteration_result(request, iteration, title, sidebar_items):
    campaign_data_info = campaign_data.objects.get()
    result = supervisor_result.objects.get(iteration=iteration)
    return render(request, 'iteration_result.html',
                  {'result': result, 'campaign_data': campaign_data_info,
                   'title': title, 'sidebar_items': sidebar_items})


def register_chart(request, title, sidebar_items):
    campaign_data_info = campaign_data.objects.get()
    if campaign_data_info.use_simics:
        queryset = simics_result.objects.all()
        fltr = simics_result_filter(request.GET, queryset=queryset)
        datasource = PivotDataPool(
            series=[{
                'options': {
                    'source': fltr.qs,
                    'categories': ['injection__register',
                                   'injection__register_index'],
                    'legend_by': 'outcome'
                },
                'terms': {'injections': Sum('qty')}
            }],
            sortf_mapf_mts=(fix_sort, None, False))
    else:
        queryset = hw_result.objects.all()
        fltr = hw_result_filter(request.GET, queryset=queryset)
        datasource = PivotDataPool(
            series=[{
                'options': {
                    'source': fltr.qs,
                    'categories': ['injection__register'],
                    'legend_by': 'outcome'
                },
                'terms': {'injections': Sum('qty')}
            }],
            sortf_mapf_mts=(fix_sort, None, False))
    chart = PivotChart(datasource=datasource,
                       series_options=[{'options': {'type': 'column',
                                                    'stacking': True},
                                        'terms': ['injections']}],
                       chart_options={'title': {'text': ''},
                                      'xAxis': {'title': {'text': 'Registers'},
                                                'labels': {'align': 'right',
                                                           'x': 5, 'y': 10,
                                                           'rotation': '-60'}},
                                      'yAxis': {'title': {
                                          'text': 'Number of Injections'}}})
    return render_to_response('chart.html', {'filter': fltr,
                                             'chart_list': chart,
                                             'title': title,
                                             'sidebar_items': sidebar_items})


def bit_chart(request, title, sidebar_items):
    campaign_data_info = campaign_data.objects.get()
    if campaign_data_info.use_simics:
        queryset = simics_result.objects.all()
        fltr = simics_result_filter(request.GET, queryset=queryset)
    else:
        queryset = hw_result.objects.all()
        fltr = hw_result_filter(request.GET, queryset=queryset)
    datasource = PivotDataPool(series=[{'options': {'source': fltr.qs,
                                                    'categories': [
                                                        'injection__bit'],
                                                    'legend_by': 'outcome'},
                                        'terms': {'injections': Sum('qty')}}],
                               sortf_mapf_mts=(fix_sort, None, False))
    chart = PivotChart(datasource=datasource,
                       series_options=[{'options': {'type': 'column',
                                                    'stacking': True},
                                        'terms': ['injections']}],
                       chart_options={'title': {'text': ''},
                                      'xAxis': {'title': {'text': 'Bits'}},
                                      'yAxis': {'title': {
                                          'text': 'Number of Injections'}}})
    return render_to_response('chart.html', {'filter': fltr,
                                             'chart_list': chart,
                                             'title': title,
                                             'sidebar_items': sidebar_items})


def time_chart(request, title, sidebar_items):
    campaign_data_info = campaign_data.objects.get()
    if campaign_data_info.use_simics:
        queryset = simics_result.objects.all()
        fltr = simics_result_filter(request.GET, queryset=queryset)
        datasource = PivotDataPool(
            series=[{
                'options': {'source': fltr.qs,
                            'categories': ['injection__checkpoint_number'],
                            'legend_by': 'outcome'},
                'terms': {'injections': Sum('qty')}}])
        chart = PivotChart(datasource=datasource,
                           series_options=[{'options': {'type': 'column',
                                                        'stacking': True},
                                            'terms': ['injections']}],
                           chart_options={'title': {'text': ''},
                                          'xAxis': {'title': {
                                              'text': 'Checkpoints'}},
                                          'yAxis': {'title': {
                                              'text': 'Number of Injections'}}})
    else:
        queryset = hw_result.objects.all()
        fltr = hw_result_filter(request.GET, queryset=queryset)
        datasource = PivotDataPool(
            series=[{
                'options': {'source': fltr.qs,
                            'categories': ['injection__time_rounded'],
                            'legend_by': 'outcome'},
                'terms': {'injections': Sum('qty')}}])
        chart = PivotChart(datasource=datasource,
                           series_options=[{'options': {'type': 'column',
                                                        'stacking': True},
                                            'terms': ['injections']}],
                           chart_options={'title': {'text': ''},
                                          'xAxis': {'title': {
                                              'text': 'Seconds'}},
                                          'yAxis': {'title': {
                                              'text': 'Number of Injections'}}})
    return render_to_response('chart.html', {'filter': fltr,
                                             'chart_list': chart,
                                             'title': title,
                                             'sidebar_items': sidebar_items})


def outcome_chart(request, title, sidebar_items):
    campaign_data_info = campaign_data.objects.get()
    if campaign_data_info.use_simics:
        queryset = simics_result.objects.values('outcome').\
            annotate(qty=Count('outcome'))
        fltr = simics_result_filter(request.GET, queryset=queryset)
    else:
        queryset = hw_result.objects.values('outcome').\
            annotate(qty=Count('outcome'))
        fltr = hw_result_filter(request.GET, queryset=queryset)
    datasource = DataPool(series=[{'options': {'source': fltr.qs},
                                   'terms': ['outcome', 'qty']}])
    chart = Chart(datasource=datasource,
                  series_options=[{'options': {'type': 'pie'},
                                   'terms': {'outcome': ['qty']}}],
                  chart_options={'title': {'text': ' '}})
    return render_to_response('chart.html', {'filter': fltr,
                                             'chart_list': chart,
                                             'title': title,
                                             'sidebar_items': sidebar_items})
