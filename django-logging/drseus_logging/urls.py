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

chart_view_title = [
    (r'', 'table', 'Results Table'),
    (r'charts/register/', 'register_chart', 'Injections By Register Chart'),
    (r'charts/bit/', 'bit_chart', 'Injections By Bit Chart'),
]

sidebar = [
    (r'../' + myurl, title) for (myurl, view, title) in chart_view_title
]

sidebar_items = [("Navigation", sidebar)]

chart_pattern_tuples = [
    (
        r'^' + myurl + r'$',
        view,
        {
            'title': title,
            'sidebar_items': sidebar_items
        }
    ) for (myurl, view, title) in chart_view_title
]

# homepatterns = patterns('drseus_logging.views', (r'^$', 'table'), )
chartpatterns = patterns('drseus_logging.views', *chart_pattern_tuples)

urlpatterns = chartpatterns  # + homepatterns
