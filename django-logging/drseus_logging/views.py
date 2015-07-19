from django.shortcuts import render
from django_tables2 import RequestConfig

from .charts import json_charts
from .filters import (hw_result_filter, hw_injection_filter,
                      simics_result_filter, simics_injection_filter,
                      simics_register_diff_filter)
from .models import (campaign, result, injection, simics_register_diff,
                     simics_memory_diff)
from .tables import (campaign_table, result_table, results_table,
                     hw_injection_table, simics_injection_table,
                     simics_register_diff_table, simics_memory_diff_table)

navigation_items = (('Campaign Information', '../campaign'),
                    ('Injection Charts', '../charts/'),
                    ('Results Table', '../results/'))


def charts_page(request, campaign_number):
    page_items = (('Outcomes', 'outcomes'),
                  ('Outcomes By Register', 'registers'),
                  ('Outcomes By Bit', 'bits'),
                  ('Outcomes Over Time', 'times'))
    campaign_data = campaign.objects.get(campaign_number=campaign_number)
    injection_objects = injection.objects.filter(
        result__campaign__campaign_number=campaign_number)
    if campaign_data.use_simics:
        injection_filter = simics_injection_filter(request.GET,
                                                   queryset=injection_objects)
    else:
        injection_filter = hw_injection_filter(request.GET,
                                               queryset=injection_objects)
    chart_array = json_charts(injection_filter.qs, campaign_data)
    return render(request, 'charts.html', {'campaign_data': campaign_data,
                                           'chart_array': chart_array,
                                           'filter': injection_filter,
                                           'navigation_items':
                                               navigation_items,
                                           'page_items': page_items})


def campaign_page(request, campaign_number):
    campaign_data = campaign.objects.get(campaign_number=campaign_number)
    page_items = [('Campaign Data', 'campaign_data'),
                  ('DUT Output', 'dut_output')]
    if campaign_data.use_aux:
        page_items.append(('AUX Output', 'aux_output'))
    page_items.extend([('Debugger Output', 'debugger_output'),
                       ('SCP Log', 'paramiko_output')])
    if campaign_data.use_aux:
        page_items.append(('AUX SCP Log', 'aux_paramiko_output'))
    table = campaign_table(campaign.objects.filter(
        campaign_number=campaign_number))
    return render(request, 'campaign.html', {'campaign_data': campaign_data,
                                             'navigation_items':
                                                 navigation_items,
                                             'page_items': page_items,
                                             'table': table})


def campaigns_page(request):
    table = campaign_table(campaign.objects.all())
    return render(request, 'campaigns.html', {'table': table})


def results_page(request, campaign_number):
    campaign_data = campaign.objects.get(campaign_number=campaign_number)
    page_items = [('Result', 'result'), ('Injections', 'injections'),
                  ('DUT Output', 'dut_output')]
    if campaign_data.use_aux:
        page_items.append(('AUX Output', 'aux_output'))
    page_items.extend([('Debugger Output', 'debugger_output'),
                       ('SCP Log', 'paramiko_output')])
    if campaign_data.use_aux:
        page_items.append(('AUX SCP Log', 'aux_paramiko_output'))
    result_objects = result.objects.filter(
        campaign__campaign_number=campaign_number)
    if campaign_data.use_simics:
        result_filter = simics_result_filter(request.GET,
                                             queryset=result_objects)
    else:
        result_filter = hw_result_filter(request.GET, queryset=result_objects)
    table = results_table(result_filter.qs)
    RequestConfig(request, paginate={'per_page': 100}).configure(table)
    return render(request, 'results.html', {'campaign_data': campaign_data,
                                            'filter': result_filter,
                                            'navigation_items':
                                                navigation_items,
                                            'page_items': page_items,
                                            'table': table})


def result_page(request, campaign_number, iteration):
    campaign_data = campaign.objects.get(campaign_number=campaign_number)
    navigation_items = (('Campaign Information', '../../campaign'),
                        ('Injection Charts', '../../charts/'),
                        ('Results Table', '../../results/'))
    page_items = [('Result', 'result'), ('Injections', 'injections'),
                  ('DUT Output', 'dut_output')]
    if campaign_data.use_aux:
        page_items.append(('AUX Output', 'aux_output'))
    page_items.extend([('Debugger Output', 'debugger_output'),
                       ('SCP Log', 'paramiko_output')])
    if campaign_data.use_aux:
        page_items.append(('AUX SCP Log', 'aux_paramiko_output'))
    if campaign_data.use_simics:
        page_items.extend([('Register Diffs', 'register_diffs'),
                           ('Memory Diffs', 'memory_diffs')])
    result_object = result.objects.get(
        campaign__campaign_number=campaign_number, iteration=iteration)
    table = result_table(result.objects.filter(
        campaign__campaign_number=campaign_number, iteration=iteration))
    injection_objects = \
        injection.objects.filter(
            result__campaign__campaign_number=campaign_number,
            result__iteration=iteration)
    if campaign_data.use_simics:
        injection_table = simics_injection_table(injection_objects)
        register_objects = simics_register_diff.objects.filter(
            result__campaign__campaign_number=campaign_number,
            result__iteration=iteration)
        register_filter = \
            simics_register_diff_filter(request.GET, queryset=register_objects)
        register_table = simics_register_diff_table(register_filter.qs)
        memory_objects = simics_memory_diff.objects.filter(
            result__campaign__campaign_number=campaign_number,
            result__iteration=iteration)
        memory_table = simics_memory_diff_table(memory_objects)
        config = RequestConfig(request, paginate={'per_page': 50})
        config.configure(memory_table)
        config.configure(register_table)
    else:
        register_filter = None
        memory_table = None
        register_table = None
        injection_table = hw_injection_table(injection_objects)
    return render(request, 'result.html', {'campaign_data': campaign_data,
                                           'filter': register_filter,
                                           'injection_table': injection_table,
                                           'memory_table': memory_table,
                                           'navigation_items': navigation_items,
                                           'page_items': page_items,
                                           'register_table': register_table,
                                           'result': result_object,
                                           'table': table})
