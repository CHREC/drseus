from django.http import HttpResponse
from django.shortcuts import redirect, render
from django_tables2 import RequestConfig
from imghdr import what
from mimetypes import guess_type
from os.path import exists
from subprocess import Popen

from .charts import (campaigns_chart, injections_charts, results_charts,
                     target_bits_chart)
from . import filters
from . import models
from . import tables

navigation_items = (('All Campaigns', '/', 'campaigns', 'flag'),
                    ('All Results', '/results', 'results', 'list'),
                    ('All Events', '/events', 'events', 'calendar'),
                    ('All Injections', '/injections', 'injections',
                     'crosshairs'),
                    ('All Charts', '/category_charts', 'charts', 'bar-chart'))

campaign_items = (('Campaign Information', 'info', 'info', 'info'),
                  ('Campaign Results', 'results', 'results', 'list'),
                  ('Campaign Events', 'events', 'events', 'calendar'),
                  ('Campaign Injections', 'injections', 'injections',
                   'crosshairs'),
                  ('Campaign Charts', 'category_charts', 'charts', 'bar-chart'))

table_length = 50


def campaigns_page(request):
    campaign = models.campaign.objects.all()
    if campaign.count() == 1:
        return redirect('/campaign/'+str(campaign[0].id)+'/info')
    campaign_table = tables.campaigns(campaign)
    chart_data = campaigns_chart(models.result.objects.all())
    RequestConfig(request).configure(campaign_table)
    return render(request, 'campaigns.html', {
        'chart_data': chart_data, 'campaign_table': campaign_table,
        'navigation_items': navigation_items})


def campaign_page(request, campaign_id):
    campaign = models.campaign.objects.get(id=campaign_id)
    chart_data = target_bits_chart(campaign)
    output_file = ('campaign-data/'+str(campaign_id) +
                   '/gold_'+campaign.output_file)
    output_image = exists(output_file) and what(output_file) is not None
    campaign_table = tables.campaign(models.campaign.objects.filter(
        id=campaign_id))
    event_table = tables.event(models.event.objects.filter(
        campaign_id=campaign_id))
    RequestConfig(request, paginate=False).configure(campaign_table)
    RequestConfig(request, paginate=False).configure(event_table)
    return render(request, 'campaign.html', {
        'campaign': campaign, 'campaign_table': campaign_table,
        'chart_data': chart_data, 'navigation_items': navigation_items,
        'event_table': event_table, 'campaign_items': campaign_items,
        'output_image': output_image})


def category_charts_page(request, campaign_id=None):
    return charts_page(request, campaign_id, True)


def charts_page(request, campaign_id=None, group_categories=False):
    if campaign_id is not None:
        campaign = models.campaign.objects.get(id=campaign_id)
        campaign_items_ = campaign_items
        results = models.result.objects.filter(campaign_id=campaign_id)
    else:
        campaign = None
        campaign_items_ = None
        results = models.result.objects.all()
    result_filter = filters.result(request.GET, queryset=results)
    results = result_filter.qs
    if results.count() > 0:
        chart_data, chart_list = results_charts(results, group_categories)
        chart_list = [chart[:-1]
                      for chart in sorted(chart_list, key=lambda x: x[2])]
    else:
        chart_data = None
        chart_list = None
    return render(request, 'charts.html', {
        'campaign': campaign, 'campaign_items': campaign_items_,
        'categories': group_categories, 'chart_data': chart_data,
        'chart_list': chart_list, 'filter': result_filter,
        'navigation_items': navigation_items})


def events_page(request, campaign_id=None):
    if campaign_id is not None:
        campaign = models.campaign.objects.get(id=campaign_id)
        campaign_items_ = campaign_items
        events = models.event.objects.filter(result__campaign_id=campaign_id)
    else:
        campaign = None
        campaign_items_ = None
        events = models.event.objects.all()
    event_filter = filters.event(request.GET, queryset=events)
    events = event_filter.qs
    event_table = tables.events(events)
    RequestConfig(
        request, paginate={'per_page': table_length}).configure(event_table)
    return render(request, 'events.html', {
        'campaign': campaign, 'navigation_items': navigation_items,
        'event_count': '{:,}'.format(events.count()),
        'event_table': event_table, 'filter': event_filter,
        'campaign_items': campaign_items_})


