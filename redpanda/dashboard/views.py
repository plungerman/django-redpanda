# -*- coding: utf-8 -*-

"""URLs for all views."""

import os

from datetime import datetime
from datetime import date
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.db.models.query import Q
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from djauth.decorators import portal_auth_required
from djimix.core.database import get_connection
from djimix.core.database import xsql
from redpanda.core.models import HealthCheck
from redpanda.core.utils import get_coach
from redpanda.research.models import Registration


def _get_dates(request):
    today = date.today()
    date_start = request.POST.get('date_start')
    if not date_start:
        date_start = today - timedelta(days=1)
    else:
        date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
    date_end = request.POST.get('date_end')
    if not date_end:
        date_end = today + timedelta(days=1)
    else:
        date_end = datetime.strptime(date_end, '%Y-%m-%d').date() + timedelta(days=1)

    return (date_start, date_end)


def _get_sports(request):
    sport = request.POST.get('sport', '666')
    sports = None
    sportsql = os.path.join(settings.BASE_DIR, 'sql/sports_all.sql')
    with open(sportsql) as incantation:
        with get_connection() as connection:
            sports = xsql(incantation.read(), connection).fetchall()
    # simple protection against sql injection
    for spor in sports:
        if spor[0] == sport:
            sport = spor[0]
            break
    return (sport, sports)


@portal_auth_required(
    session_var='REDPANDA_AUTH',
    redirect_url=reverse_lazy('access_denied'),
)
def home(request):
    """Dashboard home for administrators."""
    user = request.user
    perms = user.profile.get_perms()
    admins = perms.get(settings.ADMIN_GROUP)
    if not admins:
        response = HttpResponseRedirect(reverse_lazy('dashboard_managers'))
    else:
        group = request.POST.get('group')
        sport, sports = _get_sports(request)
        date_start, date_end = _get_dates(request)
        response = render(
            request,
            'dashboard/home.html',
            {
                'admins': admins,
                'group': group,
                'groups': settings.ALL_GROUPS,
                'sport': sport,
                'sports': sports,
                'date_start': date_start,
                'date_end': date_end - timedelta(days=1),
            },
        )
    return response


@csrf_exempt
@portal_auth_required(
    session_var='REDPANDA_AUTH',
    redirect_url=reverse_lazy('access_denied'),
    group=settings.ADMIN_GROUP
)
def home_ajax(request):
    """ajax response for dashboard home for admins."""
    user = request.user
    czechs = None
    post = request.POST
    # draw counter
    draw = int(post.get('draw', 0))
    # paging first record indicator.
    start = int(post.get('start', 0))
    # number of records that the table can display in the current draw
    length = int(post.get('length', 100))
    # page number, 1-based index
    page = int((start / length) + 1)
    # search box data
    search = post.get('search[value]')
    # order by
    order_by = '-created_at'
    order = post.get('order[0][column]')
    if order:
        order = int(order)
        # column names
        columns = HealthCheck.COLUMNS
        # direction
        dirx = post.get('order[0][dir]')
        col = columns.get(order)
        order_by = col if dirx == 'asc' else '-' + col
    date_start, date_end = _get_dates(request)
    group = request.POST.get('group', None)
    all_czechs = HealthCheck.objects.filter(
        created_at__range=(date_start, date_end)
    )
    if group:
        all_czechs = all_czechs.filter(
            created_by__groups__name=group
        )
    if search:
        czechs = all_czechs.filter(
            created_at__range=(date_start, date_end)
        ).filter(
            Q(created_by__last_name__icontains=search)|
            Q(created_by__first_name__icontains=search)|
            Q(created_by__id__icontains=search)
        )
    else:
        czechs = all_czechs.order_by(order_by)
    records_total = czechs.count()
    records_filtered = records_total
    paginator = Paginator(czechs, length)
    object_list = paginator.get_page(page).object_list
    data = []
    for czech in object_list:
        full_name = '{0}, {1}'.format(
            czech.created_by.last_name, czech.created_by.first_name,
        )
        try:
            vax = czech.created_by.profile.vaccine
        except Exception:
            vax = None
        if vax == 'Yes':
            vax = True
        data.append({
            'email': czech.created_by.email,
            'full_name': full_name,
            'vaccine': vax,
            'cid': czech.created_by.id,
            'created_at': czech.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'group': czech.group(),
            'tested_positive': czech.tested_positive,
            'tested_negative': czech.tested_negative,
            'tested_pending': czech.tested_pending,
            'negative': czech.negative,
            'temperature': czech.temperature,
            'cough': czech.cough,
            'short_breath': czech.short_breath,
            'loss_taste_smell': czech.loss_taste_smell,
            'sore_throat': czech.sore_throat,
            'congestion': czech.congestion,
            'fatigue': czech.fatigue,
            'body_aches': czech.body_aches,
            'headache': czech.headache,
            'nausea': czech.nausea,
            'diarrhea': czech.diarrhea,
            'quarantine': czech.quarantine,
        })

    return JsonResponse(
        {
            'draw': draw,
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': data,
        },
        safe=False,
    )


