from collections import OrderedDict
from django.db.models import Case, Count, IntegerField, Sum, When
from json import dumps
from time import time

from .. import fix_sort, fix_sort_list
from . import colors, colors_extra, default_chart


def outcomes(**kwargs):
    campaigns = kwargs['campaigns']
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    start = time()
    chart_id = 'registers_chart'
    injections = injections.exclude(target='TLB')
    registers = injections.values_list(
        'register', flat=True).distinct().order_by('register')
    if len(registers) < 1:
        return
    registers = sorted(registers, key=fix_sort)
    chart = default_chart(chart_id, 'Injected Register', registers)
    chart['xAxis']['labels'] = {
        'align': 'right',
        'rotation': -60,
        'step': 1,
        'x': 5,
        'y': 15
    }
    if success:
        outcome = 'success'
    elif group_categories:
        outcome = 'result__outcome_category'
    else:
        outcome = 'result__outcome'
    series = {campaign: OrderedDict([
        (str(outcome), [0]*len(registers)) for outcome in outcomes])
        for campaign in campaigns}
    for campaign, outcome, register, count in injections.values_list(
            'result__campaign_id', outcome, 'register').distinct().annotate(
                count=Count('result')
            ).values_list('result__campaign_id', outcome, 'register', 'count'):
        series[campaign][outcome][registers.index(register)] = count
    for campaign in series:
        for outcome, data in series[campaign].items():
            series_data = {'data': data, 'name': outcome, 'stack': campaign}
            if campaign == campaigns[0]:
                series_data['id'] = outcome
            else:
                series_data['linkedTo'] = outcome
            if outcome in colors:
                series_data['color'] = colors[outcome]
            chart['series'].append(series_data)
    chart = dumps(chart, indent=4)
    chart = chart.replace('\"__series_click__\"', """
    function(event) {
        var reg = this.category.split(':');
        var register = reg[0];
        var index = reg[1];
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
                    '&injection__register='+register+filter);
    }
    """)
    chart = chart.replace('\"__tooltip_formatter__\"', """
        function () {
            return this.series.name+': <b>'+this.y+'</b><br/>'+
                   'Register: '+this.x+'<br/>'+
                   'Campaign: '+this.series.options.stack;
        }
    """)
    chart = chart.replace('\n    ', '\n                        ')
    if success:
        chart = chart.replace('?outcome=', '?injection__success=')
    elif group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append({
        'id': chart_id,
        'order': order,
        'title': 'Registers'})
    print(chart_id, round(time()-start, 2), 'seconds')


def fields(**kwargs):
    campaigns = kwargs['campaigns']
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    start = time()
    chart_id = 'register_fields_chart'
    injections = injections.exclude(target='TLB').exclude(field__isnull=True)
    fields = list(injections.values_list(
        'field', flat=True).distinct().order_by('field'))
    if len(fields) < 1:
        return
    chart = default_chart(chart_id, 'Injected Register Field', fields)
    if success:
        outcome = 'success'
    elif group_categories:
        outcome = 'result__outcome_category'
    else:
        outcome = 'result__outcome'
    series = {campaign: OrderedDict([
        (str(outcome), [0]*len(fields)) for outcome in outcomes])
        for campaign in campaigns}
    for campaign, outcome, field, count in injections.values_list(
            'result__campaign_id', outcome, 'field').distinct().annotate(
                count=Count('result')
            ).values_list('result__campaign_id', outcome, 'field', 'count'):
        series[campaign][outcome][fields.index(field)] = count
    for campaign in series:
        for outcome, data in series[campaign].items():
            series_data = {'data': data, 'name': outcome, 'stack': campaign}
            if campaign == campaigns[0]:
                series_data['id'] = outcome
            else:
                series_data['linkedTo'] = outcome
            if outcome in colors:
                series_data['color'] = colors[outcome]
            chart['series'].append(series_data)
    chart = dumps(chart, indent=4)
    chart = chart.replace('\"__series_click__\"', """
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
                    '&injection__field='+this.category+filter);
    }
    """)
    chart = chart.replace('\"__tooltip_formatter__\"', """
        function () {
            return this.series.name+': <b>'+this.y+'</b><br/>'+
                   'Register field: '+this.x+'<br/>'+
                   'Campaign: '+this.series.options.stack;
        }
    """)
    chart = chart.replace('\n    ', '\n                        ')
    if success:
        chart = chart.replace('?outcome=', '?injection__success=')
    elif group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append({
        'id': chart_id,
        'order': order,
        'title': 'Register Fields'})
    print(chart_id, round(time()-start, 2), 'seconds')


