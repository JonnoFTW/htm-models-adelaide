import json
from datetime import timedelta

import pymongo
from .util import du, get_accident_near, date_format
from .reports import REPORTS
from pluck import pluck
from pyramid import exceptions as exc
from pyramid.view import view_config


def _get_intersections(request, images=True):
    """
    Get the signalised intersections for Adelaide
    :return: a cursor of documents of signalised intersections
    """
    exclude = {'_id': False}
    if not images:
        exclude['scats_diagram'] = False
    return request.db.locations.find({'site_no': {'$exists': True}}, exclude)


@view_config(route_name='intersection_info', renderer='bson')
def intersection_info(request):
    request.response.content_type = 'application/json'
    return _get_intersection(request.matchdict['intersection'], request)


def _get_intersection(intersection, request):
    """
    Get information for a single intersection
    :return: a dict with the info
    """
    return request.db.locations.find_one({'site_no': intersection})


def _get_neighbours(intersection, request):
    """

    :param intersection:
    :return:
    """
    center = _get_intersection(intersection, request)
    if not center or 'neighbours' not in center or len(center['neighbours']) == 0:
        return []
    coll = request.db.locations
    if type(center['neighbours']) is dict:
        neighbours = center['neighbours'].keys()
    else:
        neighbours = center['neighbours']
    return list(coll.find({'site_no': {'$in': neighbours}}))


@view_config(route_name='intersection_json', renderer='bson')
def intersections_json(request):
    """

    :return:
    """
    return list(_get_intersections(request))


def get_diagrams(intersections, request):
    intersections = pluck(intersections, 'site_no')
    return request.db.locations.find(
        {'site_no': {'$in': intersections}, 'scats_diagram': {'$exists': True}})


@view_config(route_name='intersection', renderer='views/intersection.mako')
def show_intersection(request):
    """
    :param request:
    :return:
    """

    args = request.matchdict
    # show specific intersection if it exists
    site = args['site_no']

    intersection = _get_intersection(site, request=request)
    if intersection is None:
        raise exc.HTTPBadRequest("Invalid Intersection")
        # return render_to_response('views/missing_intersection.mako', {}, request)
    # if 'neighbours' in intersection:
    #     intersection['_neighbours'] = intersection['neighbours']
    intersection['neighbours'] = _get_neighbours(site, request=request)

    # cursor = get_anomaly_scores(intersection=site)
    day_range = 60
    # cursor_count = cursor.count()
    # cursor = list(cursor)
    # # get the very latest date
    # if cursor_count == 0:
    #     anomaly_score_count = 0
    # else:
    #     last = cursor[-1]['datetime']

    last_reading = list(request.db.scats_readings.find({'site_no': site}).sort([('datetime', -1)]).limit(1))[0]
    end_date = last_reading['datetime']
    from_date = end_date - timedelta(days=day_range)
    cursor = get_anomaly_scores(from_date=from_date, to_date=end_date, intersection=site, request=request)
    anomaly_score_count = cursor.count()

    # if anomaly_score_count == 0:
    #     time_start = None
    #     time_end = None
    # else:
    # try:
    #     intersection['sensors'] = intersection['sensors']
    # except:
    intersection['sensors'] = list(last_reading['readings'].keys())

    incidents, radius = get_accident_near(from_date, end_date, intersection['site_no'], request=request)
    neighbour_diagrams = get_diagrams(intersection['neighbours'], request=request)
    if 'neighbours_sensors' not in intersection:
        intersection['neighbours_sensors'] = {k['site_no']: {'to': [], 'from': []} for k in
                                              intersection['neighbours']}
    return {'intersection': intersection,
            'scores_count': anomaly_score_count,
            'incidents': incidents,
            'radius': radius,
            'day_range': day_range,
            'time_start': from_date,
            'time_end': end_date,
            'scats_diagrams': neighbour_diagrams,
            'reports': REPORTS,
            'max_vehicles': request.registry.settings['max_vehicles'],
            'date_format': date_format
            }


@view_config(route_name='readings_anomaly_json', renderer='pymongo_cursor')
def get_readings_anomaly_json(request):
    """

    :param request:
    :return:
    """

    args = request.matchdict
    request.response.content_type = 'application/json'
    ft = request.GET.get('from', None)
    tt = request.GET.get('to', None)
    if ft is not None:
        ft = int(ft)
    if tt is not None:
        tt = int(tt)
    return get_anomaly_scores(ft, tt, args['intersection'], request=request)


@view_config(route_name='map', renderer='views/map.mako')
def show_map(request):
    """

    :param request:
    :return:
    """
    intersections = _get_intersections(images=True, request=request)
    return {'intersections': json.dumps(list(intersections))}


@view_config(route_name='intersections', renderer='views/list.mako')
def list_intersections(request):
    """

    :param request:
    :return:
    """
    return {'intersections': _get_intersections(request=request),
            'reports': REPORTS
            }


def get_anomaly_scores(from_date=None, to_date=None, intersection='3001', anomaly_threshold=None, request=None):
    """

    :param from_date: unix time to get readings from
    :param to_date:  unix time to get readings until
    :param intersection:  the intersection to get readings for
    :return:
    """
    if type(from_date) is int:
        from_date = du(from_date)
    if type(to_date) is int:
        to_date = du(to_date)
    if from_date > to_date:
        from_date, to_date = to_date, from_date
    coll = request.db.scats_readings
    # input is a unix date
    query = {'site_no': intersection}
    if from_date or to_date:
        query['datetime'] = {}
    if from_date is not None:
        query['datetime']['$gte'] = from_date
    if to_date is not None:
        query['datetime']['$lte'] = to_date
    if anomaly_threshold is not None:
        query['anomaly_score'] = {'$gte': float(anomaly_threshold)}
    results = coll.find(query, {'_id': 0, 'predictions': 0}).sort([('datetime', pymongo.ASCENDING)])
    return results