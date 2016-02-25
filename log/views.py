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

navigation_items = (('Campaign Information', 'info', 'info'),
                    ('Category Charts', 'category_charts', 'bar-chart'),
                    ('Outcome Charts', 'outcome_charts', 'bar-chart'),
                    ('Results', 'results', 'list'),
                    ('Events', 'events', 'exclamation-circle'),
                    ('Injections', 'injections', 'crosshairs'))


def campaigns_page(request):
    campaign = models.campaign.objects.all()
    if campaign.count() == 1:
        return redirect('/campaign/'+str(campaign[0].id)+'/results')
    campaign_table = tables.campaigns(campaign)
    chart_data = campaigns_chart(models.result.objects.all())
    RequestConfig(request).configure(campaign_table)
    return render(request, 'campaigns.html', {'chart_data': chart_data,
                                              'campaign_table': campaign_table})


def campaign_page(request, campaign_id):
    campaign = models.campaign.objects.get(id=campaign_id)
    chart_data = target_bits_chart(campaign)
    page_items = [('Campaign Data', 'campaign_data'), ('Events', 'events'),
                  ('Injection Targets', 'target_bits_chart')]
    output_file = ('campaign-data/'+str(campaign_id) +
                   '/gold_'+campaign.output_file)
    if exists(output_file) and what(output_file) is not None:
        output_image = True
        page_items.append(('Output Image', 'output_image'))
    else:
        output_image = False
    page_items.append(('DUT Output', 'dut_output'))
    if campaign.aux:
        page_items.append(('AUX Output', 'aux_output'))
    page_items.append(('Debugger Output', 'debugger_output'))
    campaign_table = tables.campaign(models.campaign.objects.filter(
        id=campaign_id))
    event_table = tables.event(models.event.objects.filter(
        campaign_id=campaign_id))
    RequestConfig(request, paginate=False).configure(campaign_table)
    RequestConfig(request, paginate=False).configure(event_table)
    return render(request, 'campaign.html', {
        'campaign': campaign, 'chart_data': chart_data,
        'event_table': event_table, 'navigation_items': navigation_items,
        'output_image': output_image, 'page_items': page_items,
        'campaign_table': campaign_table})


def category_charts_page(request, campaign_id):
    return charts_page(request, campaign_id, True)


def charts_page(request, campaign_id, group_categories=False):
    campaign = models.campaign.objects.get(id=campaign_id)
    page_items = [('Results Overview', 'overview_chart'),
                  ('Injections By Target', 'targets_charts')]
    if campaign.simics:
        page_items.append(('Fault Propagation', 'propagation_chart'))
    page_items.extend([('Data Diff By Target', 'diff_targets_chart'),
                       ('Injections By Register', 'registers_chart'),
                       ('Injections By Register Bit', 'register_bits_chart')])
    if campaign.simics:
        page_items.extend([('Injections By TLB Entry', 'tlbs_chart'),
                          ('Injections By TLB Field', 'tlb_fields_chart')])
    page_items.extend([('Injections Over Time', 'times_charts'),
                       ('Results By Injection Count', 'counts_charts')])
    filter_ = filters.result(
        request.GET, campaign=campaign_id,
        queryset=models.result.objects.filter(campaign_id=campaign_id))
    result_ids = filter_.qs.values('id').distinct()
    if result_ids.count() > 0:
        chart_data, chart_list = results_charts(result_ids, campaign,
                                                group_categories)
        chart_list = [chart[:-1]
                      for chart in sorted(chart_list, key=lambda x: x[2])]
    else:
        chart_data = None
        chart_list = None
    return render(request, 'charts.html', {
        'campaign': campaign, 'chart_data': chart_data,
        'chart_list': chart_list, 'filter': filter_,
        'categories': group_categories, 'navigation_items': navigation_items,
        'page_items': page_items})


def events_page(request, campaign_id):
    campaign = models.campaign.objects.get(id=campaign_id)
    filter_ = filters.result(
        request.GET, campaign=campaign_id,
        queryset=models.result.objects.filter(campaign_id=campaign_id))
    result_ids = filter_.qs.values('id').distinct()
    events = models.event.objects.filter(result_id__in=result_ids)
    event_table = tables.events(events)
    RequestConfig(request, paginate={'per_page': 250}).configure(event_table)
    return render(request, 'events.html', {
        'campaign': campaign, 'filter': filter_,
        'navigation_items': navigation_items, 'event_table': event_table})


def injections_page(request, campaign_id):
    campaign = models.campaign.objects.get(id=campaign_id)
    filter_ = filters.result(
        request.GET, campaign=campaign_id,
        queryset=models.result.objects.filter(campaign_id=campaign_id))
    result_ids = filter_.qs.values('id').distinct()
    if result_ids.count() > 0:
        chart_data, chart_list = injections_charts(result_ids, campaign)
        chart_list = [chart[:-1]
                      for chart in sorted(chart_list, key=lambda x: x[2])]
    else:
        chart_data = None
        chart_list = None
    injections = models.injection.objects.filter(
        result_id__in=result_ids)
    injection_table = tables.injections(injections)
    RequestConfig(request, paginate={'per_page': 50}).configure(injection_table)
    return render(request, 'injections.html', {
        'campaign': campaign, 'chart_data': chart_data,
        'chart_list': chart_list, 'filter': filter_,
        'navigation_items': navigation_items,
        'injection_table': injection_table})


