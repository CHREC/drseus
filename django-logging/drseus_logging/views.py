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
    use_simics = campaign_data.objects.get().use_simics
    if use_simics:
        queryset = simics_injection.objects.all()
        fltr = simics_injection_filter(request.GET, queryset=queryset)
    else:
        queryset = hw_injection.objects.all()
        fltr = hw_injection_filter(request.GET, queryset=queryset)
    import simplejson
    chart_array = simplejson.dumps([outcome_chart(fltr.qs),
                                    register_chart(use_simics, fltr.qs),
                                    # register_chart(use_simics, fltr.qs),
                                    # bit_chart(fltr.qs),
                                    # time_chart(use_simics, fltr.qs)])
                                    ], indent=4)
    return render_to_response('charts.html', {'filter': fltr, 'title': title,
                                              'chart_array': chart_array,
                                              'sidebar_items': sidebar_items})


# chart_array = '[{"series": [{"data": [["DUT hanging", 11], ["Kernel panic", 2], ["Missing output", 2], ["No error", 131], ["Segmentation fault", 12], ["Signal SIGIOT", 2], ["Signal SIGSEGV", 9], ["Silent data error", 31]], "type": "pie", "showInLegend": true, "name": "Bit"}], "yAxis": [{"title": {"text": "Bit"}}], "chart": {"renderTo": "outcome_chart"}, "xAxis": [{"title": {"text": "Outcome"}}], "title": {"text": "Outcomes"}}, {"series": [{"stacking": true, "type": "column", "data": [0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], "name": "Kernel panic"}, {"stacking": true, "type": "column", "data": [12, 8, 3, 11, 8, 7, 6, 7, 4, 4, 9, 11, 11, 4, 10, 10, 16, 9, 14, 8, 10, 4, 3, 9, 9, 5, 7, 7, 10, 12, 9, 5], "name": "No error"}, {"stacking": true, "type": "column", "data": [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1], "name": "Missing output"}, {"stacking": true, "type": "column", "data": [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0], "name": "Signal SIGIOT"}, {"stacking": true, "type": "column", "data": [0, 3, 2, 0, 1, 0, 0, 2, 0, 0, 2, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 1, 0, 1, 0, 2], "name": "Signal SIGSEGV"}, {"stacking": true, "type": "column", "data": [1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 4, 0, 0, 0, 1, 2, 0, 0, 1, 0, 1, 1, 0, 0, 5, 0, 0, 0, 1, 0, 0, 0], "name": "DUT hanging"}, {"stacking": true, "type": "column", "data": [1, 3, 7, 7, 1, 1, 2, 2, 4, 3, 0, 2, 3, 2, 0, 0, 1, 5, 3, 2, 1, 0, 0, 1, 0, 0, 5, 1, 2, 2, 1, 0], "name": "Silent data error"}, {"stacking": true, "type": "column", "data": [1, 0, 0, 0, 0, 0, 5, 0, 2, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 7, 1, 0, 0, 0, 1, 0, 0, 1, 0], "name": "Segmentation fault"}], "yAxis": {"title": {"text": "Number of Injections"}}, "chart": {"renderTo": "register_chart"}, "xAxis": {"labels": {"y": 10, "x": 5, "align": "right", "rotation": "-60"}, "categories": ["gprs:030", "gprs:005", "gprs:008", "gprs:007", "gprs:019", "gprs:016", "gprs:001", "gprs:012", "gprs:010", "gprs:025", "gprs:020", "gprs:017", "gprs:026", "gprs:023", "gprs:011", "gprs:021", "gprs:006", "gprs:009", "gprs:022", "gprs:024", "gprs:000", "gprs:018", "gprs:002", "gprs:027", "gprs:003", "gprs:014", "gprs:004", "gprs:029", "gprs:028", "gprs:013", "gprs:031", "gprs:015"], "title": {"text": "Registers"}}, "title": {"text": "Injections By Register"}}, {"series": [{"stacking": true, "type": "column", "data": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "name": "Kernel panic"}, {"stacking": true, "type": "column", "data": [3, 2, 3, 7, 7, 3, 4, 3, 3, 2, 6, 3, 1, 1, 3, 4, 4, 5, 5, 1, 2, 2, 0, 4, 4, 2, 3, 1, 2, 5, 2, 3, 2, 8, 5, 4, 9, 2, 4, 7, 4, 8, 7, 1, 7, 6, 5, 8, 5, 7, 7, 2, 6, 10, 2, 7, 7, 3, 8, 3, 0, 3, 5], "name": "No error"}, {"stacking": true, "type": "column", "data": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0], "name": "Missing output"}, {"stacking": true, "type": "column", "data": [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0], "name": "Signal SIGIOT"}, {"stacking": true, "type": "column", "data": [0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 2, 0, 1, 0, 1, 0, 0, 2, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0], "name": "Signal SIGSEGV"}, {"stacking": true, "type": "column", "data": [1, 1, 1, 0, 0, 0, 1, 2, 1, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0], "name": "Segmentation fault"}, {"stacking": true, "type": "column", "data": [2, 3, 0, 1, 4, 0, 2, 2, 0, 1, 2, 1, 3, 1, 0, 0, 4, 4, 1, 2, 0, 0, 3, 1, 0, 1, 0, 1, 0, 2, 2, 2, 0, 0, 0, 0, 1, 0, 2, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 3, 1, 0, 0, 1, 1], "name": "Silent data error"}, {"stacking": true, "type": "column", "data": [0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 0, 2, 1, 0, 0, 1, 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 2, 0], "name": "DUT hanging"}], "yAxis": {"title": {"text": "Number of Injections"}}, "chart": {"renderTo": "bit_chart"}, "xAxis": {"categories": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63"], "title": {"text": "Bits"}}, "title": {"text": "Injections By Bit"}}, {"series": [{"stacking": "normal", "type": "area", "data": [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "name": "Kernel panic"}, {"stacking": "normal", "type": "area", "data": [10, 5, 4, 3, 4, 6, 5, 5, 7, 7, 3, 2, 3, 3, 7, 3, 5, 10, 5, 3, 9, 4, 5, 2, 5, 5, 8, 6, 3, 6, 4, 5, 5, 10, 4, 1, 9, 4, 5, 10, 3, 8, 5, 4, 4, 9, 7, 6, 6], "name": "No error"}, {"stacking": "normal", "type": "area", "data": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0], "name": "Missing output"}, {"stacking": "normal", "type": "area", "data": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0], "name": "Signal SIGIOT"}, {"stacking": "normal", "type": "area", "data": [1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 2, 3, 1], "name": "Signal SIGSEGV"}, {"stacking": "normal", "type": "area", "data": [0, 1, 2, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 2, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 2, 1, 1, 0, 0, 0, 0], "name": "DUT hanging"}, {"stacking": "normal", "type": "area", "data": [0, 1, 1, 1, 2, 2, 1, 2, 2, 0, 2, 0, 0, 3, 1, 0, 1, 2, 1, 1, 2, 2, 0, 1, 1, 0, 1, 1, 2, 1, 1, 4, 2, 3, 0, 1, 0, 0, 2, 2, 2, 2, 1, 0, 1, 0, 4, 1, 2], "name": "Silent data error"}, {"stacking": "normal", "type": "area", "data": [0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 0, 2, 0, 0, 0, 0, 0, 0, 1, 0, 2, 1, 0, 1, 0, 0, 0, 2, 0, 2, 3], "name": "Segmentation fault"}], "yAxis": {"title": {"text": "Number of Injections"}}, "chart": {"renderTo": "time_chart"}, "xAxis": {"categories": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48"], "title": {"text": "Checkpoints"}}, "title": {"text": "Injections Over Time"}}];'
