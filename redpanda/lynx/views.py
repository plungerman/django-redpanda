# -*- coding: utf-8 -*-

import json

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from djauth.decorators import portal_auth_required
from djimix.core.encryption import encrypt
from redpanda.lynx.models import URL


def rewrite(request, earl_hash):
    try:
        earl = URL.objects.get(earl_hash=earl_hash)
    except Exception:
        response = HttpResponseRedirect(reverse_lazy('home'))
    if earl.clicks == 0:
        earl.clicked()
        response = redirect(earl.earl_full)
    else:
        response = HttpResponseRedirect(reverse_lazy('home'))

    return response

@csrf_exempt
@portal_auth_required(
    session_var='REDPANDA_AUTH',
    redirect_url=reverse_lazy('access_denied'),
)
def api(request):
    uid = request.GET.get('uid')
    clear = None
    if uid:
        clear = '{0}?uid={1}'.format(
            request.build_absolute_uri(str(reverse_lazy('home'))),
            encrypt(uid),
        )
    earl = URL.objects.create(earl_full=clear)
    earl.earl_hash

    jason = {
        'lynx': '{0}{1}'.format(
            request.build_absolute_uri(str(reverse_lazy('lynx'))),
            earl.earl_hash,
        ),
        'hash': earl.earl_hash,
    }

    return HttpResponse(
        json.dumps(jason), content_type='application/json; charset=utf-8'
    )
