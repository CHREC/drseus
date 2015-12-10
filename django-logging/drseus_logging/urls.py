"""
drseus_logging URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
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
    url(r'^(?P<campaign_number>[0-9]+)/result/(?P<iteration>[0-9]+)/$',
        result_page),
    url(r'^output-images/(?P<campaign_number>[0-9]+)/(?P<iteration>[0-9]+)$',
        output_image)
]
