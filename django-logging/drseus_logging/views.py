import simplejson
from django.shortcuts import render
from django_tables2 import RequestConfig
from .models import (campaign_data, result, injection, simics_register_diff,
                     simics_memory_diff)
from .tables import (result_table, hw_injection_table, simics_injection_table,
                     simics_register_diff_table, simics_memory_diff_table)
from .charts import (outcome_category_chart, outcome_chart, register_chart,
                     bit_chart, time_chart)
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
    queryset = result.objects.all()
    if campaign_data_info.use_simics:
        fltr = simics_result_filter(request.GET, queryset=queryset)
    else:
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
    injections = injection.objects.filter(result_id=iteration)
    if campaign_data_info.use_simics:
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
    else:
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
    outcome_category_chart_click = """
    function(event) {
        var outcome_categories = __outcome_category_list__;
        window.location.assign('../table/?outcome_category='+
                               outcome_categories[this.x]);
    }
    """
    outcome_chart_click = """
    function(event) {
        var outcomes = __outcome_list__;
        window.location.assign('../table/?outcome='+outcomes[this.x]);
    }
    """
    register_chart_click = """
    function(event) {
        var reg = this.category.split(':');
        var register = reg[0];
        var index = reg[1];
        window.location.assign('../table/?outcome='+this.series.name+
                               '&injection__register='+register+
                               '&injection__register_index='+index);
    }
    """
    bit_chart_click = """
    function(event) {
        window.location.assign('../table/?outcome='+this.series.name+
                               '&injection__bit='+this.category);
    }
    """
    simics_time_chart_click = """
    function(event) {
        window.location.assign('../table/?outcome='+this.series.name+
                               '&injection__checkpoint_number='+this.category);
    }
    """
    hw_time_chart_click = """
    function(event) {
        var time = parseFloat(this.category)
        window.location.assign('../table/?outcome='+this.series.name+
                               '&injection__time_rounded='+time.toFixed(1));
    }
    """
    outcome_category_percentage_formatter = """
    function() {
        var outcome_categories = __outcome_category_list__;
        return ''+outcome_categories[parseInt(this.point.x)]+' '+
        Highcharts.numberFormat(this.percentage, 1)+'%';
    }
    """
    outcome_percentage_formatter = """
    function() {
        var outcomes = __outcome_list__;
        return ''+outcomes[parseInt(this.point.x)]+' '+
        Highcharts.numberFormat(this.percentage, 1)+'%';
    }
    """
    use_simics = campaign_data.objects.get().use_simics
    queryset = injection.objects.all()
    if use_simics:
        fltr = simics_injection_filter(request.GET, queryset=queryset)
    else:
        fltr = hw_injection_filter(request.GET, queryset=queryset)
    outcome_chart_, outcome_list = outcome_chart(fltr.qs)
    outcome_list = simplejson.dumps(outcome_list)
    outcome_category_chart_, outcome_category_list = \
        outcome_category_chart(fltr.qs)
    outcome_category_list = simplejson.dumps(outcome_category_list)
    chart_array = simplejson.dumps(
        [outcome_category_chart_, outcome_chart_, register_chart(fltr.qs),
         bit_chart(fltr.qs), time_chart(use_simics, fltr.qs)], indent=4
    ).replace(
        '\"outcome_category_chart_click\"',
        outcome_category_chart_click.replace('__outcome_category_list__',
                                             outcome_category_list)
    ).replace(
        '\"outcome_chart_click\"',
        outcome_chart_click.replace('__outcome_list__', outcome_list)
    ).replace(
        '\"register_chart_click\"', register_chart_click
    ).replace(
        '\"bit_chart_click\"', bit_chart_click
    ).replace(
        '\"time_chart_click\"',
        simics_time_chart_click if use_simics else hw_time_chart_click
    ).replace(
        '\"outcome_category_percentage_formatter\"',
        outcome_category_percentage_formatter.replace(
            '__outcome_category_list__', outcome_category_list)
    ).replace(
        '\"outcome_percentage_formatter\"',
        outcome_percentage_formatter.replace('__outcome_list__', outcome_list))
    return render(request, 'charts.html', {'filter': fltr, 'title': title,
                                           'chart_array': chart_array,
                                           'sidebar_items': sidebar_items})
