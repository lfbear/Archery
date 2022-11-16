# -*- coding: UTF-8 -*-
""" 
@author: hhyo
@license: Apache Licence
@file: views.py
@time: 2019/12/21
"""

from django.shortcuts import render, reverse, redirect

__author__ = "hhyo"

from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseServerError,
)
from django.views.decorators.csrf import requires_csrf_token

import common
from archery.settings import GoogleOAuth
from sql.models import Users
import datetime
import logging


def google_login(request):
    redirect_uri = request.build_absolute_uri('/google-auth')
    return GoogleOAuth.google.authorize_redirect(request, redirect_uri)


def google_auth(request):
    token = GoogleOAuth.google.authorize_access_token(request)
    userinfo = token['userinfo']
    username = userinfo['email'].split('@')[0]
    login_flag = False
    err_msg = None

    try:
        user = Users.objects.get(username=username)
    except Users.DoesNotExist:
        user = Users.objects.create_user(
            username=username,
            password="",
            display=userinfo['name'],
            email=userinfo['email'],
            is_active=1,
            is_staff=False,
        )
        common.auth.init_user(user)
        login_flag = True
    except Exception as e:
        logger = logging.getLogger("default")
        logger.error("OAuth登录失败")
        err_msg = "%s occurred." % e.__class__
    else:
        login_flag = True

    if login_flag:
        user.last_login_failed_at = datetime.datetime.now()
        user.save()
        common.auth.login(request, user)
        return redirect('/')
    else:
        return server_error_with_content(request, {"title": "OAuth登录验证失败", "message": err_msg})


@requires_csrf_token
def bad_request(request, exception, template_name="errors/400.html"):
    return HttpResponseBadRequest(render(request, template_name))


@requires_csrf_token
def permission_denied(request, exception, template_name="errors/403.html"):
    return HttpResponseForbidden(render(request, template_name))


@requires_csrf_token
def page_not_found(request, exception, template_name="errors/404.html"):
    return HttpResponseNotFound(render(request, template_name))


@requires_csrf_token
def server_error(request, template_name="errors/500.html"):
    return HttpResponseServerError(render(request, template_name))


@requires_csrf_token
def server_error_with_content(request, data, template_name="errors/500.html"):
    return HttpResponseServerError(render(request, template_name, {"content": data}))
