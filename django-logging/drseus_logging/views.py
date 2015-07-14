from django.shortcuts import render_to_response, render
from django.db.models import Count
from django_tables2 import RequestConfig
from .models import (campaign_data, result, hw_injection, simics_injection,
                     simics_register_diff, simics_memory_diff)
from .tables import (result_table, hw_injection_table, simics_injection_table,
                     simics_register_diff_table, simics_memory_diff_table)
from .charts import (outcome_chart, register_chart, bit_chart, time_chart)
from .filters import (hw_result_filter, hw_injection_filter,
                      simics_result_filter, simics_injection_filter,
                      simics_register_diff_filter)

# from django.db.models.query import QuerySet
# from pprint import PrettyPrinter


# def dprint(object, stream=None, indent=1, width=80, depth=None):
#     """
#     A small addition to pprint that converts any Django model objects to
#     dictionaries so they print prettier.

#     h3. Example usage

#         >>> from toolbox.dprint import dprint
#         >>> from app.models import Dummy
#         >>> dprint(Dummy.objects.all().latest())
#          {'first_name': u'Ben',
#           'last_name': u'Welsh',
#           'city': u'Los Angeles',
#           'slug': u'ben-welsh',
#     """
#     # Catch any singleton Django model object that might get passed in
#     if getattr(object, '__metaclass__', None):
#         if object.__metaclass__.__name__ == 'ModelBase':
#             # Convert it to a dictionary
#             object = object.__dict__

#     # Catch any Django QuerySets that might get passed in
#     elif isinstance(object, QuerySet):
#         # Convert it to a list of dictionaries
#         object = [i.__dict__ for i in object]

#     # Pass everything through pprint in the typical way
#     printer = PrettyPrinter(stream=stream, indent=indent, width=width,
#                             depth=depth)
#     printer.pprint(object)


def table_page(request, title, sidebar_items):
    campaign_data_info = campaign_data.objects.get()
    if campaign_data_info.use_simics:
        queryset = result.objects.all().annotate(
            injections=Count('simics_injection'))
        fltr = simics_result_filter(request.GET, queryset=queryset)
    else:
        queryset = result.objects.all().annotate(
            injections=Count('hw_injection'))
        fltr = hw_result_filter(request.GET, queryset=queryset)
    table = result_table(fltr.qs)
    RequestConfig(request, paginate={'per_page': 100}).configure(table)
    return render(request, 'table.html',
                  {'campaign_data': campaign_data_info, 'filter': fltr,
                   'table': table, 'title': title,
                   'sidebar_items': sidebar_items})


def result_page(request, iteration, title, sidebar_items):
    campaign_data_info = campaign_data.objects.get()
    results = result.objects.get(iteration=iteration)
    table = result_table(result.objects.filter(iteration=iteration))
    if campaign_data_info.use_simics:
        injections = simics_injection.objects.filter(result_id=iteration)
        injection_table = simics_injection_table(injections)
        register_queryset = simics_register_diff.objects.filter(
            result_id=iteration)
        register_filter = simics_register_diff_filter(
            request.GET, queryset=register_queryset)
        register_table = simics_register_diff_table(register_filter.qs)
        memory_queryset = simics_memory_diff.objects.filter(
            result_id=iteration)
        memory_table = simics_memory_diff_table(memory_queryset)
        config = RequestConfig(request, paginate={'per_page': 50})
        config.configure(injection_table)
        config.configure(register_table)
        config.configure(memory_table)
        return render(request, 'simics_injection.html',
                      {'campaign_data': campaign_data_info,
                       'result_table': table, 'result': results,
                       'filter': register_filter,
                       'injection_table': injection_table,
                       'register_table': register_table,
                       'memory_table': memory_table, 'title': title,
                       'sidebar_items': sidebar_items})
    # elif supervised:
    #     return render(request, 'supervisor.html',
    #                   {'result': results, 'campaign_data': campaign_data_info,
    #                    'title': title, 'sidebar_items': sidebar_items})
    else:
        injections = hw_injection.objects.filter(result_id=iteration)
        injection_table = hw_injection_table(injections)
        config = RequestConfig(request, paginate={'per_page': 50})
        config.configure(injection_table)
        return render(request, 'hw_injection.html',
                      {'campaign_data': campaign_data_info,
                       'result_table': table, 'result': results,
                       'injection_table': injection_table, 'title': title,
                       'sidebar_items': sidebar_items})


def campaign_info_page(request, title, sidebar_items):
    campaign_data_info = campaign_data.objects.get()
    return render(
        request, 'campaign.html', {'campaign_data': campaign_data_info,
                                   'title': title,
                                   'sidebar_items': sidebar_items})


def charts_page(request, title, sidebar_items):
    campaign_data_info = campaign_data.objects.get()
    if campaign_data_info.use_simics:
        queryset = simics_injection.objects.order_by('result__outcome')
        fltr = simics_injection_filter(request.GET, queryset=queryset)
    else:
        queryset = hw_injection.objects.order_by('result__outcome')
        fltr = hw_injection_filter(request.GET, queryset=queryset)
    chart_list = (outcome_chart(fltr.qs.filter(injection_number=0)),
                  register_chart(campaign_data_info, fltr.qs),
                  bit_chart(fltr.qs),
                  time_chart(campaign_data_info, fltr.qs))
    return render_to_response('charts.html', {'filter': fltr,
                                              'chart_list': chart_list,
                                              'title': title,
                                              'sidebar_items': sidebar_items})
