from django.conf.urls import url

import views

urlpatterns = [
    url(r'^$', views.campaigns_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/info$', views.campaign_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/category_charts$',
        views.category_charts_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/outcome_charts$',
        views.outcome_charts_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/results$', views.results_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/result/(?P<result_id>[0-9]+)$',
        views.result_page),
    url(r'^campaign/(?P<campaign_id>[0-9]+)/output/(?P<result_id>[0-9]+)$',
        views.output)
]
