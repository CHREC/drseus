from bisect import bisect_left
from collections import defaultdict, OrderedDict
from copy import deepcopy
from django.db.models import Avg, Case, Count, When
from json import dumps
from numpy import convolve, ones
from time import time

colors = {
    'Data error': '#ba79f2',
    'Detected data error': '#7f6600',
    'Silet data error': '#162859',

    'Execution error': '#cc3333',
    'Hanging': '#c200f2',
    'Illegal instruction': '#ff4400',
    'Kernel error': '#591643',
    'Segmentation fault': '#f2a200',
    'Signal SIGILL': '#9fbf60',
    'Signal SIGIOT': '#88ff00',
    'Signal SIGSEGV': '#7c9da6',
    'Signal SIGTRAP': '#ff83ff',

    'No error': '#33cc70',
    'Latent faults': '#a18069',
    'Masked faults': '#185900',
    'Persistent faults': '#0099e6',

    'Post execution error': '#0061f2',

    'SCP error': '#d4a017',
    'Missing output': '#f75d59',

    'Simics error': '#006652',
    'Address not mapped': '#992645',
    'Dropping memop': '#bf6600',

    'True': '#00ff00',
    'False': '#ff0000'
}

colors_extra = ['#7cb5ec', '#434348', '#90ed7d', '#f7a35c', '#8085e9',
                '#f15c80', '#e4d354', '#2b908f', '#f45b5b', '#91e8e1']*5


def count_intervals(items, intervals, data_diff=False):
    if data_diff:
        count_dict = defaultdict(list)
    else:
        count_dict = defaultdict(int)
    for item in items:
        if data_diff:
            index = bisect_left(intervals, item[0], hi=len(intervals)-1)
            count_dict[intervals[index]].append(
                item[1] if item[1] is not None else 0)
        else:
            index = bisect_left(intervals, item, hi=len(intervals)-1)
            count_dict[intervals[index]] += 1
    count_list = []
    for interval in intervals:
        if interval in count_dict.keys():
            if data_diff:
                count_list.append(
                    sum(count_dict[interval])/len(count_dict[interval])*100)
            else:
                count_list.append(count_dict[interval])
        else:
            count_list.append(0)
    return count_list


def create_chart(chart_list, chart_data, chart_title, order, chart_id,
                 injections, xaxis_title, xaxis_name, xaxis_type, xaxis_items,
                 yaxis_items, group_categories=False, success=False,
                 average=None, percent=False, log=False, smooth=False,
                 intervals=False, results=None, pie=False, rotate_labels=False,
                 export_wide=False):
    start = time()
    if results is not None:
        stack_type = 'campaign_id'
        model = results
    else:
        stack_type = 'result__campaign_id'
        model = injections
    if not pie:
        campaigns = list(model.values_list(
            stack_type, flat=True).distinct().order_by(stack_type))
        log = log and len(yaxis_items) == 1
        smooth = smooth and len(campaigns) == 1
        if not isinstance(xaxis_items, list):
            xaxis_items = list(xaxis_items)
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
                'text': 'Injections'
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
    if smooth:
        chart_smooth = deepcopy(chart)
        chart_smooth['chart']['type'] = 'area'
        chart_smooth['chart']['renderTo'] = '{}_smooth'.format(chart_id)
    if success:
        yaxis_type = 'success'
    elif group_categories:
        if results is not None:
            yaxis_type = 'outcome_category'
        else:
            yaxis_type = 'result__outcome_category'
    else:
        if results is not None:
            yaxis_type = 'outcome'
        else:
            yaxis_type = 'result__outcome'
    if pie:
        series = OrderedDict([[str(yaxis_item), 0]
                              for yaxis_item in yaxis_items])
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
    elif intervals:
        for campaign, yaxis_item, xaxis_item in model.values_list(
                stack_type, yaxis_type, xaxis_type):
            index = bisect_left(xaxis_items, xaxis_item, hi=len(xaxis_items)-1)
            series[campaign][str(yaxis_item)][index] += 1
    elif average:
        when_kwargs = {'{}__isnull'.format(average): True, 'then': 0}
        for campaign, xaxis_item, value in model.values_list(
                    stack_type, xaxis_type
                ).distinct().annotate(value=Avg(Case(
                    When(**when_kwargs), default=average)
                )).values_list(stack_type, xaxis_type, 'value'):
            (series[campaign][str(yaxis_items[0])]
                   [xaxis_items.index(xaxis_item)]) = value
    else:
        for campaign, yaxis_item, xaxis_item, value in model.values_list(
                    stack_type, yaxis_type, xaxis_type
                ).distinct().annotate(value=Count('result')).values_list(
                    stack_type, yaxis_type, xaxis_type, 'value'):
            (series[campaign][str(yaxis_item)]
                   [xaxis_items.index(xaxis_item)]) = value
    if pie:
        for yaxis_item, value in series.items():
                series_item = {'name': yaxis_item}
                if yaxis_item in colors:
                    series_item['color'] = colors[yaxis_item]
                series_item['y'] = value
                chart['series'][0]['data'].append(series_item)
    else:
        for stack in series:
            for yaxis_item, values in series[stack].items():
                series_item = {'name': yaxis_item, 'stack': stack}
                if average is None:
                    if stack == campaigns[0]:
                        series_item['id'] = yaxis_item
                    else:
                        series_item['linkedTo'] = yaxis_item
                if yaxis_item in colors:
                    series_item['color'] = colors[yaxis_item]
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
                                    '/results?injection____xaxis_type__=' +
                                    this.category+filter);
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
                                    '&injection____xaxis_type__=' +
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
            json = json.replace('?outcome=', '?injection__success=')
        elif group_categories:
            json = json.replace('?outcome=', '?outcome_category=')
        if intervals:
            json = json.replace('"__label_formatter__"', """
                function() {
                    return this.value.toFixed(4);
                }
            """)
        chart_json[index] = json
    chart_data.extend(chart_json)
    chart_list.append({'id': chart_id, 'log': log, 'order': order,
                       'percent': percent, 'smooth': smooth,
                       'title': chart_title})
    print(chart_id, round(time()-start, 2), 'seconds')