@portal_auth_required(
    session_var='REDPANDA_AUTH',
    redirect_url=reverse_lazy('access_denied'),
)
def managers(request):
    """Dashboard home for managers."""
    user = request.user
    perms = user.profile.get_perms()
    faculty = perms.get(settings.FACULTY_GROUP)
    athletics = perms.get(settings.ATHLETICS_GROUP)
    coach = get_coach(user.id)
    students = []
    if faculty or athletics or coach:
        date_start, date_end = _get_dates(request)
        sport, sports = _get_sports(request)
        date = settings.START_DATE
        if date.month < settings.SPORTS_MONTH:
            year = date.year
        else:
            year = date.year + 1
            if coach:
                year = date.year - 1
        if athletics:
            phile = os.path.join(
                settings.BASE_DIR, 'sql/students_sport.sql',
            )
        elif coach:
            phile = os.path.join(
                settings.BASE_DIR, 'sql/students_coach.sql',
            )
        else:
            phile = os.path.join(
                settings.BASE_DIR, 'sql/students_faculty.sql',
            )
        with open(phile) as incantation:
            sql = incantation.read()
            if athletics:
                sql = sql.replace('{YEAR}', str(year)).replace('{SPORT}', sport)
            elif coach:
                sql = sql.replace('{YEAR}', str(year)).replace('{CID}', str(user.id))
            else:
                sql = sql.replace(
                    '{YEAR}', str(year),
                ).replace('{CID}', str(user.id)).replace('{TERM}', settings.TERM)
        with get_connection() as connection:
            roster = xsql(sql, connection).fetchall()
        for ros in roster:
            students.append(
                {
                    'roster': ros,
                    'czechs': HealthCheck.objects.filter(
                        created_by__id=ros.id,
                    ).filter(created_at__range=(date_start, date_end)),
                },
            )
        return render(
            request,
            'dashboard/managers.html',
            {
                'athletics': athletics,
                'coach': coach,
                'faculty': faculty,
                'sport': sport,
                'sports': sports,
                'students': students,
                'date_start': date_start,
                'date_end': date_end - timedelta(days=1),
            },
        )
    else:
        return HttpResponseRedirect(reverse_lazy('home'))


@portal_auth_required(
    session_var='REDPANDA_AUTH',
    redirect_url=reverse_lazy('access_denied'),
)
def research(request):
    """Dashboard for smell study."""
    user = request.user
    perms = user.profile.get_perms()
    admins = perms.get(settings.ADMIN_GROUP)
    study = perms.get(settings.RESEARCH_GROUP)
    date_start, date_end = _get_dates(request)

    if admins or study:
        czechs = HealthCheck.objects.filter(
            created_at__range=(date_start, date_end)
        ).filter(
            created_by__profile__opt_in='Yes',
        ).order_by('-created_at')
        response =  render(
            request,
            'dashboard/research.html',
            {'czechs': czechs, 'research': study},
        )
    else:
        response = HttpResponseRedirect(reverse_lazy('home'))
    return response

@cache_page(60*60*24)
@portal_auth_required(
    session_var='REDPANDA_AUTH',
    redirect_url=reverse_lazy('access_denied'),
)
def vaccine(request):
    """Dashboard home for vaccine verification."""
    user = request.user
    perms = user.profile.get_perms()
    admins = perms.get(settings.ADMIN_GROUP)
    student_vax = perms.get(settings.STUDENT_VAX_DATA)
    if admins or student_vax:
        group = request.POST.get('group')
        profiles = cache.get('profiles_all')
        if not profiles:
            profiles = Registration.objects.filter(
                vaccine__in=['Yes', 'No'],
            ).order_by('user__last_name')
        cache.set('profiles_all', profiles)
        if student_vax:
            student_profiles = cache.get('profiles_students')
            if not student_profiles:
                student_profiles = profiles.filter(user__groups__name__in=[settings.STUDENT_GROUP])
            cache.set('profiles_students', student_profiles)
            profiles = student_profiles
        response = render(
            request,
            'dashboard/vaccine.html',
            {
                'profiles': profiles,
                'admins': admins,
                'group': group,
                'groups': settings.ALL_GROUPS,
            },
        )
    else:
        response = HttpResponseRedirect(reverse_lazy('home'))
    return response


@portal_auth_required(
    session_var='REDPANDA_AUTH',
    redirect_url=reverse_lazy('access_denied'),
)
def participation(request):
    """Dashboard for stats on folks who have participated."""
    user = request.user
    perms = user.profile.get_perms()
    if perms.get(settings.ADMIN_GROUP):
        groups = {
            'carthageStaffStatus': [],
            'carthageFacultyStatus': [],
            'carthageStudentStatus': [],
        }
        vaccines = User.objects.filter(profile__vaccine='Yes').count()
        for group in groups:
            vax = User.objects.filter(profile__vaccine='Yes').filter(
                groups__name=group,
            )
            groups[group] = vax.count()
        return render(
            request,
            'dashboard/participation.html',
            {'groups': groups, 'vax': vaccines},
        )
    else:
        return HttpResponseRedirect(reverse_lazy('dashboard_managers'))