def injections_page(request, campaign_id=None):
    if campaign_id is not None:
        campaign = models.campaign.objects.get(id=campaign_id)
        campaign_items_ = campaign_items
        injections = models.injection.objects.filter(
            result__campaign_id=campaign_id)
    else:
        campaign = None
        campaign_items_ = None
        injections = models.injection.objects.all()
    injection_filter = filters.injection(request.GET, queryset=injections)
    injections = injection_filter.qs
    if injections.count() > 0:
        chart_data, chart_list = injections_charts(injections)
        chart_list = [chart[:-1]
                      for chart in sorted(chart_list, key=lambda x: x[2])]
    else:
        chart_data = None
        chart_list = None
    injection_table = tables.injections(injections)
    RequestConfig(
        request, paginate={'per_page': table_length}).configure(injection_table)
    return render(request, 'injections.html', {
        'campaign': campaign, 'chart_data': chart_data,
        'chart_list': chart_list, 'navigation_items': navigation_items,
        'filter': injection_filter,
        'injection_count': '{:,}'.format(injections.count()),
        'campaign_items': campaign_items_,
        'injection_table': injection_table})


def results_page(request, campaign_id=None):
    if campaign_id is not None:
        campaign = models.campaign.objects.get(id=campaign_id)
        campaign_items_ = campaign_items
        output_file = ('campaign-data/'+campaign_id+'/gold_' +
                       campaign.output_file)
        if exists(output_file) and what(output_file) is not None:
            output_image = True
        else:
            output_image = False
        results = models.result.objects.filter(campaign_id=campaign_id)
    else:
        campaign = None
        campaign_items_ = None
        output_image = True
        results = models.result.objects.all()
    result_filter = filters.result(request.GET, queryset=results)
    results = result_filter.qs
    if request.method == 'GET':
        if (('view_output' in request.GET or
                'view_output_image' in request.GET) and
                'select_box' in request.GET):
            result_ids = sorted(map(int, dict(request.GET)['select_box']),
                                reverse=True)
            results = models.result.objects.filter(
                    id__in=result_ids).order_by('-id')
            image = 'view_output_image' in request.GET
            if image:
                result_ids = []
                for result in results:
                    if exists(
                        'campaign-data/'+str(result.campaign_id)+'/results/' +
                            str(result.id)+'/'+result.campaign.output_file):
                        result_ids.append(result.id)
                results = models.result.objects.filter(
                    id__in=result_ids).order_by('-id')
            if results.count():
                return render(request, 'output.html', {
                    'campaign': campaign, 'image': image,
                    'campaign_items': campaign_items,
                    'navigation_items': navigation_items, 'results': results})
            else:
                results = result_filter.qs
        elif ('view_output_all' in request.GET or
              'view_output_image_all' in request.GET):
            image = 'view_output_image_all' in request.GET
            if image:
                result_ids = []
                for result in results:
                    if exists(
                        'campaign-data/'+str(result.campaign_id)+'/results/' +
                            str(result.id)+'/'+result.campaign.output_file):
                        result_ids.append(result.id)
                results = models.result.objects.filter(
                    id__in=result_ids).order_by('-id')
            if results.count():
                return render(request, 'output.html', {
                    'campaign': campaign, 'image': image,
                    'campaign_items': campaign_items,
                    'navigation_items': navigation_items, 'results': results})
            else:
                results = result_filter.qs
    elif request.method == 'POST':
        if 'new_outcome_category' in request.POST:
            results.values('outcome_category').update(
                outcome_category=request.POST['new_outcome_category'])
        elif 'new_outcome' in request.POST:
            results.values('outcome').update(
                outcome=request.POST['new_outcome'])
        elif 'delete' in request.POST and 'results[]' in request.POST:
            result_ids = [int(result_id) for result_id
                          in dict(request.POST)['results[]']]
            models.event.objects.filter(result_id__in=result_ids).delete()
            models.injection.objects.filter(result_id__in=result_ids).delete()
            models.simics_memory_diff.objects.filter(
                result_id__in=result_ids).delete()
            models.simics_register_diff.objects.filter(
                result_id__in=result_ids).delete()
            models.result.objects.filter(id__in=result_ids).delete()
        elif 'delete_all' in request.POST:
            result_ids = results.values('id')
            models.event.objects.filter(result_id__in=result_ids).delete()
            models.injection.objects.filter(result_id__in=result_ids).delete()
            models.simics_memory_diff.objects.filter(
                result_id__in=result_ids).delete()
            models.simics_register_diff.objects.filter(
                result_id__in=result_ids).delete()
            results.delete()
            if campaign_id:
                return redirect('/campaign/'+str(campaign_id)+'/results')
            else:
                return redirect('/results')
    result_table = tables.results(results)
    RequestConfig(
        request, paginate={'per_page': table_length}).configure(result_table)
    return render(request, 'results.html', {
        'campaign': campaign, 'navigation_items': navigation_items,
        'filter': result_filter, 'filter_tabs': True,
        'campaign_items': campaign_items_, 'output_image': output_image,
        'result_count': '{:,}'.format(results.count()),
        'result_table': result_table})


