from django.conf.urls import url
from .views import (campaigns_page, campaign_page, edit_page,
                    category_charts_page, outcome_charts_page, results_page,
                    result_page, output_image)

urlpatterns = [
    url(r'^$', campaigns_page),
    url(r'^(?P<campaign_number>[0-9]+)/campaign/$', campaign_page),
    url(r'^(?P<campaign_number>[0-9]+)/edit/$', edit_page),
    url(r'^(?P<campaign_number>[0-9]+)/category_charts/$',
        category_charts_page),
    url(r'^(?P<campaign_number>[0-9]+)/outcome_charts/$', outcome_charts_page),
    url(r'^(?P<campaign_number>[0-9]+)/results/$', results_page),
    url(r'^(?P<campaign_number>[0-9]+)/result/(?P<result_id>[0-9]+)/$',
        result_page),
    url(r'^output-images/(?P<campaign_number>[0-9]+)/(?P<result_id>[0-9]+)$',
        output_image)
]
