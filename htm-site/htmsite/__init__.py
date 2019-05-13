from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import unauthenticated_userid
import logging

log = logging.getLogger(__name__)

import json
from urllib.parse import urlparse
from pymongo import MongoClient
from pyramid.config import Configurator


def main(global_config, **settings):
    import os
    if 'mongo_uri' in settings:
        db_url = urlparse(settings['mongo_uri'])
    else:
        db_url = urlparse(os.getenv("WEBCAN_MONGO_URI"))
        settings['ldap_server'] = os.getenv('LDAP_SERVER')
        settings['ldap_suffix'] = os.getenv('LDAP_USERNAME_SUFFIX')
        settings['auth_ticket_key'] = os.getenv('AUTH_TICKET_KEY')
        settings['smtp_domain'] = os.getenv('SMTP_DOMAIN')
        settings['smtp_from'] = os.getenv('SMTP_FROM')
        settings['gmaps_api_key'] = os.getenv('GMAPS_API_KEY')

    config = Configurator(settings=settings)
    config.include('pyramid_mako')
    log.debug('Settings are: \n{}'.format(json.dumps(settings, indent=4)))

    def add_db(request):
        conn = MongoClient(db_url.geturl(),
                           serverSelectionTimeoutMS=10000,
                           connectTimeoutMS=10000,
                           socketTimeoutMS=10000,
                           maxPoolSize=200,
                           maxIdleTimeMs=30000,
                           appname='htm-site')
        db = conn[db_url.path[1:]]

        def conn_close(request):
            conn.close()

        request.add_finished_callback(conn_close)
        return db

    config.add_request_method(add_db, 'db', reify=True)

    def get_user(request):
        userid = unauthenticated_userid(request)
        if userid is not None:
            return request.db['scats_users'].find_one({'username': request.authenticated_userid})

    def auth_callback(uid, request):

        user = request.db['scats_users'].find_one({'username': uid})
        if user is not None:
            return ['auth']

    auth_policy = AuthTktAuthenticationPolicy(settings['auth_ticket_key'], callback=auth_callback, hashalg='sha512')
    config.set_authentication_policy(auth_policy)
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.add_request_method(get_user, 'user', reify=True)
    config.add_renderer('bson', 'htmsite.renderers.BSONRenderer')
    config.add_renderer('zip', 'htmsite.renderers.ZipRenderer')
    config.add_renderer('pymongo_cursor', 'htmsite.renderers.PymongoCursorRenderer')

    config.add_route('map', '/')
    config.add_route('intersections', '/intersections')
    config.add_route('intersection', '/intersection/{site_no}')
    config.add_route('intersection_json', '/intersections.json')
    config.add_route('intersection_info', '/intersection_{intersection}.json')
    config.add_route('readings_anomaly_json', '/get_readings_anomaly_{intersection}.json')
    config.add_route('get_anomalies_json', '/get_anomaly_{intersection}.json')
    config.add_route('readings_vs_sm_anomalies', '/readings_vs_sm_anomalies')

    config.add_route('reports', '/reports/{intersection}/{report}')

    config.add_route('accidents', '/accidents/{intersection}/{time_start}/{time_end}/{radius}')
    config.add_route('crash_investigate', '/crashes')
    config.add_route('incidents', '/incidents')

    config.add_route('update_neighbour_list', '/intersection/{site_no}/update_neighbours_list')
    config.add_route('update_neighbours', '/intersection/{site_no}/update_neighbours')
    config.add_route('csv_export', '/export')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')

    config.add_route('favicon', '/favicon.ico')
    config.add_static_view(name='assets', path='assets', cache_max_age=3600)
    config.scan()
    return config.make_wsgi_app()
