import re
import secrets

import bcrypt
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config

LOGIN_TYPES = ('external', 'ldap')


@view_config(route_name='users', request_method='GET', renderer='views/users.mako')
def users(request):
    return {
        'users': list(request.db['scats_users'].find({}, {'_id': 0, 'password': 0, 'secret': 0, 'reset_password': 0})),
        'login_types': LOGIN_TYPES
    }


@view_config(route_name='users', request_method='POST', renderer='bson')
def add_user(request):
    new_fan = request.POST.get('fan')
    login_type = request.POST.get('login_type')

    if login_type not in LOGIN_TYPES:
        return HTTPBadRequest('Login type must be in ' + ', '.join(LOGIN_TYPES))
    if login_type == 'ldap':
        if not re.findall(r"\[a-z]{1,4}\d{4}", new_fan):
            return HTTPBadRequest("Must be a valid FAN")
    if request.db.webcan_users.find_one({'username': new_fan}) is not None:
        return HTTPBadRequest('Empty or existing usernames cannot be used again')

    new_user_obj = {
        'username': new_fan,
        'login': login_type,
        'password': ''
    }

    if login_type == 'external':
        new_user_obj['email'] = new_fan
        password = secrets.token_hex(16)
        new_user_obj['password'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user_obj['reset_password'] = secrets.token_urlsafe(16)

    request.db.webcan_users.insert_one(new_user_obj)
    return new_user_obj
