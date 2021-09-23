from datetime import datetime

import pymongo
from pyramid.view import view_config
import logging
log = logging.getLogger(__name__)


date_format = '%H/%M/%D'


def get_accident_near(time_start, time_end, intersection, radius=150, request=None):
    """
    Return any accidents at this time,
    should probably be listed in the app
    :param time:
    :param intersection:
    :return:
    """

    crashes = request.db.crashes
    locations = request.db.locations
    location = locations.find_one({'site_no': intersection})
    # timestamp = datetime.utcfromtimestamp(float(time))
    # delta = timedelta(minutes=30)
    query = {
        'loc': {
            '$geoNear': {
                '$geometry': location['loc'],
                '$maxDistance': radius
            }
        },
    }
    if time_start is not None:
        query['datetime'] = {
            '$gte': time_start,
            '$lte': time_end
        }

    return list(crashes.find(query).sort('datetime', pymongo.ASCENDING)), radius


def du(unix):
    return datetime.utcfromtimestamp(float(unix))


def validate_nodes(nodes, request):
    if len(nodes) == 0:
        return True
    ns = request.db.locations.distinct('site_no', {'site_no': {'$in': nodes}})
    return len(ns) == len(nodes)


@view_config(route_name='update_neighbours', renderer='json', request_method='POST')
def update_neighbours(request):
    locs = request.db.locations
    data = request.json_body
    # print data
    if not validate_nodes(data.keys()):
        return {'error': 'Invalid nodes'}
    locs.update_one({'site_no': request.matchdict['site_no']},
                    {
                        '$set': {
                            'neighbours_sensors': data
                        }
                    })
    return {'success': True}


@view_config(route_name='update_neighbour_list', renderer='json', request_method='POST')
def update_neighbour_list(request):
    locs = request.db.locations
    data = request.POST['neighbours'].split(',')
    # print data
    # print data
    if not validate_nodes(data, request):
        return {'error': 'Invalid nodes'}
    # return
    res = locs.update_one({'site_no': request.matchdict['site_no']},
                    {
                        '$set': {
                            'neighbours': data
                        }
                    })
    log.debug(res.raw_result)
    return {'success': True}

