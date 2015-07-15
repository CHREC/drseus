import re
from django.db.models import Count


def fix_sort(string):
    return ''.join([text.zfill(5) if text.isdigit() else text.lower() for
                    text in re.split('([0-9]+)', str(string))])


def outcome_chart(queryset):
    # outcome_categories = list(queryset.filter(injection_number=0).values_list(
    #     'result__outcome_category').annotate(
    #     count=Count('result__outcome_category')))
    outcomes = list(queryset.filter(injection_number=0).order_by(
        'result__outcome').values_list('result__outcome').annotate(
        outcome_count=Count('result__outcome')))
    chart = {'chart': {'renderTo': 'outcome_chart', 'type': 'pie'},
             'title': {'text': 'Outcomes'},
             'plotOptions': {'pie': {
                 'dataLabels': {'style': {'textShadow': False}}}},
             'series': [{'name': 'Outcomes', 'size': '80%', 'data': outcomes,
                         'dataLabels': {'format': '{point.name} {point.y}'}},
                        # {'name': 'Categories', 'size': '60%',
                        #  'data': outcome_categories,
                        #  'dataLabels': {'distance': -30}},
                        ]}
    return chart


def register_chart(use_simics, queryset):
    registers = sorted(queryset.values_list('register').distinct(),
                       key=fix_sort)
    registers = zip(*registers)[0]
    print(registers)
    outcomes = list(queryset.values_list('result__outcome').distinct().order_by(
        'result__outcome'))
    outcomes = zip(*outcomes)[0]
    print(outcomes)
    chart = {'chart': {'renderTo': 'register_chart', 'type': 'column'},
             'title': {'text': 'Registers'},
             'plotOptions': {'column': {
                 'dataLabels': {'style': {'textShadow': False}}}},
             'xAxis': {'labels': {'x': 5, 'y': 10, 'align': 'right',
                                  'rotation': -60},
                       'categories': registers},
             'yAxis': {'title': {'text': 'Injections'}}}
    chart['series'] = []
    for outcome in outcomes:
        data = []
        for register in registers:
            data.append(queryset.filter(result__outcome=outcome,
                                        register=register).count())
        chart['series'].append({
            'data': data, 'name': outcome, 'stacking': True
        })
    return chart
#     if campaign_data_info.use_simics:
#         datasource = PivotDataPool(
#             series=[{
#                 'options': {
#                     'source': queryset,
#                     'categories': ['register',
#                                    'register_index'],
#                     'legend_by': 'result__outcome'
#                 },
#                 'terms': {'injections': Count('result__outcome')}
#             }],
#             sortf_mapf_mts=(fix_sort, None, False))
#     else:
#         datasource = PivotDataPool(
#             series=[{
#                 'options': {
#                     'source': queryset,
#                     'categories': ['register'],
#                     'legend_by': 'result__outcome'
#                 },
#                 'terms': {'injections': Count('result__outcome')}
#             }],
#             sortf_mapf_mts=(fix_sort, None, False))
#     chart = PivotChart(datasource=datasource,
#                        series_options=[{'options': {'type': 'column',
#                                                     'stacking': True},
#                                         'terms': ['injections']}],
#                        chart_options={
#                            'title': {'text': 'Injections By Register'},
#                            'xAxis': {'title': {'text': 'Registers'},
#                                      'labels': {'align': 'right', 'x': 5,
#                                                 'y': 10, 'rotation': '-60'}},
#                            'yAxis': {'title': {
#                                'text': 'Number of Injections'}}})
#     return chart


def bit_chart(queryset):
    pass
#     datasource = PivotDataPool(series=[{'options': {'source': queryset,
#                                                     'categories': ['bit'],
#                                                     'legend_by':
#                                                         'result__outcome'},
#                                         'terms': {'injections':
#                                                   Count('result__outcome')}}],
#                                sortf_mapf_mts=(fix_sort, None, False))
#     chart = PivotChart(datasource=datasource,
#                        series_options=[{'options': {'type': 'column',
#                                                     'stacking': True},
#                                         'terms': ['injections']}],
#                        chart_options={'title': {'text': 'Injections By Bit'},
#                                       'xAxis': {'title': {'text': 'Bits'}},
#                                       'yAxis': {'title': {
#                                           'text': 'Number of Injections'}}})
#     return chart


def time_chart(campaign_data_info, queryset):
    pass
#     if campaign_data_info.use_simics:
#         datasource = PivotDataPool(
#             series=[{
#                 'options': {'source': queryset,
#                             'categories': ['checkpoint_number'],
#                             'legend_by': 'result__outcome'},
#                 'terms': {'injections': Count('result__outcome')}}],
#             sortf_mapf_mts=(fix_sort, None, False))
#         chart = PivotChart(datasource=datasource,
#                            series_options=[{'options': {'type': 'area',
#                                                         'stacking': 'normal'},
#                                             'terms': ['injections']}],
#                            chart_options={
#                                'title': {'text': 'Injections Over Time'},
#                                'xAxis': {'title': {'text': 'Checkpoints'}},
#                                'yAxis': {'title': {
#                                    'text': 'Number of Injections'}}})
#     else:
#         datasource = PivotDataPool(
#             series=[{
#                 'options': {'source': queryset,
#                             'categories': ['time_rounded'],
#                             'legend_by': 'result__outcome'},
#                 'terms': {'injections': Count('result__outcome')}}])
#         chart = PivotChart(datasource=datasource,
#                            series_options=[{'options': {'type': 'area',
#                                                         'stacking': 'normal'},
#                                             'terms': ['injections']}],
#                            chart_options={
#                                'title': {'text': 'Injections Over Time'},
#                                'xAxis': {'title': {'text': 'Seconds'}},
#                                'yAxis': {'title': {
#                                    'text': 'Number of Injections'}}})
#     return chart
