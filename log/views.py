from django.http import HttpResponse
from django.shortcuts import redirect, render
from django_tables2 import RequestConfig
from imghdr import what
from mimetypes import guess_type
from subprocess import Popen
import os

from .charts import json_campaign, json_campaigns, json_charts
from .filters import (injection_filter, simics_register_diff_filter)
from .forms import edit_form, result_form
from .models import (campaign, result, injection, simics_register_diff,
                     simics_memory_diff)
from .tables import (campaign_table, campaigns_table, result_table,
                     results_table, hw_injection_table, simics_injection_table,
                     simics_register_diff_table, simics_memory_diff_table)

navigation_items = (('Campaign Information', '../campaign'),
                    ('Charts (Grouped by Category)', '../category_charts/'),
                    ('Charts (Grouped by Outcome)', '../outcome_charts/'),
                    ('Results Table', '../results/'),
                    ('Edit Categories and Outcomes', '../edit/'))


def category_charts_page(request, campaign_number):
    return charts_page(request, campaign_number, True)


def outcome_charts_page(request, campaign_number):
    return charts_page(request, campaign_number, False)


def charts_page(request, campaign_number, group_categories):
    campaign_data = campaign.objects.get(id=campaign_number)
    page_items = [('Results Overview', 'outcomes'),
                  ('Injections By Target', 'targets')]
    page_items.extend([('Injections By Register', 'registers'),
                       ('Injections By Bit', 'bits')])
    if campaign_data.use_simics:
        page_items.extend([('Injections By TLB Entry', 'tlbs'),
                          ('Injections By TLB Field', 'fields')])
    page_items.extend([('Injections Over Time', 'times'),
                       ('Results By Injection Count', 'counts')])
    injection_objects = injection.objects.filter(
        result__campaign_id=campaign_number)
    filter_ = injection_filter(request.GET, queryset=injection_objects,
                               campaign=campaign_number)
    if filter_.qs.count() > 0:
        chart_array = json_charts(
            filter_.qs.exclude(result__outcome_category='Incomplete'),
            campaign_data, group_categories)
    else:
        chart_array = None
    return render(request, 'charts.html', {'campaign_data': campaign_data,
                                           'chart_array': chart_array,
                                           'filter': filter_,
                                           'navigation_items':
                                               navigation_items,
                                           'page_items': page_items})


def campaign_page(request, campaign_number):
    campaign_data = campaign.objects.get(id=campaign_number)
    chart_array = json_campaign(campaign_data)
    page_items = [('Campaign Data', 'campaign_data'),
                  ('Injection Targets', 'device_targets')]
    chart_array = json_campaign(campaign_data)
    output_file = ('campaign-data/'+str(campaign_number) +
                   '/gold_'+campaign_data.output_file)
    if os.path.exists(output_file) and what(output_file) is not None:
        output_image = True
        page_items.append(('Output Image', 'output_image'))
    else:
        output_image = False
    page_items.append(('DUT Output', 'dut_output'))
    if campaign_data.use_aux:
        page_items.append(('AUX Output', 'aux_output'))
    page_items.append(('Debugger Output', 'debugger_output'))
    table = campaign_table(campaign.objects.filter(id=campaign_number))
    RequestConfig(request, paginate=False).configure(table)
    return render(request, 'campaign.html', {'campaign_data': campaign_data,
                                             'chart_array': chart_array,
                                             'navigation_items':
                                                 navigation_items,
                                             'output_image': output_image,
                                             'page_items': page_items,
                                             'table': table})


