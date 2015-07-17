from django.shortcuts import render
from django_tables2 import RequestConfig

from .charts import json_charts
from .filters import (hw_result_filter, hw_injection_filter,
                      simics_result_filter, simics_injection_filter,
                      simics_register_diff_filter)
from .models import (campaign_data, result, injection, simics_register_diff,
                     simics_memory_diff)
from .tables import (campaign_data_table, result_table, hw_injection_table,
                     simics_injection_table, simics_register_diff_table,
                     simics_memory_diff_table)


def charts_page(request, title, sidebar_items):
    use_simics = campaign_data.objects.get().use_simics
    injection_objects = injection.objects.all()
    if use_simics:
        injection_filter = simics_injection_filter(request.GET,
                                                   queryset=injection_objects)
    else:
        injection_filter = hw_injection_filter(request.GET,
                                               queryset=injection_objects)
    chart_array = json_charts(injection_filter.qs, use_simics)
    return render(request, 'charts.html', {'chart_array': chart_array,
                                           'filter': injection_filter,
                                           'sidebar_items': sidebar_items,
                                           'title': title})


def campaign_page(request, title, sidebar_items):
    campaign = campaign_data.objects.get()
    table = campaign_data_table(campaign_data.objects.all())
    return render(request, 'campaign.html', {'campaign': campaign,
                                             'sidebar_items': sidebar_items,
                                             'table': table, 'title': title})


def results_page(request, title, sidebar_items):
    use_simics = campaign_data.objects.get().use_simics
    result_objects = result.objects.all()
    if use_simics:
        result_filter = simics_result_filter(request.GET,
                                             queryset=result_objects)
    else:
        result_filter = hw_result_filter(request.GET, queryset=result_objects)
    table = result_table(result_filter.qs)
    RequestConfig(request, paginate={'per_page': 100}).configure(table)
    return render(request, 'results.html', {'filter': result_filter,
                                            'sidebar_items': sidebar_items,
                                            'table': table, 'title': title})


def result_page(request, iteration, title, sidebar_items):
    campaign = campaign_data.objects.get()
    result_object = result.objects.get(iteration=iteration)
    table = result_table(result.objects.filter(iteration=iteration))
    injection_objects = injection.objects.filter(result_id=iteration)
    if campaign.use_simics:
        injection_table = simics_injection_table(injection_objects)
        register_objects = \
            simics_register_diff.objects.filter(result_id=iteration)
        register_filter = \
            simics_register_diff_filter(request.GET, queryset=register_objects)
        register_table = simics_register_diff_table(register_filter.qs)
        memory_objects = simics_memory_diff.objects.filter(result_id=iteration)
        memory_table = simics_memory_diff_table(memory_objects)
        config = RequestConfig(request, paginate={'per_page': 50})
        config.configure(memory_table)
        config.configure(register_table)
        return render(request, 'simics_result.html',
                      {'campaign': campaign, 'filter': register_filter,
                       'injection_table': injection_table,
                       'memory_table': memory_table,
                       'register_table': register_table,
                       'result': result_object, 'sidebar_items': sidebar_items,
                       'table': table, 'title': title})
    else:
        injection_table = hw_injection_table(injection_objects)
        return render(request, 'hw_result.html',
                      {'campaign': campaign, 'injection_table': injection_table,
                       'result': result_object, 'sidebar_items': sidebar_items,
                       'table': table, 'title': title})