def bits(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    start = time()
    injections = injections.exclude(target='TLB')
    bits = list(injections.values_list('bit', flat=True).distinct().order_by(
        '-bit'))
    if len(bits) < 1:
        return
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'register_bits_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'register_bits_chart',
            'sourceWidth': 960,
            'sourceHeight': 540,
            'scale': 2
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': '__series_click__'
                    }
                },
                'stacking': True
            }
        },
        'series': [],
        'title': {
            'text': None
        },
        'xAxis': {
            'categories': bits,
            'title': {
                'text': 'Injected Bit (MSB=' +
                        ('31' if max(bits) < 32 else '63')+')'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Injections'
            }
        }
    }
    for outcome in outcomes:
        when_kwargs = {'then': 1}
        if success:
            when_kwargs['success'] = outcome
        else:
            when_kwargs['result__outcome_category' if group_categories
                        else 'result__outcome'] = outcome
        data = list(injections.values_list('bit').distinct().order_by(
            '-bit').annotate(
                count=Sum(Case(When(**when_kwargs), default=0,
                               output_field=IntegerField()))
            ).values_list('count', flat=True))
        chart['series'].append({'data': data, 'name': str(outcome)})
    chart = dumps(chart, indent=4)
    chart = chart.replace('\"__series_click__\"', """
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
        window.open('results?outcome='+outcome+
                    '&injection__bit='+this.category+filter);
    }
    """.replace('\n    ', '\n                        '))
    if success:
        chart = chart.replace('?outcome=', '?injection__success=')
    elif group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append({
        'id': 'register_bits_chart',
        'order': order,
        'title': 'Register Bits'})
    print('register_bits_chart:', round(time()-start, 2), 'seconds')


def access(**kwargs):
    chart_data = kwargs['chart_data']
    chart_list = kwargs['chart_list']
    group_categories = kwargs['group_categories']
    injections = kwargs['injections']
    order = kwargs['order']
    outcomes = kwargs['outcomes']
    success = kwargs['success']

    start = time()
    injections = injections.exclude(target='TLB').exclude(
        register_access__isnull=True)
    register_accesses = injections.values_list(
        'register_access', flat=True).distinct().order_by('register_access')
    if len(register_accesses) < 1:
        return
    register_accesses = sorted(register_accesses)
    extra_colors = list(colors_extra)
    chart = {
        'chart': {
            'renderTo': 'register_accesses_chart',
            'type': 'column',
            'zoomType': 'xy'
        },
        'colors': [colors[outcome] if outcome in colors else extra_colors.pop()
                   for outcome in outcomes],
        'credits': {
            'enabled': False
        },
        'exporting': {
            'filename': 'register_accesses_chart',
            'sourceWidth': 480,
            'sourceHeight': 360,
            'scale': 2
        },
        'title': {
            'text': None
        },
        'plotOptions': {
            'series': {
                'point': {
                    'events': {
                        'click': '__series_click__'
                    }
                },
                'stacking': True
            }
        },
        'series': [],
        'xAxis': {
            'categories': register_accesses,
            'title': {
                'text': 'Injected Register Access'
            }
        },
        'yAxis': {
            'title': {
                'text': 'Injections'
            }
        }
    }
    for outcome in outcomes:
        when_kwargs = {'then': 1}
        if success:
            when_kwargs['success'] = outcome
        else:
            when_kwargs['result__outcome_category' if group_categories
                        else 'result__outcome'] = outcome
        data = injections.values_list('register_access').distinct().order_by(
            'register_access').annotate(
                count=Sum(Case(When(**when_kwargs),
                               default=0, output_field=IntegerField()))
            ).values_list('register_access', 'count')
        data = sorted(data, key=fix_sort_list)
        chart['series'].append({'data': list(zip(*data))[1],
                                'name': str(outcome)})
    chart = dumps(chart, indent=4)
    chart = chart.replace('\"__series_click__\"', """
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
        window.open('results?outcome='+outcome+
                    '&injection__register_access='+this.category+filter);
    }
    """.replace('\n    ', '\n                        '))
    if success:
        chart = chart.replace('?outcome=', '?injection__success=')
    elif group_categories:
        chart = chart.replace('?outcome=', '?outcome_category=')
    chart_data.append(chart)
    chart_list.append({
        'id': 'register_accesses_chart',
        'order': order,
        'title': 'Register Access'})
    print('registers_accesses_chart:', round(time()-start, 2), 'seconds')
