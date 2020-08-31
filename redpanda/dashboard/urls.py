# -*- coding: utf-8 -*-

"""URLs for all views."""

from django.urls import path

from redpanda.dashboard import views


urlpatterns = [
    path(
        'research/',
        views.research, name='dashboard_research'
    ),
    path('', views.home, name='dashboard'),
]
