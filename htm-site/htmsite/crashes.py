import json
from datetime import timedelta, datetime

from geopy.distance import geodesic
from .util import du, get_accident_near
from .intersection import _get_intersections
from pluck import pluck
from pyramid.view import view_config


@view_config(route_name='crash_investigate', renderer='views/crash.mako', request_method='GET')
def investigate_crash(request):
    intersections = _get_intersections(request, False)
    return {
        'intersections': json.dumps([i for i in intersections if 'loc' in i])
    }


@view_config(route_name='accidents', renderer='bson')
def get_accident_near_json(request):
    args = request.matchdict
    request.response.content_type = 'application/json'
    intersection, time_start, time_end = args['intersection'], du(args['time_start']), du(args['time_end'])
    radius = int(args['radius'])
    return get_accident_near(time_start, time_end, intersection, radius, request)


@view_config(route_name='crash_investigate', renderer='bson', request_method='POST')
def crash_in_polygon(request):
    readings_coll = request.db.scats_readings
    crashes_coll = request.db.crashes
    locations_coll = request.db.locations
    start = datetime(2012, 1, 1, 0, 0, 0)
    end = datetime(2015, 12, 12, 23, 59)
    drange = {'$gte': start, '$lte': end}

    if request.GET.get('site'):
        crashes = crashes_coll.find({
            'datetime': drange,
            'loc': {
                '$geoNear': {
                    '$geometry': locations_coll.find_one({'site_no': request.GET['site']})['loc'],
                    '$maxDistance': 100
                }
            }}).sort([('datetime', 1)])
    else:
        points = request.json_body
        # make sure it's a list of lists of floats
        points.append(points[0])

        crashes = crashes_coll.find({
            'datetime': drange,
            'loc': {
                '$geoWithin': {
                    '$geometry': {
                        'type': 'Polygon',
                        'coordinates': [points]
                    }
                }
            }}).sort([('datetime', 1)])
    crashes = list(crashes)
    td = timedelta(minutes=10)
    for i, crash in enumerate(crashes):
        # find the nearest 2 intersections
        # and get the readings for the downstream one
        sites = locations_coll.find({
            'loc': {
                '$geoNear': {
                    '$geometry': crash['loc']
                }
            }
        }).limit(2)
        sites = pluck(list(sites), 'site_no')
        # readings = readings_coll.find({
        #     'datetime': {'$gte': crash['datetime'] - td, '$lte': crash['datetime'] + td},
        #     'site_no': {'$in': sites}
        # }).limit(6).sort([['site_no', pymongo.ASCENDING], ['datetime', pymongo.ASCENDING]])
        anomalies = request.db.scats_anomalies.find({
            'site_no': {'$in': sites},
            'datetime': {'$gte': crash['datetime'] - td,
                         '$lte': crash['datetime'] + td}
        })
        crashes[i]['anomalies'] = list(anomalies)
        crashes[i]['sites'] = sites
    return {
        'crashes': crashes
    }


@view_config(route_name='incidents', renderer='views/incidents.mako')
def show_incidents(request):
    """
    Show the
    :param request:
    :return:
    """
    readings_coll = request.db.scats_readings
    crashes_coll = request.db.crashes
    locations_coll = request.db.locations
    # cursor = readings_coll.find().sort('datetime')
    # start = cursor[0]['datetime']
    # end = cursor[cursor.count() - 1]['datetime']
    incidents = []
    # get incidents in this range in CITY OF ADELAIDE lga

    results = crashes_coll.find()
    # get the readings of the nearest intersection at at the nearest time step
    td = timedelta(minutes=5)
    for crash in results:
        site = locations_coll.find_one({
            'loc': {
                '$geoNear': {
                    '$geometry': crash['loc']
                }
            }
        })
        readings = readings_coll.find({
            'datetime': {'$gte': crash['datetime'] - td, '$lte': crash['datetime'] + td},
            'site_no': site['site_no']
        }).limit(3).sort('datetime')
        incidents.append(
            (crash, list(readings), site, geodesic(site['loc']['coordinates'], crash['loc']['coordinates']).meters))
    #  print json.dumps(incidents, indent=4, default=json_util.default)
    return {'incidents': incidents}
