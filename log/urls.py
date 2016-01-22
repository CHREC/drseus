from django.conf.urls import url

from .views import (campaigns_page, campaign_page, category_charts_page,
                    charts_page, events_page, results_page, result_page, output)

urlpatterns = [
    url(r'^$', campaigns_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/info$', campaign_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/category_charts$',
        category_charts_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/outcome_charts$', charts_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/results$', results_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/events$', events_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/result/(?P<result_id>[0-9]+)$',
        result_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/output/(?P<result_id>[0-9]+)$',
        output)
]
