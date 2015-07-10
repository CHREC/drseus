"""drseus_logging URL Configuration

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
from django.conf.urls import patterns

charts_and_tables = [
    (r'', 'campaign_info', 'Campaign Information'),
    (r'charts/', 'charts', 'Injection Charts'),
    (r'table/', 'tables', 'Results Table'),
]

sidebar_group1 = [
    (r'../' + myurl, title) for (myurl, view, title) in charts_and_tables
]

sidebar_groups = [("Navigation", sidebar_group1)]

charts_and_tables.append(
    (r'injection/(?P<injection_number>[0-9]+)/', 'injection_result',
     'Injection Result'))
charts_and_tables.append(
    (r'iteration/(?P<iteration>[0-9]+)/', 'iteration_result',
     'Iteration Result')
)

chart_pattern_tuples = [
    (
        r'^' + myurl + r'$',
        view,
        {
            'title': title,
            'sidebar_items': sidebar_groups
        }
    ) for (myurl, view, title) in charts_and_tables
]

urlpatterns = patterns('drseus_logging.views', *chart_pattern_tuples)
