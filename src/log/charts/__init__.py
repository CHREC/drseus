from bisect import bisect_left
from collections import defaultdict

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
    'Dropping memop': '#bf6600'
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


def default_chart(chart_id, axis_title, axis_items):
    return {
        'chart': {
            'renderTo': chart_id,
            'type': 'column',
            'zoomType': 'xy'
        },
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': chart_id,
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'plotOptions': {
            'column': {
                'stacking': 'normal'
            },
            'series': {
                'point': {
                    'events': {
                        'click': '__series_click__'
                    }
                }
            }
        },
        'series': [],
        'title': {
            'text': None
        },
        'tooltip': {
            'formatter': '__tooltip_formatter__'
        },
        'xAxis': {
            'categories': axis_items,
            'title': {
                'text': axis_title
            }
        },
        'yAxis': {
            'title': {
                'text': 'Injections'
            }
        }
    }
