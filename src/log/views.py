"""
Copyright (c) 2018 NSF Center for Space, High-performance, and Resilient Computing (SHREC)
University of Pittsburgh. All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided
that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS AS IS AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGE.
"""

from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect, render
from django_tables2 import RequestConfig
from io import BytesIO
from mimetypes import guess_type
from os.path import exists
from progressbar import ProgressBar
from progressbar.widgets import Bar, Percentage, SimpleProgress, Timer
from subprocess import Popen
from shutil import rmtree
from sys import argv
from tarfile import open as open_tar
from tarfile import TarInfo
from tempfile import TemporaryFile
from time import perf_counter

from . import filters
from . import models
from . import tables
from .charts.json import (campaigns_chart, injections_charts, results_charts,
                          target_bits_chart)

navigation_items = (('All Campaigns', '/', 'campaigns', 'home'),
                    ('All Results', '/results', 'results', 'list'),
                    ('All Events', '/events', 'events', 'flag'),
                    ('All Injections', '/injections', 'injections',
                     'crosshairs'),
                    ('All Charts', '/category_charts', 'charts', 'bar-chart'))

campaign_items = (('Campaign Information', 'info', 'info', 'info'),
                  ('Campaign Results', 'results', 'results', 'list'),
                  ('Campaign Events', 'events', 'events', 'flag'),
                  ('Campaign Injections', 'injections', 'injections',
                   'crosshairs'),
                  ('Campaign Charts', 'category_charts', 'charts', 'bar-chart'))

table_length = 50


def campaigns_page(request):
    campaign = models.campaign.objects.all()
    campaign_table = tables.campaigns(campaign)
    chart_data, chart_list = campaigns_chart(models.result.objects.all())
    chart_list = sorted(chart_list, key=lambda x: x['order'])
    RequestConfig(request).configure(campaign_table)
    return render(request, 'campaigns.html', {
        'campaign_table': campaign_table,
        'chart_data': chart_data,
        'chart_list': chart_list,
        'navigation_items': navigation_items})


def campaign_page(request, campaign_id):
    campaign = models.campaign.objects.get(id=campaign_id)
    chart_data = target_bits_chart(campaign)
    if campaign.output_file:
        output_file = 'campaign-data/{}/gold/{}'.format(campaign_id,
                                                        campaign.output_file)
        output_file = \
            exists(output_file) and guess_type(output_file)[0] is not None
    else:
        output_file = False
    campaign_table = tables.campaign(models.campaign.objects.filter(
        id=campaign_id))
    event_table = tables.event(campaign.event_set.all())
    if request.method == 'POST' and 'save' in request.POST:
        campaign.description = request.POST['description']
        campaign.save()
    RequestConfig(request, paginate=False).configure(campaign_table)
    RequestConfig(request, paginate=False).configure(event_table)
    return render(request, 'campaign.html', {
        'campaign': campaign,
        'campaign_items': campaign_items,
        'campaign_table': campaign_table,
        'chart_data': chart_data,
        'event_table': event_table,
        'navigation_items': navigation_items,
        'output_file': output_file})


def category_charts_page(request, campaign_id=None):
    return charts_page(request, campaign_id, True)


