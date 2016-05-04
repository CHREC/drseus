from bisect import bisect_left
from collections import OrderedDict
from copy import deepcopy
from django.db.models import Avg, Case, Count, When
from json import dumps
from numpy import convolve, ones
from time import perf_counter
from traceback import extract_stack

from .. import fix_sort

colors = {
    'Data error': '#ba79f2',
    'Detected data error': '#7f6600',
    'Silent data error': '#162859',

    'Execution error': '#cc3333',
    'Hanging': '#c200f2',
    'Illegal instruction': '#ff4400',
    'Kernel error': '#591643',
    'Reboot': '#e4d354',
    'Segmentation fault': '#f2a200',
    'Signal SIGABRT': '#f7a35c',
    'Signal SIGBUS': '#8085e9',
    'Signal SIGFPE': '#f15c80',
    'Signal SIGILL': '#9fbf60',
    'Signal SIGIOT': '#88ff00',
    'Signal SIGSEGV': '#7c9da6',
    'Signal SIGTRAP': '#ff83ff',
    'Stall detected': '#90ed7d',


    'No error': '#33cc70',
    'Latent faults': '#a18069',
    'Masked faults': '#185900',
    'Persistent faults': '#0099e6',

    'Post execution error': '#0061f2',

    'File transfer error': '#f75d59',
    'SCP error': '#d4a017',
    'SSH error': '#434348',

    'Debugger error': '#bf6600',
    'Error halting DUT': '#91e8e1',

    'Simics error': '#006652',
    'Address not mapped': '#992645',

    'Incomplete': '#7cb5ec',
    'In progress': '#2b908f',
    'Interrupted': '#f45b5b',

    'True': '#01df74',
    'False': '#fe2e64',

    'Error finding port or pseudoterminal': '#610b0b',
    'Error getting register value': '#8a0808',
    'Error injecting fault': '#b40404',
}


