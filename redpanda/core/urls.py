# -*- coding: utf-8 -*-

"""URLs for all views."""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include
from django.urls import path
from django.urls import reverse_lazy
from django.views.generic import RedirectView
from django.views.generic import TemplateView
from djauth.views import loggedout
from redpanda.core import views
from redpanda.dashboard import views as dash_views

admin.autodiscover()

handler404 = 'djtools.views.errors.four_oh_four_error'
handler500 = 'djtools.views.errors.server_error'


urlpatterns = [
    # auth
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(),
        {'template_name': 'registration/login.html'},
        name='auth_login',
    ),
    path(
        'accounts/logout/',
        auth_views.LogoutView.as_view(),
        {'next_page': reverse_lazy('auth_loggedout')},
        name='auth_logout',
    ),
    path(
        'accounts/loggedout/',
        loggedout,
        {'template_name': 'registration/logged_out.html'},
        name='auth_loggedout',
    ),
    path('accounts/', RedirectView.as_view(url=reverse_lazy('auth_login'))),
    path(
        'denied/',
        TemplateView.as_view(template_name='denied.html'),
        name='access_denied',
    ),
    # django admin and loginas
    path('rocinante/', include('loginas.urls')),
    path('rocinante/', admin.site.urls),
    # admin honeypot
    path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
    # dashboard
    path('dashboard/', include('redpanda.dashboard.urls')),
    # clear cache via ajax post
    path('cache/<str:ctype>/clear/', views.clear_cache, name='clear_cache'),
    # short URLs
    path('lynx/', include('redpanda.lynx.urls')),
    # Smell Study Research
    path('research/', include('redpanda.research.urls')),
    # health check
    path('health-check/', views.health_check, name='health_check'),
    # vaccine verification
    path('vax/dashboard/', dash_views.vaccine, name='vax_dash'),
    path('vax/', views.vaccine, name='vaccine'),
    # home
    path('', views.vaccine, name='home'),
]
