from pyramid.events import subscriber, BeforeTraversal
from ldap3 import Server, Connection, ALL, NTLM
from pyramid.security import remember, forget
from datetime import datetime, timedelta
from pyramid.view import view_config
import pyramid.httpexceptions as exc
import logging
import bcrypt
log = logging.getLogger(__name__)


@subscriber(BeforeTraversal)
def check_logged_in(event):
    # if the user is not logged in and tries to access anything but /login,
    # redirect to /login or send ajax error about not being logged in
    # return
    req = event.request
    req.environ['REMOTE_USER'] = req.authenticated_userid
    if req.path in ('/login', '/logout'):
        return
    if not req.user:
        if req.is_xhr:
            raise exc.HTTPForbidden("You need to be logged in")
        else:
            raise exc.HTTPFound('/login')


@view_config(route_name='login', renderer='views/simple/login.mako')
def login(request):
    login_url = request.resource_url(request.context, 'login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/'  # never use the login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    # if post data is set, try to login,
    message_def = 'Please provide a valid username and password'
    username = ''
    password = ''
    now = datetime.now()
    attempts = request.db.webcan_login_attempts.find_one({'ip': request.remote_addr})
    # failed login attempts in the last 10 minutes
    lockout_minutes = 20
    failed_login_msg = 'You have tried to login too much and have been banned for {} minutes'.format(lockout_minutes)
    failed_attempt_limit = 15
    if attempts is not None and attempts['banned_until'] is not None and attempts['banned_until'] > now:
        message = failed_login_msg
    elif 'form.submitted' in request.params:
        is_valid = False
        message = message_def
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        ip = request.remote_addr
        if not (username is None or password is None):
            user = request.db['scats_users'].find_one({'username': username})
            if user is not None:
                if user.get('login', None) == 'ldap':
                    is_valid, err = check_credentials(username,
                                                      password,
                                                      request.registry.settings['ldap_server'],
                                                      request.registry.settings['ldap_suffix'])
                    if err is not None:
                        log.debug("Failed login by {}: {}".format(username, err))
                        message = err
                else:  # if user['login'] == 'external':
                    is_valid = check_pass(password, user['password'])
                if is_valid:
                    # actually log the user in and take them to the front page!
                    headers = remember(request, user['username'])
                    # request.db.webcan_login_attempts.update_one({'ip': ip},
                    #                                             {'$set': {'banned_until': None, 'logins': []}})
                    return exc.HTTPFound(location=came_from, headers=headers)
        if not is_valid:
            # log this failed attempt from this IP
            if attempts is None:
                attempts = {
                    'ip': ip,
                    'banned_until': None,
                    'logins': [now]
                }
                request.db.webcan_login_attempts.insert_one(attempts)
            else:
                # failed login attempts in the last 10 minutes
                last_10_mins = [x for x in attempts['logins'] if (now - x).total_seconds() < 600]
                update = {'$push': {'logins': now}}
                if len(last_10_mins) >= failed_attempt_limit:
                    message = failed_login_msg
                    update['$set'] = {'banned_until': now + timedelta(minutes=lockout_minutes)}
                request.db.webcan_login_attempts.update_one({'_id': attempts['_id']}, update)

    else:
        message = ''

    return dict(
        message=message,
        url=request.application_url + '/login',
        came_from=came_from,
        username=username,
        password=password,
    )


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return exc.HTTPFound(location='/login', headers=headers)


def check_pass(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def check_credentials(username, password, ldap_server, ldap_suffix):
    """Verifies credentials for username and password.
    Returns True on success or False on failure
    """
    ldap_user = '\\{}@{}'.format(username, ldap_suffix)
    server = Server(ldap_server, use_ssl=True)

    connection = Connection(server, user=ldap_user, password=password, authentication=NTLM, receive_timeout=5)
    try:
        return connection.bind(), None
    except Exception as e:

        print("LDAP Error: ", connection.result, e)
        return False, "LDAP Error: " + str(e)