def create_chart(chart_list, chart_data, chart_title, order=0, injections=None,
                 results=None, outcomes=None,
                 # x axis info
                 xaxis_title=None, xaxis_name=None, xaxis_type=None,
                 xaxis_model='injections', xaxis_items=None,
                 # y axis info
                 yaxis_items=None, average=None,
                 # axis options
                 intervals=False, pie=False,
                 # series groups
                 group_categories=True, success=False,
                 # additional charts
                 percent=False, log=False, smooth=False,
                 # chart properties
                 rotate_labels=False, export_wide=False):
    start = perf_counter()
    chart_id = str(extract_stack()[-2][-2])
    if yaxis_items is None:
        yaxis_items = outcomes
    if xaxis_model == 'injections':
        stack_type = 'result__campaign_id'
        model = injections
    elif xaxis_model == 'results':
        stack_type = 'campaign_id'
        model = results
    else:
        raise Exception()
    if success and (average or xaxis_model == 'results'):
        return
    if not pie:
        if xaxis_items is None:
            xaxis_items = model.values_list(xaxis_type, flat=True).distinct()
        campaigns = list(model.values_list(
            stack_type, flat=True).distinct().order_by(stack_type))
        log = log and len(yaxis_items) == 1
        smooth = smooth and len(campaigns) == 1
        if not isinstance(xaxis_items, list):
            xaxis_items = sorted(xaxis_items, key=fix_sort)
        if len(xaxis_items) < 1:
            return
    chart = {
        'chart': {
            'renderTo': chart_id,
            'type': 'pie' if pie else 'column',
            'zoomType': 'xy'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': chart_id,
            'sourceWidth': 960 if export_wide else 480,
            'sourceHeight': 540 if export_wide else 360,
            'scale': 2
        },
        'plotOptions': {},
        'series': [],
        'title': {
            'text': None
        },
        'tooltip': {
            'formatter': '__tooltip_formatter__'
        },
        'yAxis': {
            'title': {
                'text':  (
                    yaxis_items[0] if yaxis_items and len(yaxis_items) == 1
                    else 'Results' if xaxis_model == 'results'
                    else 'Injections')
            }
        }
    }
    if pie:
        chart['plotOptions']['pie'] = {
            'dataLabels': {
                'formatter': '__dataLabels_formatter__',
            }
        }
        chart['series'].append({'data': []})
    else:
        chart['plotOptions']['column'] = {
            'stacking': 'normal'
        }
        chart['xAxis'] = {
            'categories': xaxis_items,
            'title': {
                'text': xaxis_title
            }
        }
        if len(campaigns) == 1 and len(yaxis_items) == 1:
            chart['legend'] = {
                'enabled': False
            }
    if intervals:
        chart['xAxis']['labels'] = {
            'formatter': '__label_formatter__'
        }
    else:
        chart['plotOptions']['series'] = {
            'point': {
                'events': {
                    'click': '__series_click__'
                }
            }
        }
    if rotate_labels:
        chart['xAxis']['labels'] = {
            'align': 'right',
            'rotation': -60,
            'step': 1,
            'x': 5,
            'y': 15
        }
    if average and 'data_diff' in average:
        chart['yAxis']['labels'] = {
            'format': '{value}%'
        }
        chart['yAxis']['max'] = 100
    if smooth:
        chart_smooth = deepcopy(chart)
        chart_smooth['chart']['type'] = 'area'
        chart_smooth['chart']['renderTo'] = '{}_smooth'.format(chart_id)

    if success:
        yaxis_type = 'success'
    elif group_categories:
        if xaxis_model == 'results':
            yaxis_type = 'outcome_category'
        else:
            yaxis_type = 'result__outcome_category'
    else:
        if xaxis_model == 'results':
            yaxis_type = 'outcome'
        else:
            yaxis_type = 'result__outcome'
    if pie:
        series = OrderedDict([[str(yaxis_item), 0]
                              for yaxis_item in yaxis_items])
    elif intervals and average:
        series = {
            campaign: OrderedDict([(str(yaxis_item),
                                    [[] for i in range(len(xaxis_items))])
                                   for yaxis_item in yaxis_items])
            for campaign in campaigns}
    else:
        series = {
            campaign: OrderedDict([(str(yaxis_item), [0]*len(xaxis_items))
                                   for yaxis_item in yaxis_items])
            for campaign in campaigns}
    if pie:
        for yaxis_item, value in \
                model.values_list(yaxis_type).distinct().annotate(
                    value=Count(yaxis_type)).values_list(yaxis_type, 'value'):
            series[str(yaxis_item)] = value
    elif average:
        when_kwargs = {'{}__isnull'.format(average): True, 'then': 0}
        for campaign, xaxis_item, value in model.values_list(
                    stack_type, xaxis_type
                ).distinct().annotate(value=Avg(Case(
                    When(**when_kwargs), default=average)
                )).values_list(stack_type, xaxis_type, 'value'):
            if intervals:
                x_index = bisect_left(xaxis_items, xaxis_item,
                                      hi=len(xaxis_items)-1)
                series[campaign][str(yaxis_items[0])][x_index].append(value)
            else:
                (series[campaign][str(yaxis_items[0])]
                       [xaxis_items.index(xaxis_item)]) = value
    elif intervals:
        for campaign, yaxis_item, xaxis_item in model.values_list(
                stack_type, yaxis_type, xaxis_type):
            index = bisect_left(xaxis_items, xaxis_item, hi=len(xaxis_items)-1)
            series[campaign][str(yaxis_item)][index] += 1
    else:
        for campaign, yaxis_item, xaxis_item, value in model.values_list(
                    stack_type, yaxis_type, xaxis_type
                ).distinct().annotate(value=Count(
                    'id' if xaxis_model == 'results' else 'result_id')
                ).values_list(stack_type, yaxis_type, xaxis_type, 'value'):
            (series[campaign][str(yaxis_item)]
                   [xaxis_items.index(xaxis_item)]) = value
    if pie:
        for yaxis_item, value in series.items():
                series_item = {'name': yaxis_item}
                if yaxis_item in colors:
                    series_item['color'] = colors[yaxis_item]
                else:
                    print('* missing color for', yaxis_item)
                series_item['y'] = value
                chart['series'][0]['data'].append(series_item)
    else:
        for stack in series:
            for yaxis_item, values in series[stack].items():
                if isinstance(values[0], list):
                    # TODO: remove these empty averages from axis
                    values = [sum(value)/len(value) if len(value) else 0
                              for value in values]
                series_item = {}
                if 'campaign_id' not in xaxis_type:
                    series_item['stack'] = stack
                if average and len(series) > 1:
                    series_item['name'] = 'Campaign {}'.format(stack)
                else:
                    series_item['name'] = yaxis_item
                    if stack == campaigns[0]:
                        series_item['id'] = yaxis_item
                    else:
                        series_item['linkedTo'] = yaxis_item
                    if yaxis_item in colors:
                        series_item['color'] = colors[yaxis_item]
                    elif not average:
                        print('* missing color for', yaxis_item)
                if average and 'data_diff' in average:
                    values = [x*100 for x in values]
                if smooth:
                    series_item_smooth = deepcopy(series_item)
                    series_item_smooth['data'] = convolve(values, ones(10)/10,
                                                          'same').tolist()
                    chart_smooth['series'].append(series_item_smooth)
                series_item['data'] = values
                chart['series'].append(series_item)
    chart_json = [dumps(chart, indent=4)]
    if smooth:
        chart_json.append(dumps(chart_smooth, indent=4))
    if percent:
        chart_percent = deepcopy(chart)
        chart_percent['chart']['renderTo'] = '{}_percent'.format(chart_id)
        chart_percent['plotOptions']['series']['stacking'] = 'percent'
        chart_percent['yAxis']['labels'] = {'format': '{value}%'}
        chart_json.append(dumps(chart_percent, indent=4))
    if log:
        chart_log = deepcopy(chart)
        chart_log['chart']['renderTo'] = '{}_log'.format(chart_id)
        chart_log['yAxis']['type'] = 'logarithmic'
        chart_json.append(dumps(chart_log, indent=4))
    for index, json in enumerate(chart_json):
        if not intervals:
            if pie:
                json = json.replace('"__series_click__"', """
                    function(event) {
                        var outcomes = __yaxis_items__;
                        var filter;
                        if (window.location.href.indexOf('?') > -1) {
                            filter = window.location.href.replace(/.*\?/g, '&');
                        } else {
                            filter = '';
                        }
                        var outcome;
                        if (this.series.name == 'True') {
                            outcome = '1';
                        } else if (this.series.name == 'False') {
                            outcome = '0';
                        } else {
                            outcome = outcomes[this.x];
                        }
                        window.open('results?outcome='+outcome+filter);
                    }
                """.replace('__yaxis_items__', str(yaxis_items)))
            elif average:
                json = json.replace('"__series_click__"', """
                    function(event) {
                        var filter;
                        if (window.location.href.indexOf('?') > -1) {
                            filter = window.location.href.replace(/.*\?/g, '&');
                        } else {
                            filter = '';
                        }
                        var outcome;
                        if (this.series.name == 'True') {
                            outcome = '1';
                        } else if (this.series.name == 'False') {
                            outcome = '0';
                        } else {
                            outcome = this.series.name;
                        }
                        window.open('/campaign/'+this.series.options.stack+
                                    '/results?__xaxis_model_type__' +
                                    '__xaxis_type__='+this.category+filter);
                    }
                """)
            else:
                json = json.replace('"__series_click__"', """
                    function(event) {
                        var filter;
                        if (window.location.href.indexOf('?') > -1) {
                            filter = window.location.href.replace(/.*\?/g, '&');
                        } else {
                            filter = '';
                        }
                        var outcome;
                        if (this.series.name == 'True') {
                            outcome = '1';
                        } else if (this.series.name == 'False') {
                            outcome = '0';
                        } else {
                            outcome = this.series.name;
                        }
                        window.open('/campaign/'+this.series.options.stack+
                                    '/results?outcome='+outcome+
                                    '&__xaxis_model_type____xaxis_type__=' +
                                    this.category+filter);
                    }
                """)
        if pie:
            json = json.replace('"__tooltip_formatter__"', """
                function () {
                    return this.key+': <b>'+this.y+'</b>';
                }
            """).replace('\"__dataLabels_formatter__\"', """
                function() {
                    var outcomes = __yaxis_items__;
                    return ''+outcomes[parseInt(this.point.x)]+' '+
                    Highcharts.numberFormat(this.percentage, 1)+'%';
                }
            """.replace('__yaxis_items__', str(yaxis_items)))
        elif 'campaign_id' in xaxis_type:
            json = json.replace('"__tooltip_formatter__"', """
                function () {
                    return this.series.name+': <b>'+this.y+'</b><br/>'+
                           '__xaxis_name__: '+this.x+'<br/>';
                }
            """).replace('__xaxis_name__', xaxis_name).replace(
                '__xaxis_type__', xaxis_type)
        else:
            json = json.replace('"__tooltip_formatter__"', """
                function () {
                    return this.series.name+': <b>'+this.y+'</b><br/>'+
                           '__xaxis_name__: '+this.x+'<br/>'+
                           'Campaign: '+this.series.options.stack;
                }
            """).replace('__xaxis_name__', xaxis_name).replace(
                '__xaxis_type__', xaxis_type)
        if success:
            json = json.replace('?outcome=', '?__xaxis_model_type__success=')
        elif group_categories:
            json = json.replace('?outcome=', '?outcome_category=')
        if intervals:
            json = json.replace('"__label_formatter__"', """
                function() {
                    return this.value.toFixed(4);
                }
            """)
        json = json.replace('__xaxis_model_type__',
                            '' if xaxis_model == 'results' else 'injection__')
        chart_json[index] = json
    chart_data.extend(chart_json)
    chart_list.append({'id': chart_id, 'log': log, 'order': order,
                       'percent': percent, 'smooth': smooth,
                       'title': chart_title})
    print(chart_id, round(perf_counter()-start, 2), 'seconds')
