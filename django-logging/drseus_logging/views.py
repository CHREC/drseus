from django.shortcuts import render
from django_tables2 import RequestConfig

from .charts import json_charts
from .filters import (hw_result_filter, hw_injection_filter,
                      simics_result_filter, simics_injection_filter,
                      simics_register_diff_filter)
from .models import (campaign, result, injection, simics_register_diff,
                     simics_memory_diff)
from .tables import (campaign_table, result_table, hw_injection_table,
                     simics_injection_table, simics_register_diff_table,
                     simics_memory_diff_table)


def charts_page(request, campaign_number):
    use_simics = campaign.objects.get(id=campaign_number).use_simics
    injection_objects = \
        injection.objects.filter(result__campaign__id=campaign_number)
    if use_simics:
        injection_filter = simics_injection_filter(request.GET,
                                                   queryset=injection_objects)
    else:
        injection_filter = hw_injection_filter(request.GET,
                                               queryset=injection_objects)
    chart_array = json_charts(injection_filter.qs, use_simics)
    return render(request, 'charts.html', {'chart_array': chart_array,
                                           'filter': injection_filter})


def campaign_page(request):
    table = campaign_table(campaign.objects.all())
    return render(request, 'campaign.html', {'campaign': None, 'table': table})


def results_page(request, campaign_number):
    use_simics = campaign.objects.get(id=campaign_number).use_simics
    result_objects = result.objects.filter(campaign__id=campaign_number)
    if use_simics:
        result_filter = simics_result_filter(request.GET,
                                             queryset=result_objects)
    else:
        result_filter = hw_result_filter(request.GET, queryset=result_objects)
    table = result_table(result_filter.qs)
    RequestConfig(request, paginate={'per_page': 100}).configure(table)
    return render(request, 'results.html', {'filter': result_filter,
                                            'table': table})


def result_page(request, campaign_number, iteration):
    use_simics = campaign.objects.get(id=campaign_number).use_simics
    result_object = result.objects.get(campaign__id=campaign_number,
                                       iteration=iteration)
    table = result_table(result.objects.filter(campaign__id=campaign_number,
                                               iteration=iteration))
    injection_objects = \
        injection.objects.filter(result__campaign__id=campaign_number,
                                 result__iteration=iteration)
    if use_simics:
        injection_table = simics_injection_table(injection_objects)
        register_objects = simics_register_diff.objects.filter(
            result__campaign__id=campaign_number, result__iteration=iteration)
        register_filter = \
            simics_register_diff_filter(request.GET, queryset=register_objects)
        register_table = simics_register_diff_table(register_filter.qs)
        memory_objects = simics_memory_diff.objects.filter(
            result__campaign__id=campaign_number, result__iteration=iteration)
        memory_table = simics_memory_diff_table(memory_objects)
        config = RequestConfig(request, paginate={'per_page': 50})
        config.configure(memory_table)
        config.configure(register_table)
        return render(request, 'simics_result.html',
                      {'campaign': campaign, 'filter': register_filter,
                       'injection_table': injection_table,
                       'memory_table': memory_table,
                       'register_table': register_table,
                       'result': result_object, 'table': table})
    else:
        injection_table = hw_injection_table(injection_objects)
        return render(request, 'hw_result.html',
                      {'campaign': campaign, 'injection_table': injection_table,
                       'result': result_object, 'table': table})
