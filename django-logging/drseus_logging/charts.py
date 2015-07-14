import re
from django.db.models import Count
from chartit import DataPool, Chart, PivotChart, PivotDataPool


def fix_sort(string):
    return ''.join([text.zfill(5) if text.isdigit() else text.lower() for
                    text in re.split('([0-9]+)', str(string[0]))])


def outcome_chart(queryset):
    # using bit in annotate since it is a valid field for both injection models
    # otherwise chartit will fail model validation (used in terms)
    queryset = queryset.values('result__outcome').annotate(
        bit=Count('result__outcome'))
    datasource = DataPool(series=[{'options': {'source': queryset},
                                   'terms': ['result__outcome', 'bit']}])
    chart = Chart(datasource=datasource,
                  series_options=[{'options': {'type': 'pie',
                                               'showInLegend': True},
                                   'terms': {'result__outcome': ['bit']}}],
                  chart_options={'title': {'text': 'Outcomes'}})
    return chart


def register_chart(campaign_data_info, queryset):
    if campaign_data_info.use_simics:
        datasource = PivotDataPool(
            series=[{
                'options': {
                    'source': queryset,
                    'categories': ['register',
                                   'register_index'],
                    'legend_by': 'result__outcome'
                },
                'terms': {'injections': Count('result__outcome')}
            }],
            sortf_mapf_mts=(fix_sort, None, False))
    else:
        datasource = PivotDataPool(
            series=[{
                'options': {
                    'source': queryset,
                    'categories': ['register'],
                    'legend_by': 'result__outcome'
                },
                'terms': {'injections': Count('result__outcome')}
            }],
            sortf_mapf_mts=(fix_sort, None, False))
    chart = PivotChart(datasource=datasource,
                       series_options=[{'options': {'type': 'column',
                                                    'stacking': True},
                                        'terms': ['injections']}],
                       chart_options={
                           'title': {'text': 'Injections By Register'},
                           'xAxis': {'title': {'text': 'Registers'},
                                     'labels': {'align': 'right', 'x': 5,
                                                'y': 10, 'rotation': '-60'}},
                           'yAxis': {'title': {
                               'text': 'Number of Injections'}}})
    return chart


def bit_chart(queryset):
    datasource = PivotDataPool(series=[{'options': {'source': queryset,
                                                    'categories': ['bit'],
                                                    'legend_by':
                                                        'result__outcome'},
                                        'terms': {'injections':
                                                  Count('result__outcome')}}],
                               sortf_mapf_mts=(fix_sort, None, False))
    chart = PivotChart(datasource=datasource,
                       series_options=[{'options': {'type': 'column',
                                                    'stacking': True},
                                        'terms': ['injections']}],
                       chart_options={'title': {'text': 'Injections By Bit'},
                                      'xAxis': {'title': {'text': 'Bits'}},
                                      'yAxis': {'title': {
                                          'text': 'Number of Injections'}}})
    return chart


def time_chart(campaign_data_info, queryset):
    if campaign_data_info.use_simics:
        datasource = PivotDataPool(
            series=[{
                'options': {'source': queryset,
                            'categories': ['checkpoint_number'],
                            'legend_by': 'result__outcome'},
                'terms': {'injections': Count('result__outcome')}}],
            sortf_mapf_mts=(fix_sort, None, False))
        chart = PivotChart(datasource=datasource,
                           series_options=[{'options': {'type': 'area',
                                                        'stacking': 'normal'},
                                            'terms': ['injections']}],
                           chart_options={
                               'title': {'text': 'Injections Over Time'},
                               'xAxis': {'title': {'text': 'Checkpoints'}},
                               'yAxis': {'title': {
                                   'text': 'Number of Injections'}}})
    else:
        datasource = PivotDataPool(
            series=[{
                'options': {'source': queryset,
                            'categories': ['time_rounded'],
                            'legend_by': 'result__outcome'},
                'terms': {'injections': Count('result__outcome')}}])
        chart = PivotChart(datasource=datasource,
                           series_options=[{'options': {'type': 'area',
                                                        'stacking': 'normal'},
                                            'terms': ['injections']}],
                           chart_options={
                               'title': {'text': 'Injections Over Time'},
                               'xAxis': {'title': {'text': 'Seconds'}},
                               'yAxis': {'title': {
                                   'text': 'Number of Injections'}}})
    return chart
