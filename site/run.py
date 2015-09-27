from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.renderers import render_to_response
from datetime import datetime, timedelta
from mako.template import Template
import pymongo
import os
import yaml
import json


def get_site_dir():
    return os.path.dirname(os.path.realpath(__file__))

try:
    path = os.path.join(os.path.dirname(get_site_dir()), 'connection.yaml')
    with open(path, 'r') as f:
        conf = yaml.load(f)
        mongo_uri = conf['mongo_uri']
        gmaps_key = conf['GMAPS_API_KEY']
except:
    raise Exception('No connection.yaml with mongo_uri defined! please make one with a mongo_uri variable')


def _get_mongo_client():
    """
    Give you a pymongoclient for the database
    might need to do some caching or we'll end up
    with loads of open connections
    :return: a pymongo client
    """
    return pymongo.MongoClient(mongo_uri)


def _get_intersection(intersection):
    """
    Get information for a single intersection
    :return: a dict with the info
    """
    return {}
    with _get_mongo_client() as client:
        coll = client.mack0242['locations']
        return coll.find_one({'intersection_number': intersection})


def _get_intersections():
    """
    Get the signalised intersections for Adelaide
    :return: a cursor of documents of signalised intersections
    """
    return [{'lga':'ACC','scats_region':'ACC','intersection_no':'3001'}]

    with _get_mongo_client() as client:
        coll = client.mack0242['locations']
        return coll.find({'intersection_number': {'$exists': True}})


def get_accident_near(time, intersection):
    """
    Return any accidents at this time,
    should probably be listed in the app
    :param time:
    :param intersection:
    :return:
    """
    with _get_mongo_client() as client:
        db = client.mack0242
        crashes = db['crashes']
        locations = db['locations']
        location = locations.find_one({'intersection_number': intersection})
        timestamp = datetime.utcfromtimestamp(time)
        delta = timedelta(minutes=30)
        return crashes.find({
            'loc': {
                '$geoNear': {
                   '$geometry': location['loc'],
                    '$maxDistance': 200
                }
            },
            'datetime': {
                '$gte': timestamp - delta,
                '$lte': timestamp + delta
            }
        })


def get_anomaly_scores(from_date=None, to_date=None, intersection='3001'):
    """

    :param from_date: unix time to get readings from
    :param to_date:  unix time to get readings until
    :param intersection:  the intersection to get readings for
    :return:
    """
    with _get_mongo_client() as client:
        # input is a unix date
        coll = client.mack0242['ACC_201306_20130819113933']
        query = {'site_no': intersection}
        if from_date is not None:
              query['datetime']['$gte'] =  datetime.utcfromtimestamp(from_date)
        if to_date is not None:
            query['datetime']['$lte'] = datetime.utcfromtimestamp(to_date)
        return coll.find(query,
                         ['datetime', 'site_no', 'prediction', 'anomaly_score'])


def show_map(request):
    """

    :param request:
    :return:
    """
    return render_to_response(
        'views/map.mak',
        {'GMAPS_API_KEY': gmaps_key},
        request=request
    )

def intersections_json():
    return list(_get_intersections())

def list_intersections(request):
    """

    :param request:
    :return:
    """
    return render_to_response(
        'views/list.mak',
        {'intersections': _get_intersections()},
        request=request
    )


def show_intersection(request):
    """

    :param request:
    :return:
    """

    args = request.matchdict
    # show specific intersection if it exists
    intersection = _get_intersection(args['site_no'])
    anomaly_score = get_anomaly_scores(intersection=args['site_no'])
    return render_to_response(
        'views/intersection.mak',
        {'intersection': intersection,
         'scores': anomaly_score
         'GMAPS_API_KEY': gmaps_key},
        request=request
    )


if __name__ == '__main__':
    config = Configurator()
    config.include('pyramid_mako')
    config.add_route('map', '/')
    config.add_view(show_map, route_name='map')
    config.add_route('intersection', '/intersection/{site_no}')
    config.add_route('intersection_json', '/intersections.json')
    config.add_view(intersections_json, route_name='intersection_json', renderer='json')
    config.add_view(show_intersection, route_name='intersection')
    config.add_route('intersections', '/intersections')
    config.add_view(list_intersections, route_name='intersections')
    config.add_static_view(name='assets',path='assets')
    app = config.make_wsgi_app()
    host, port = '127.0.0.1', 8080
    server = make_server(host, port, app)
    print ("Running on http://{}:{}".format(host, port))
    server.serve_forever()
