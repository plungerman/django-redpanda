# -*- coding: utf-8 -*-

"""Admin classes for data models."""

from django.contrib import admin
from django.db import models
from django.forms import CheckboxSelectMultiple
from django.utils.safestring import mark_safe

from redpanda.core.models import GenericChoice
from redpanda.core.models import HealthCheck


class GenericChoiceAdmin(admin.ModelAdmin):
    """GenericChoice admin class."""

    list_display = ('name', 'value', 'rank', 'active', 'admin')
    list_editable = ('active', 'admin')
    list_per_page = 500
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    ordering = ('name',)


class HealthCheckAdmin(admin.ModelAdmin):
    """Health Check admin class."""

    list_display = (
        'created_by',
        'created_at',
        'positive',
        'negative',
        'temperature',
        'cough',
        'short_breath',
        'loss_taste_smell',
        'sore_throat',
        'congestion',
        'fatigue',
        'body_aches',
        'headache',
        'nausea',
        'diarrhea',
        'quarantine',
        'notification',
    )
    list_per_page = 500
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_by',)
    search_fields = (
        'user__username', 'user__last_name', 'user__first_name', 'user__id',
    )
    raw_id_fields = ('created_by',)

    class Media:
        """Static files like javascript and style sheets."""

        js = [
            '/static/redpanda/js/foobar.js',
        ]

admin.site.register(GenericChoice, GenericChoiceAdmin)
admin.site.register(HealthCheck, HealthCheckAdmin)
