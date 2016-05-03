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
        views.get_file)
]
