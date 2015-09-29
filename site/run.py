from collections import Counter
from wsgiref.simple_server import make_server
import numpy
from pyramid.config import Configurator
from pyramid.renderers import render_to_response
from datetime import datetime, timedelta
import pymongo
import os
import yaml
import json

from pyramid.events import subscriber
from pyramid.events import BeforeRender


REPORTS = ('Daily Total', 'AM Peak', 'PM Peak', 'Peak Volumes', 'Highest AM Peaks', 'Highest PM Peaks', 'Phase Splits')

def get_site_dir():
    return os.path.dirname(os.path.realpath(__file__))

try:
    path = os.path.join(os.path.dirname(get_site_dir()), 'connection.yaml')
    with open(path, 'r') as f:
        conf = yaml.load(f)
        mongo_uri = conf['mongo_uri']
        mongo_database = conf['mongo_database']
        mongo_collection = conf['mongo_collection']
        gmaps_key = conf['GMAPS_API_KEY']

except:
    raise Exception('No connection.yaml with mongo_uri defined! please make one with a mongo_uri variable')

@subscriber(BeforeRender)
def add_global(event):
    event['GMAPS_API_KEY'] = gmaps_key
    event['date_format'] = '%Y-%m-%d %H:%M'

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
  #  return _get_intersections()[0]
    with _get_mongo_client() as client:
        coll = client.mack0242['locations']
        return coll.find_one({'intersection_number': intersection})


def _get_intersections():
    """
    Get the signalised intersections for Adelaide
    :return: a cursor of documents of signalised intersections
    """
  #  return [{'lga':'ACC','scats_region':'ACC','intersection_number':'3001','loc': {'lat':-34.9271532,'lng':138.6003676}}]

    with _get_mongo_client() as client:
        coll = client[mongo_database]['locations']
        return coll.find({'intersection_number': {'$exists': True}}, {'_id': False})


def get_accident_near(time, intersection):
    """
    Return any accidents at this time,
    should probably be listed in the app
    :param time:
    :param intersection:
    :return:
    """
    with _get_mongo_client() as client:
        db = client[mongo_database]
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


def get_anomaly_scores(from_date=None, to_date=None, intersection='3001', anomaly_threshold=None):
    """

    :param from_date: unix time to get readings from
    :param to_date:  unix time to get readings until
    :param intersection:  the intersection to get readings for
    :return:
    """
    with _get_mongo_client() as client:
        # input is a unix date
        coll = client[mongo_database][mongo_collection]
        query = {'site_no': intersection}
        if from_date is not None:
              query['datetime']['$gte'] = datetime.utcfromtimestamp(from_date)
        if to_date is not None:
            query['datetime']['$lte'] = datetime.utcfromtimestamp(to_date)
        if anomaly_threshold is not None:
            query['anomaly_score'] = {'$gte': float(anomaly_threshold)}
        return coll.find(query,
                         ['datetime', 'site_no', 'prediction', 'readings', 'anomaly_score']).\
                sort('datetime', pymongo.ASCENDING)


def _daily_volume(data, am=False, pm=False):
    counter = Counter()
    # return averages for every day in the period
    # and the average for the year
    for i in data:
        if not(am and i['datetime'].hour == 8) or not(pm and i['datetime'].hour == 15):
            continue
        for j in i['readings']:
            counter[i['datetime'].date()] += j['vehicle_count']
    return counter


def _am_peak(data):
    return _daily_volume(data, am=True)


def _pm_peak(data):
    return _daily_volume(data, pm=True)


def _peak_volumes(data):
    pass


def _highest_am_peaks(data):
    pass


def _highest_pm_peaks(data):
    pass


def _phase_splits(data):
    pass


def _get_report(intersection, report, start=None, end=None):
    """
    Return a report
    :param intersection:
    :param report:
    :param start:
    :param end:
    :return:
    """

    report_funcs = dict(zip(map(lambda x:x.lower().replace(' ','_'),REPORTS),
                            [_daily_volume,_am_peak,_pm_peak,_peak_volumes,
                             _highest_am_peaks,_highest_pm_peaks,_phase_splits]))
    if report not in report_funcs:
        return "No such report format exists"
    if start is None and end is not None:
        # start will be 1 year before end
        start = end - timedelta(days=365)
    elif end is None and start is not None:
        end = start + timedelta(days=365)
    with _get_mongo_client() as client:
        coll = client[mongo_database][mongo_collection]
        query = {'site_no':intersection,
                    'datetime': {
                        '$gte': start,
                        '$lte': end
                    }
             }
        data = coll.find(query).sort({'datetime': pymongo.ASCENDING})
        return report_funcs[report](data), intersection, start, end


def show_report(request):
    """

    :param request:
    :return:
    """
    args = request.matchdict
    start, end = None, None
    if 'start' in args.GET:
        start = args.GET['start']
    if 'end' in args.GET:
        end = args.GET['end']
    data, intersection, start, end = _get_report(args['intersection'], args['report'], start, end)
    arr = numpy.array(data.values())
    stats = {'std': numpy.std(arr), 'avg': numpy.average(arr)}
    return render_to_response(
        'views/report.mak',
        {'data': sorted(data.items()),
         'report': args['report'],
         'intersection': intersection,
         'stats': stats,
         'start': start,
         'end': end},
        request
    )


def show_map(request):
    """

    :param request:
    :return:
    """
    intersections = _get_intersections()
    return render_to_response(
        'views/map.mak',
        {'intersections': json.dumps(list(intersections))
         },
        request=request
    )


def get_readings_anomaly_json(request):
    """

    :param request:
    :return:
    """
    args = request.matchdict.GET
    return list(get_anomaly_scores(args['from'], args['to'], args['intersection']))


def intersections_json():
    """

    :return:
    """
    return list(_get_intersections())


def list_intersections(request):
    """

    :param request:
    :return:
    """
    return render_to_response(
        'views/list.mak',
        {'intersections': _get_intersections(),
         'reports': REPORTS
         },
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
    anomaly_score = list(get_anomaly_scores(intersection=args['site_no']))
    predIdx = -1
    if len(anomaly_score) > 0:
        try:
            predIdx = next(index for (index, d) in enumerate(anomaly_score[0]['readings'])
                   if d["sensor"] == anomaly_score[0]['prediction']['sensor'])
        except:
            pass
    return render_to_response(
        'views/intersection.mak',
        {'intersection': intersection,
         'scores': anomaly_score,
         'predIdx': predIdx,
         },
        request=request
    )


if __name__ == '__main__':
    config = Configurator()
    config.include('pyramid_mako')
    config.add_route('map', '/')
    config.add_view(show_map, route_name='map')
    config.add_route('intersection', '/intersection/{site_no}')
    config.add_route('intersection_json', '/intersections.json')
    config.add_route('readings_anomaly_json', '/get_readings_anomaly.json')
    config.add_view(get_readings_anomaly_json, route_name='readings_anomaly_json', renderer='json')
    config.add_view(intersections_json, route_name='intersection_json', renderer='json')
    config.add_view(show_intersection, route_name='intersection')
    config.add_route('intersections', '/intersections')
    config.add_route('reports', '/report/{intersection}/{report}')
    config.add_view(show_report, route_name='reports')
    config.add_view(list_intersections, route_name='intersections')
    config.add_static_view(name='assets', path='assets')
    config.scan()
    app = config.make_wsgi_app()
    host, port = '127.0.0.1', 8080
    server = make_server(host, port, app)
    print ("Running on http://{}:{}".format(host, port))
    server.serve_forever()