def charts_page(request, campaign_id=None, group_categories=False):
    if campaign_id is not None:
        campaign = models.campaign.objects.get(id=campaign_id)
        campaign_items_ = campaign_items
        results = campaign.result_set.all()
    else:
        campaign = None
        campaign_items_ = None
        results = models.result.objects.all()
    result_filter = filters.result(request.GET, queryset=results)
    error_title = None
    error_message = None
    if not result_filter.qs.count() and results.count():
        error_title = 'Filter Error'
        error_message = 'Filter did not return any results and was ignored.'
        result_filter = filters.result(None, queryset=results)
    else:
        results = result_filter.qs
    if results.count() > 0:
        chart_data, chart_list = results_charts(results, group_categories)
        chart_list = sorted(chart_list, key=lambda x: x['order'])
    else:
        chart_data = None
        chart_list = None
    return render(request, 'charts.html', {
        'campaign': campaign,
        'campaign_items': campaign_items_,
        'categories': group_categories,
        'chart_data': chart_data,
        'chart_list': chart_list,
        'error_message': error_message,
        'error_title': error_title,
        'filter': result_filter,
        'filter_tabs': True,
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
    error_title = None
    error_message = None
    if not event_filter.qs.count() and events.count():
        error_title = 'Filter Error'
        error_message = 'Filter did not return any events and was ignored.'
        event_filter = filters.event(None, queryset=events)
    else:
        events = event_filter.qs
    event_table = tables.events(events)
    RequestConfig(
        request, paginate={'per_page': table_length}).configure(event_table)
    return render(request, 'events.html', {
        'campaign': campaign,
        'campaign_items': campaign_items_,
        'error_message': error_message,
        'error_title': error_title,
        'event_count': '{:,}'.format(events.count()),
        'event_table': event_table,
        'filter': event_filter,
        'navigation_items': navigation_items})


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
    error_title = None
    error_message = None
    if not injection_filter.qs.count() and injections.count():
        error_title = 'Filter Error'
        error_message = 'Filter did not return any injections and was ignored.'
        injection_filter = filters.injection(None, queryset=injections)
    injections = injection_filter.qs

    # print('filtering for failed registers...')
    # failed_registers = []
    # all_regs = injections.values_list('register', flat=True).distinct()
    # progress_bar = ProgressBar(max_value=all_regs.count(), widgets=[
    #     Percentage(), ' (', SimpleProgress(format='%(value)d/%(max_value)d'),
    #     ') ', Bar(), ' ', Timer()])
    # for count, register in enumerate(all_regs, start=1):
    #     progress_bar.update(count)
    #     reg_injections = injections.filter(register=register)
    #     if reg_injections.filter(success=True).count():
    #         continue
    #     failed_bits = reg_injections.values_list('bit', flat=True).distinct()
    #     if len(failed_bits) != max(failed_bits)-1:
    #         continue
    #     failed_registers.append(register)
    # print()
    # injections = injections.filter(register__in=failed_registers)

    if injections.count() > 0:
        chart_data, chart_list = injections_charts(injections)
        chart_list = sorted(chart_list, key=lambda x: x['order'])
    else:
        chart_data = None
        chart_list = None
    injection_table = tables.injections(injections)
    RequestConfig(
        request, paginate={'per_page': table_length}).configure(injection_table)
    return render(request, 'injections.html', {
        'campaign': campaign,
        'campaign_items': campaign_items_,
        'chart_data': chart_data,
        'chart_list': chart_list,
        'error_message': error_message,
        'error_title': error_title,
        'filter': injection_filter,
        'injection_count': '{:,}'.format(injections.count()),
        'injection_table': injection_table,
        'navigation_items': navigation_items})


def results_page(request, campaign_id=None):
    error_title = None
    error_message = None
    result_filter = None
    if campaign_id is not None:
        campaign = models.campaign.objects.get(id=campaign_id)
    else:
        campaign = None
    if request.method == 'GET' and 'view_output' in request.GET and \
            'view_all' not in request.GET and 'select_box' in request.GET:
        result_ids = map(int, dict(request.GET)['select_box'])
        results = models.result.objects.filter(
            id__in=result_ids).order_by('-id')
    else:
        if campaign_id is not None:
            campaign_items_ = campaign_items
            output_file = 'campaign-data/{}/gold/{}'.format(
                campaign_id, campaign.output_file)
            if exists(output_file) and guess_type(output_file)[0] is not None:
                output_file = True
            else:
                output_file = False
            results = campaign.result_set.all()
        else:
            campaign_items_ = None
            output_file = True
            results = models.result.objects.all()
        result_filter = filters.result(request.GET, queryset=results)
        if not result_filter.qs.count() and results.count():
            error_title = 'Filter Error'
            error_message = 'Filter did not return any results and was ignored.'
            result_filter = filters.result(None, queryset=results)
        else:
            results = result_filter.qs.order_by('-id')
    if request.method == 'GET' and 'view_output' in request.GET:
        if 'view_dut_output' in request.GET:
            if 'view_download' in request.GET:
                temp_file = TemporaryFile()
                start = perf_counter()
                with open_tar(fileobj=temp_file, mode='w:gz') as archive:
                    for result in results:
                        with BytesIO(result.dut_output.encode('utf-8')) as \
                                byte_file:
                            info = TarInfo('{}_dut_output.txt'.format(
                                result.id))
                            info.size = len(result.dut_output)
                            archive.addfile(info, byte_file)
                print('archive created', round(perf_counter()-start, 2),
                      'seconds')
                response = FileResponse(
                    temp_file, content_type='application/x-compressed')
                response['Content-Disposition'] = \
                    'attachment; filename=dut_outputs.tar.gz'
                response['Content-Length'] = temp_file.tell()
                temp_file.seek(0)
                return response
            else:
                return render(request, 'output.html', {
                    'campaign': campaign,
                    'campaign_items': campaign_items if campaign else None,
                    'navigation_items': navigation_items,
                    'results': results,
                    'type': 'dut_output'})
        elif 'view_aux_output' in request.GET:
            if 'view_download' in request.GET:
                temp_file = TemporaryFile()
                start = perf_counter()
                with open_tar(fileobj=temp_file, mode='w:gz') as archive:
                    for result in results:
                        with BytesIO(result.aux_output.encode('utf-8')) as \
                                byte_file:
                            info = TarInfo('{}_aux_output.txt'.format(
                                result.id))
                            info.size = len(result.aux_output)
                            archive.addfile(info, byte_file)
                print('archive created', round(perf_counter()-start, 2),
                      'seconds')
                response = FileResponse(
                    temp_file, content_type='application/x-compressed')
                response['Content-Disposition'] = \
                    'attachment; filename=aux_outputs.tar.gz'
                response['Content-Length'] = temp_file.tell()
                temp_file.seek(0)
                return response
            else:
                return render(request, 'output.html', {
                    'campaign': campaign,
                    'campaign_items': campaign_items if campaign else None,
                    'navigation_items': navigation_items,
                    'results': results,
                    'type': 'aux_output'})
        elif 'view_debugger_output' in request.GET:
            if 'view_download' in request.GET:
                temp_file = TemporaryFile()
                start = perf_counter()
                with open_tar(fileobj=temp_file, mode='w:gz') as archive:
                    for result in results:
                        with BytesIO(
                                result.debugger_output.encode('utf-8')) as \
                                byte_file:
                            info = TarInfo('{}_debugger_output.txt'.format(
                                result.id))
                            info.size = len(result.debugger_output)
                            archive.addfile(info, byte_file)
                print('archive created', round(perf_counter()-start, 2),
                      'seconds')
                response = FileResponse(
                    temp_file, content_type='application/x-compressed')
                response['Content-Disposition'] = \
                    'attachment; filename=debugger_outputs.tar.gz'
                response['Content-Length'] = temp_file.tell()
                temp_file.seek(0)
                return response
            else:
                return render(request, 'output.html', {
                    'campaign': campaign,
                    'campaign_items': campaign_items if campaign else None,
                    'navigation_items': navigation_items,
                    'results': results,
                    'type': 'debugger_output'})
        elif 'view_output_file' in request.GET:
            result_ids = []
            for result in results:
                if exists('campaign-data/{}/results/{}/{}'.format(
                        result.campaign_id, result.id,
                        result.campaign.output_file)):
                    result_ids.append(result.id)
            results = models.result.objects.filter(
                id__in=result_ids).order_by('-id')
            if 'view_download' in request.GET:
                temp_file = TemporaryFile()
                start = perf_counter()
                with open_tar(fileobj=temp_file, mode='w:gz') as archive:
                    for result in results:
                        archive.add(
                            'campaign-data/{}/results/{}/{}'.format(
                                result.campaign_id, result.id,
                                result.campaign.output_file),
                            '{}_{}'.format(
                                result.id, result.campaign.output_file))
                print('archive created', round(perf_counter()-start, 2),
                      'seconds')
                response = FileResponse(
                    temp_file, content_type='application/x-compressed')
                response['Content-Disposition'] = \
                    'attachment; filename=output_files.tar.gz'
                response['Content-Length'] = temp_file.tell()
                temp_file.seek(0)
                return response
            else:
                return render(request, 'output.html', {
                    'campaign': campaign,
                    'campaign_items': campaign_items if campaign else None,
                    'navigation_items': navigation_items,
                    'results': results,
                    'type': 'output_file'})
        elif 'view_log_file' in request.GET:
            if 'view_download' in request.GET:
                temp_file = TemporaryFile()
                start = perf_counter()
                with open_tar(fileobj=temp_file, mode='w:gz') as archive:
                    for result in results:
                        for log_file in result.campaign.log_files:
                            archive.add(
                                'campaign-data/{}/results/{}/{}'.format(
                                    result.campaign_id, result.id, log_file),
                                '{}_{}'.format(result.id, log_file))
                print('archive created', round(perf_counter()-start, 2),
                      'seconds')
                response = FileResponse(
                    temp_file, content_type='application/x-compressed')
                response['Content-Disposition'] = \
                    'attachment; filename=log_files.tar.gz'
                response['Content-Length'] = temp_file.tell()
                temp_file.seek(0)
                return response
            else:
                return render(request, 'output.html', {
                    'campaign': campaign,
                    'campaign_items': campaign_items if campaign else None,
                    'navigation_items': navigation_items,
                    'results': results,
                    'type': 'log_file'})
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
            results_to_delete = models.result.objects.filter(id__in=result_ids)
            for result in results_to_delete:
                if exists('campaign-data/{}/results/{}'.format(
                        result.campaign_id, result.id)):
                    rmtree('campaign-data/{}/results/{}'.format(
                        result.campaign_id, result.id))
            results_to_delete.delete()
        elif 'delete_all' in request.POST:
            for result in results:
                if exists('campaign-data/{}/results/{}'.format(
                        result.campaign_id, result.id)):
                    rmtree('campaign-data/{}/results/{}'.format(
                        result.campaign_id, result.id))
            results.delete()
            if campaign_id:
                return redirect('/campaign/{}/results'.format(campaign_id))
            else:
                return redirect('/results')
    if campaign_id is None:
        result_table = tables.all_results(results)
    else:
        result_table = tables.results(results)
    RequestConfig(
        request, paginate={'per_page': table_length}).configure(result_table)
    return render(request, 'results.html', {
        'campaign': campaign,
        'campaign_items': campaign_items_,
        'error_message': error_message,
        'error_title': error_title,
        'filter': result_filter,
        'filter_tabs': True,
        'navigation_items': navigation_items,
        'output_file': output_file,
        'result_count': '{:,}'.format(results.count()),
        'result_table': result_table})


def result_page(request, result_id):
    result = models.result.objects.get(id=result_id)
    if request.method == 'GET':
        if 'get_dut_output' in request.GET:
            response = HttpResponse(result.dut_output,
                                    content_type='text/plain')
            response['Content-Disposition'] = \
                'attachment; filename="{}_dut_output.txt"'.format(
                    result_id)
            return response
        elif 'get_debugger_output' in request.GET:
            response = HttpResponse(result.debugger_output,
                                    content_type='text/plain')
            response['Content-Disposition'] = \
                'attachment; filename="{}_debugger_output.txt"'.format(
                    result_id)
            return response
        elif 'get_aux_output' in request.GET:
            response = HttpResponse(result.aux_output,
                                    content_type='text/plain')
            response['Content-Disposition'] = \
                'attachment; filename="{}_aux_output.txt"'.format(
                    result_id)
            return response
        elif 'get_output_file' in request.GET:
            response = get_file(result.campaign.output_file, result_id)
            response['Content-Disposition'] = \
                'attachment; filename={}_{}'.format(
                    result_id, result.campaign.output_file)
            return response
        elif 'get_log_file' in request.GET:
            temp_file = TemporaryFile()
            with open_tar(fileobj=temp_file, mode='w:gz') as archive:
                for log_file in result.campaign.log_files:
                    archive.add(
                        'campaign-data/{}/results/{}/{}'.format(
                            result.campaign_id, result.id, log_file),
                        '{}_{}'.format(result.id, log_file))
            response = FileResponse(
                temp_file, content_type='application/x-compressed')
            response['Content-Disposition'] = \
                'attachment; filename={}_log_files.tar.gz'.format(result.id)
            response['Content-Length'] = temp_file.tell()
            temp_file.seek(0)
            return response
    campaign_items_ = [(
        item[0], '/campaign/{}/{}'.format(result.campaign_id, item[1]), item[2],
        item[3]) for item in campaign_items]
    if result.campaign.output_file:
        output_file = 'campaign-data/{}/results/{}/{}'.format(
            result.campaign_id, result_id, result.campaign.output_file)
        output_file = \
            exists(output_file) and guess_type(output_file)[0] is not None
    else:
        output_file = False
    result_table = tables.result(models.result.objects.filter(id=result_id))
    events = result.event_set.all()
    event_table = tables.event(events)
    if request.method == 'POST' and 'launch' in request.POST:
        Popen([argv[0], '--campaign_id', str(result.campaign_id),
               'regenerate', result_id])
    if request.method == 'POST' and 'save' in request.POST:
        result.outcome = request.POST['outcome']
        result.outcome_category = request.POST['outcome_category']
        result.save()
    elif request.method == 'POST' and 'delete' in request.POST:
        if exists('campaign-data/{}/results/{}'.format(
                result.campaign_id, result.id)):
            rmtree('campaign-data/{}/results/{}'.format(
                result.campaign_id, result.id))
        result.delete()
        return HttpResponse('Result deleted')
    injections = result.injection_set.all()
    if result.campaign.simics:
        if injections.count():
            injection_table = tables.injection(injections)
        else:
            injection_table = None
        register_diffs = result.simics_register_diff_set.all()
        register_filter = filters.simics_register_diff(
            request.GET, queryset=register_diffs)
        register_diff_count = register_filter.qs.count()
        register_table = tables.simics_register_diff(register_filter.qs)
        RequestConfig(
            request,
            paginate={'per_page': table_length}).configure(register_table)
        memory_diffs = result.simics_memory_diff_set.all()
        memory_diff_count = memory_diffs.count()
        memory_table = tables.simics_memory_diff(memory_diffs)
        RequestConfig(
            request,
            paginate={'per_page': table_length}).configure(memory_table)
    else:
        register_filter = None
        memory_diff_count = 0
        memory_table = None
        register_diff_count = 0
        register_table = None
        if injections.count():
            injection_table = tables.injection(injections)
        else:
            injection_table = None
    RequestConfig(request, paginate=False).configure(result_table)
    RequestConfig(request, paginate=False).configure(event_table)
    if injection_table:
        RequestConfig(request, paginate=False).configure(injection_table)
    return render(request, 'result.html', {
        'campaign_items': campaign_items_,
        'event_count':  '{:,}'.format(events.count()),
        'event_table': event_table,
        'filter': register_filter,
        'injection_table': injection_table,
        'memory_diff_count': '{:,}'.format(memory_diff_count),
        'memory_table': memory_table,
        'navigation_items': navigation_items,
        'output_file': output_file,
        'register_diff_count': '{:,}'.format(register_diff_count),
        'register_table': register_table,
        'result': result,
        'result_table': result_table})


def get_file(request, filename, result_id=None, campaign_id=None):
    if result_id is not None:
        result = models.result.objects.get(id=result_id)
        file_ = 'campaign-data/{}/results/{}/{}'.format(
            result.campaign_id, result_id, filename.split('/')[-1])
    elif campaign_id is not None:
        file_ = 'campaign-data/{}/gold/{}'.format(
            campaign_id, filename.split('/')[-1])
    if exists(file_):
        return FileResponse(
            open(file_, 'rb'), content_type=guess_type(file_))
    elif exists(file_.split('/')[-1]):
        return FileResponse(
            open(file_.split('/')[-1], 'rb'), content_type=guess_type(file_))
    else:
        return HttpResponse('File not found')


def update_filter(request):
    filters.update_choices()
    return redirect(request.POST['redirect'])