def edit_page(request, campaign_number):
    if request.method == 'POST':
        form = edit_form(request.POST, campaign=campaign_number)
        if form.is_valid():
            if 'edit_outcome' in request.POST:
                if form.cleaned_data['new_outcome']:
                    result.objects.filter(
                        campaign_id=campaign_number,
                        outcome=form.cleaned_data['outcome']
                    ).values('outcome').update(
                        outcome=form.cleaned_data['new_outcome'])
            elif 'edit_outcome_category' in request.POST:
                if form.cleaned_data['new_outcome_category']:
                    result.objects.filter(
                        campaign_id=campaign_number,
                        outcome_category=form.cleaned_data['outcome_category']
                    ).values('outcome_category').update(
                        outcome_category=form.cleaned_data[
                            'new_outcome_category'])
            elif 'delete_outcome' in request.POST:
                if form.cleaned_data['outcome']:
                    injection.objects.filter(
                        result__campaign_id=campaign_number,
                        result__outcome=form.cleaned_data['outcome']).delete()
                    simics_memory_diff.objects.filter(
                        result__campaign_id=campaign_number,
                        result__outcome=form.cleaned_data['outcome']).delete()
                    simics_register_diff.objects.filter(
                        result__campaign_id=campaign_number,
                        result__outcome=form.cleaned_data['outcome']).delete()
                    result.objects.filter(
                        campaign_id=campaign_number,
                        outcome=form.cleaned_data['outcome']).delete()
            elif 'delete_outcome_category' in request.POST:
                if form.cleaned_data['outcome_category']:
                    injection.objects.filter(
                        result__campaign_id=campaign_number,
                        result__outcome_category=form.cleaned_data[
                            'outcome_category']).delete()
                    simics_memory_diff.objects.filter(
                        result__campaign_id=campaign_number,
                        result__outcome_category=form.cleaned_data[
                            'outcome_category']).delete()
                    simics_register_diff.objects.filter(
                        result__campaign_id=campaign_number,
                        result__outcome_category=form.cleaned_data[
                            'outcome_category']).delete()
                    result.objects.filter(
                        campaign_id=campaign_number,
                        outcome_category=form.cleaned_data[
                            'outcome_category']).delete()
    form = edit_form(campaign=campaign_number)
    return render(request, 'edit.html', {'form': form,
                                         'navigation_items': navigation_items})


def campaigns_page(request):
    campaigns = campaign.objects.all()
    if len(campaigns) == 1:
        return redirect('/'+str(campaigns[0].id)+'/results/')
    table = campaigns_table(campaigns)
    chart_array = json_campaigns(result.objects.all())
    RequestConfig(request).configure(table)
    return render(request, 'campaigns.html', {'chart_array': chart_array,
                                              'table': table})


def results_page(request, campaign_number):
    campaign_data = campaign.objects.get(id=campaign_number)
    injection_objects = injection.objects.filter(
        result__campaign_id=campaign_number)
    filter_ = injection_filter(request.GET, queryset=injection_objects,
                               campaign=campaign_number)
    result_ids = filter_.qs.values('result_id').distinct()
    result_objects = result.objects.filter(id__in=result_ids)
    if request.method == 'POST':
        if 'delete' in request.POST and 'select_box' in request.POST:
            result_ids = [int(result_id) for result_id
                          in dict(request.POST)['select_box']]
            injection.objects.filter(result_id__in=result_ids).delete()
            simics_memory_diff.objects.filter(result_id__in=result_ids).delete()
            simics_register_diff.objects.filter(
                result_id__in=result_ids).delete()
            result.objects.filter(id__in=result_ids).delete()
        elif 'delete_all' in request.POST:
            injection.objects.filter(result_id__in=result_ids).delete()
            simics_memory_diff.objects.filter(result_id__in=result_ids).delete()
            simics_register_diff.objects.filter(
                result_id__in=result_ids).delete()
            result.objects.filter(id__in=result_ids).delete()
            return redirect('/'+str(campaign_number)+'/results/')
        elif (('view_output' in request.POST or
               'view_output_image' in request.POST)
              and 'select_box' in request.POST):
            result_ids = []
            page_items = []
            for result_id in dict(request.POST)['select_box']:
                result_ids.append(int(result_id))
                page_items.append(('Result ID '+result_id, result_id))
            results = result.objects.filter(id__in=result_ids)
            image = 'view_output_image' in request.POST
            return render(request, 'output.html', {'campaign': campaign_number,
                                                   'image': image,
                                                   'navigation_items':
                                                       navigation_items,
                                                   'page_items': page_items,
                                                   'results': results})
        elif ('view_output_all' in request.POST or
              'view_output_image_all' in request.POST):
            page_items = [('Result ID '+str(result_id), result_id) for result_id
                          in result_objects.values_list('id', flat=True)]
            image = 'view_output_image_all' in request.POST
            return render(request, 'output.html', {'campaign': campaign_number,
                                                   'image': image,
                                                   'navigation_items':
                                                       navigation_items,
                                                   'page_items': page_items,
                                                   'results': result_objects})
        elif 'new_outcome_category' in request.POST:
            result_objects.values('outcome_category').update(
                outcome_category=request.POST['new_outcome_category'])
        elif 'new_outcome' in request.POST:
            result_objects.values('outcome').update(
                outcome=request.POST['new_outcome'])
    table = results_table(result_objects)
    RequestConfig(request, paginate={'per_page': 100}).configure(table)
    return render(request, 'results.html', {'campaign_data': campaign_data,
                                            'filter': filter_,
                                            'navigation_items':
                                                navigation_items,
                                            'table': table})


