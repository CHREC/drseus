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

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.campaigns_page),
    url(r'^results$', views.results_page),
    url(r'^events$', views.events_page),
    url(r'^injections$', views.injections_page),
    url(r'^category_charts$', views.category_charts_page),
    url(r'^outcome_charts$', views.charts_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/info$', views.campaign_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/results$', views.results_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/events$', views.events_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/injections$',
        views.injections_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/category_charts$',
        views.category_charts_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/outcome_charts$',
        views.charts_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/file/(?P<filename>.+)$',
        views.get_file),
    url(r'^result/(?P<result_id>[0-9]+)$', views.result_page),
    url(r'^result/(?P<result_id>[0-9]+)/file/(?P<filename>.+)$',
        views.get_file),
    url(r'^update_filter$', views.update_filter)
]