def results_page(request, campaign_id):
    if models.result.objects.filter(campaign_id=campaign_id).count() == 0:
        return redirect('/campaign/'+str(campaign_id)+'/info')
    campaign = models.campaign.objects.get(id=campaign_id)
    output_file = ('campaign-data/'+campaign_id+'/gold_' +
                   campaign.output_file)
    if exists(output_file) and what(output_file) is not None:
        output_image = True
    else:
        output_image = False
    filter_ = filters.result(
        request.GET, campaign=campaign_id,
        queryset=models.result.objects.filter(campaign_id=campaign_id))
    result_ids = filter_.qs.values('id').distinct()
    results = models.result.objects.filter(id__in=result_ids)
    if request.method == 'GET':
        if (('view_output' in request.GET or
                'view_output_image' in request.GET) and
                'select_box' in request.GET):
            result_ids = sorted(map(int, dict(request.GET)['select_box']),
                                reverse=True)
            page_items = []
            for result_id in result_ids:
                page_items.append(('Result ID '+str(result_id), result_id))
            results = models.result.objects.filter(
                id__in=result_ids).order_by('-id')
            image = 'view_output_image' in request.GET
            return render(request, 'output.html', {
                'campaign': campaign, 'image': image,
                'navigation_items': navigation_items, 'page_items': page_items,
                'results': results})
        elif ('view_output_all' in request.GET or
              'view_output_image_all' in request.GET):
            page_items = [('Result ID '+str(result_id), result_id) for result_id
                          in results.values_list('id', flat=True)]
            image = 'view_output_image_all' in request.GET
            return render(request, 'output.html', {
                'campaign': campaign, 'image': image,
                'navigation_items': navigation_items, 'page_items': page_items,
                'results': results})
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
            models.event.objects.filter(result_id__in=result_ids).delete()
            models.injection.objects.filter(result_id__in=result_ids).delete()
            models.simics_memory_diff.objects.filter(
                result_id__in=result_ids).delete()
            models.simics_register_diff.objects.filter(
                result_id__in=result_ids).delete()
            models.result.objects.filter(id__in=result_ids).delete()
            return redirect('/campaign/'+str(campaign_id)+'/results')
    result_table = tables.results(results)
    RequestConfig(request, paginate={'per_page': 50}).configure(result_table)
    return render(request, 'results.html', {
        'campaign': campaign, 'filter': filter_,
        'navigation_items': navigation_items, 'output_image': output_image,
        'page_items_block': True, 'result_table': result_table})


def result_page(request, campaign_id, result_id):
    campaign = models.campaign.objects.get(id=campaign_id)
    navigation_items_ = [(item[0], '../'+item[1], item[2])
                         for item in navigation_items]
    page_items = [('Result', 'result'), ('Injections', 'injections'),
                  ('Events', 'events')]
    output_file = ('campaign-data/'+campaign_id+'/results/'+result_id +
                   '/'+campaign.output_file)
    if exists(output_file) and what(output_file) is not None:
        output_image = True
        page_items.append(('Output Image', 'output_image'))
    else:
        output_image = False
    page_items.append(('DUT Output', 'dut_output'))
    if campaign.aux:
        page_items.append(('AUX Output', 'aux_output'))
    page_items.append(('Debugger Output', 'debugger_output'))
    if campaign.simics:
        page_items.extend([('Register Diffs', 'register_diffs'),
                           ('Memory Diffs', 'memory_diffs')])
    result = models.result.objects.get(id=result_id)
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
        return redirect('/campaign/'+str(campaign_id)+'/results')
    injections = models.injection.objects.filter(result_id=result_id)
    if campaign.simics:
        injection_table = tables.simics_injection(injections)
        register_diffs = models.simics_register_diff.objects.filter(
            result_id=result_id)
        register_filter = filters.simics_register_diff(
            request.GET, queryset=register_diffs, campaign=campaign_id)
        register_table = tables.simics_register_diff(register_filter.qs)
        RequestConfig(request,
                      paginate={'per_page': 25}).configure(register_table)
        memory_diffs = models.simics_memory_diff.objects.filter(
            result_id=result_id)
        memory_table = tables.simics_memory_diff(memory_diffs)
        RequestConfig(request,
                      paginate={'per_page': 25}).configure(memory_table)
    else:
        register_filter = None
        memory_table = None
        register_table = None
        injection_table = tables.hw_injection(injections)
    RequestConfig(request, paginate=False).configure(result_table)
    RequestConfig(request, paginate=False).configure(event_table)
    RequestConfig(request, paginate=False).configure(injection_table)
    return render(request, 'result.html', {
        'campaign': campaign, 'event_table': event_table,
        'filter': register_filter, 'injection_table': injection_table,
        'memory_table': memory_table, 'navigation_items': navigation_items_,
        'output_image': output_image, 'page_items': page_items,
        'register_table': register_table, 'result': result,
        'result_table': result_table})


def output(request, campaign_id, result_id):
    campaign = models.campaign.objects.get(id=campaign_id)
    if result_id == '0':
        output_file = ('campaign-data/'+campaign_id+'/'
                       'gold_'+campaign.output_file)
    else:
        output_file = ('campaign-data/'+campaign_id+'/results/' +
                       result_id+'/'+campaign.output_file)
    if exists(output_file):
        return HttpResponse(open(output_file, 'rb').read(),
                            content_type=guess_type(output_file))
    else:
        return HttpResponse()