def result_page(request, result_id):
    result = models.result.objects.get(id=result_id)
    campaign_items_ = [(item[0], '../'+item[1], item[2], item[3])
                       for item in campaign_items]
    output_file = ('campaign-data/'+str(result.campaign_id)+'/results/' +
                   result_id+'/'+result.campaign.output_file)
    output_image = exists(output_file) and what(output_file) is not None
    result_table = tables.result(models.result.objects.filter(id=result_id))
    event_table = tables.event(models.event.objects.filter(result_id=result_id))
    if request.method == 'GET' and 'launch' in request.GET:
        drseus = 'drseus.py'
        if not exists(drseus):
            drseus = 'drseus.sh'
        Popen(['./'+drseus, 'regenerate', result_id])
    if request.method == 'POST' and 'save' in request.POST:
        result.outcome = request.POST['outcome']
        result.outcome_category = request.POST['outcome_category']
        result.save()
    elif request.method == 'POST' and 'delete' in request.POST:
        models.event.objects.filter(result_id=result.id).delete()
        models.injection.objects.filter(result_id=result.id).delete()
        models.simics_register_diff.objects.filter(result_id=result.id).delete()
        models.simics_memory_diff.objects.filter(result_id=result.id).delete()
        result.delete()
        return redirect('/campaign/'+str(result.campaign_id)+'/results')
    injections = models.injection.objects.filter(result_id=result_id)
    if result.campaign.simics:
        injection_table = tables.simics_injection(injections)
        register_diffs = models.simics_register_diff.objects.filter(
            result_id=result_id)
        register_filter = filters.simics_register_diff(
            request.GET, queryset=register_diffs)
        register_table = tables.simics_register_diff(register_filter.qs)
        RequestConfig(
            request,
            paginate={'per_page': table_length}).configure(register_table)
        memory_diffs = models.simics_memory_diff.objects.filter(
            result_id=result_id)
        memory_table = tables.simics_memory_diff(memory_diffs)
        RequestConfig(
            request,
            paginate={'per_page': table_length}).configure(memory_table)
    else:
        register_filter = None
        memory_table = None
        register_table = None
        injection_table = tables.hw_injection(injections)
    RequestConfig(request, paginate=False).configure(result_table)
    RequestConfig(request, paginate=False).configure(event_table)
    RequestConfig(request, paginate=False).configure(injection_table)
    return render(request, 'result.html', {
        'campaign_items': campaign_items_, 'event_table': event_table,
        'filter': register_filter, 'injection_table': injection_table,
        'memory_table': memory_table, 'navigation_items': navigation_items,
        'output_image': output_image, 'register_table': register_table,
        'result': result, 'result_table': result_table})


def output(request, result_id=None, campaign_id=None):
    if result_id is not None:
        result = models.result.objects.get(id=result_id)
        output_file = ('campaign-data/'+str(result.campaign_id)+'/results/' +
                       result_id+'/'+result.campaign.output_file)
    elif campaign_id is not None:
        campaign = models.campaign.objects.get(id=campaign_id)
        output_file = ('campaign-data/'+campaign_id+'/gold_' +
                       campaign.output_file)
    if exists(output_file):
        return HttpResponse(open(output_file, 'rb').read(),
                            content_type=guess_type(output_file))
    else:
        return HttpResponse()