def result_page(request, campaign_number, result_id):
    campaign_data = campaign.objects.get(id=campaign_number)
    navigation_items_ = [(item[0], '../'+item[1])
                         for item in navigation_items]
    page_items = [('Result', 'result'), ('Injections', 'injections')]
    output_file = ('campaign-data/'+campaign_number+'/results/'+result_id +
                   '/'+campaign_data.output_file)
    if os.path.exists(output_file) and what(output_file) is not None:
        output_image = True
        page_items.append(('Output Image', 'output_image'))
    else:
        output_image = False
    page_items.append(('DUT Output', 'dut_output'))
    if campaign_data.use_aux:
        page_items.append(('AUX Output', 'aux_output'))
    page_items.append(('Debugger Output', 'debugger_output'))
    if campaign_data.use_simics:
        page_items.extend([('Register Diffs', 'register_diffs'),
                           ('Memory Diffs', 'memory_diffs')])
    result_object = result.objects.get(id=result_id)
    table = result_table(result.objects.filter(id=result_id))  # TODO: use above
    if request.method == 'POST' and 'save' in request.POST:
        form = result_form(request.POST)
        if form.is_valid():
            if form.cleaned_data['outcome']:
                result_object.outcome = form.cleaned_data['outcome']
            if form.cleaned_data['outcome_category']:
                result_object.outcome_category = \
                    form.cleaned_data['outcome_category']
            result_object.save()
    else:
        form = result_form(
            initial={'outcome': result_object.outcome,
                     'outcome_category': result_object.outcome_category})
    if request.method == 'POST' and 'delete' in request.POST:
        injection.objects.filter(result_id=result_object.id).delete()
        simics_register_diff.objects.filter(result_id=result_object.id).delete()
        simics_memory_diff.objects.filter(result_id=result_object.id).delete()
        result_object.delete()
        return HttpResponse('Result deleted.')
    if request.method == 'GET' and request.GET.get('launch'):
        drseus = 'drseus.py'
        if not os.path.exists(drseus):
            drseus = 'drseus.sh'
        Popen(['./'+drseus, '--regenerate', result_id])
    injection_objects = \
        injection.objects.filter(result_id=result_id)
    if campaign_data.use_simics:
        injection_table = simics_injection_table(injection_objects)
        register_objects = simics_register_diff.objects.filter(
            result_id=result_id)
        register_filter = \
            simics_register_diff_filter(request.GET, queryset=register_objects,
                                        campaign=campaign_number)
        register_table = simics_register_diff_table(register_filter.qs)
        RequestConfig(request,
                      paginate={'per_page': 25}).configure(register_table)
        memory_objects = simics_memory_diff.objects.filter(result_id=result_id)
        memory_table = simics_memory_diff_table(memory_objects)
        RequestConfig(request,
                      paginate={'per_page': 25}).configure(memory_table)
    else:
        register_filter = None
        memory_table = None
        register_table = None
        injection_table = hw_injection_table(injection_objects)
    RequestConfig(request, paginate=False).configure(table)
    RequestConfig(request, paginate=False).configure(injection_table)
    return render(request, 'result.html', {'campaign_data': campaign_data,
                                           'filter': register_filter,
                                           'form': form,
                                           'injection_table': injection_table,
                                           'memory_table': memory_table,
                                           'navigation_items':
                                               navigation_items_,
                                           'output_image': output_image,
                                           'page_items': page_items,
                                           'register_table': register_table,
                                           'result': result_object,
                                           'table': table})


def output_image(request, campaign_number, result_id):
    campaign_data = campaign.objects.get(id=campaign_number)
    if result_id == '0':
        output_file = ('campaign-data/'+campaign_number+'/'
                       'gold_'+campaign_data.output_file)
    else:
        output_file = ('campaign-data/'+campaign_number+'/results/' +
                       result_id+'/'+campaign_data.output_file)
    if os.path.exists(output_file):
        return HttpResponse(open(output_file, 'rb').read(),
                            content_type=guess_type(output_file))
    else:
        return HttpResponse()
