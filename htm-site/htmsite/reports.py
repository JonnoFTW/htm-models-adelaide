from calendar import monthrange
from collections import Counter
from datetime import date, timedelta, datetime
import numpy as np
from numba import jit
import logging

log = logging.getLogger(__name__)
from pluck import ipluck, pluck
from pymongo.command_cursor import CommandCursor
from pyramid.view import view_config

REPORTS = ('Daily Total', 'Monthly Average', 'AM Peak', 'PM Peak',
           'Highest Peak Volumes', 'Highest AM Peaks',
           'Highest PM Peaks', 'Phase Splits',
           'Degree of Saturation', 'VO VK Ratio')
fmt = '%d/%m/%Y'


@jit()
def _get_daily_volume(data, hour=None):
    """

    :param data: the data
    :param hour:  hour to take the volume for ?
    :return: a counter of day: volume
    """
    # TODO: Convert this to use a pymongo aggregate
    counter = Counter()
    for i in data:
        if hour and i['datetime'].hour != hour:
            continue
        for s, c in i['readings'].items():
            if c < 200:  # request.regisry.settings['max_vehicles']:
                counter[i['datetime'].date()] += c
    return counter


@jit()
def _monthly_average(data):
    monthly_average = Counter()
    for i, j in _get_daily_volume(data).items():
        monthly_average[date(i.year, i.month, 1)] += j
    for i in monthly_average:
        monthly_average[i] /= monthrange(i.year, i.month)[1]
    return sorted(monthly_average.items())


def _monthly_average_aggregate(db):
    return db.scats_readings.aggregate(
        [
            {'$match': {
                'site_no': '3001',
                'datetime': {'$gte': datetime(2013)}
            }},
            {'$project': {
                'readings': 1,
                'month': {'$month': '$datetime'},
                'year': {'$year': '$datetime'},
                'flow': {'$filter': {
                    'input': '$readings',
                    'as': 'item',
                    'cond': {'$lte': ['$$item', 200]}
                }}
            }},
            {'$group': {
                '_id': {'month': "$month", 'year': "$year"},
                'avg': {'$avg': 'flow'}
            }}
        ])


def _daily_volume_aggregate(db, site, start, end):
    return db.scats_readings.aggregate([
        {'$match': {
            'site_no': site,
            'datetime': {'$gte': start, '$lte': end}
        }},
        {'$project': {
            'month': {'$month': '$datetime'},
            'year': {'$year': '$datetime'},
            'day': {'$dayOfMonth': '$datetime'},
            'flow': {
                '$sum': {
                    '$map': {
                        'input': {
                            '$filter': {
                                'input': {'$objectToArray': '$readings'},
                                'cond': {'$lte': ['$$this.v', 200]}
                            }
                        },
                        'in': '$$this.v'
                    }
                }
            }
        }},
        {'$group': {
            '_id': {
                'year': "$year",
                'month': "$month",
                'day': '$day'
            },
            'total': {'$sum': '$flow'}
        }},
        {'$sort': {
            '_id': 1
        }}
    ])


def _get_hour_aggregate(db, site, hour):
    return db.scats_readings.aggregate(
        [
            {'$match': {
                'site_no': site,
                'datetime': {
                    '$gte': datetime(2013, 1, 1),
                    '$lte': datetime(2013, 4, 1),
                    '$eq': {{'$hour': '$datetime'}: hour}
                }
            }},
            {'$project': {
                'readings': 1,
                'month': {'$month': '$datetime'},
                'year': {'$year': '$datetime'},
                'day': {'$day', '$datetime'},
                'flow': {'$sum': {
                    {'$filter': {
                        'input': '$readings',
                        'cond': {'$lte': ['$$this', 200]}
                    }}}
                }}},
            {'$group': {
                '_id': {'month': "$month", 'year': "$year", 'day': '$day'},
                'total': {'$sum': 'flow'}
            }}
        ])


def _highest_peak_volumes_aggregate(db, site):
    return db.scats_readings.aggregate(
        [
            {'$match': {
                'site_no': site,
                'datetime': {
                    '$gte': datetime(2013, 1, 1),
                    '$lte': datetime(2013, 4, 1),
                }
            }},
            {'$project': {
                'readings': 1,
                'month': {'$month': '$datetime'},
                'year': {'$year': '$datetime'},
                'day': {'$day', '$datetime'},
                'flow': {'$sum': {
                    {'$filter': {
                        'input': '$readings',
                        'cond': {'$lte': ['$$this', 200]}
                    }}}
                }}},
            {'$group': {
                '_id': {'month': "$month", 'year': "$year", 'day': '$day'},
                'total': {'$sum': 'flow'}
            }}
        ])
    # 30 highest peaks


def _am_peak_aggregate(db, site):
    return _get_hour_aggregate(db, site, 8)


def _pm_peak_aggregate(db, site):
    return _get_hour_aggregate(db, site, 15)


def _daily_volume(data):
    return sorted(_get_daily_volume(data).items())


def _am_peak(data):
    return sorted(_get_daily_volume(data, 8).items())


def _pm_peak(data):
    return sorted(_get_daily_volume(data, 15).items())


def _highest_peak_volumes(data):
    return sorted(_get_daily_volume(data).most_common(30), key=lambda x: x[1], reverse=True)


def _highest_am_peaks(data):
    return sorted(_get_daily_volume(data, 8).most_common(30), key=lambda x: x[1], reverse=True)


def _highest_pm_peaks(data):
    return sorted(_get_daily_volume(data, 15).most_common(30), key=lambda x: x[1], reverse=True)


def _phase_splits(data):
    return []


def _saturation_degree(data):
    return []


def _vo_vk_ratio(data):
    return []


def _get_report(request, intersection, report, start=None, end=None):
    """
    Return a report
    :param intersection:
    :param report:
    :param start:
    :param end:
    :return:
    """

    report_funcs = dict(zip(map(lambda x: x.lower().replace(' ', '_'), REPORTS),
                            [_daily_volume, _monthly_average, _am_peak, _pm_peak, _highest_peak_volumes,
                             _highest_am_peaks, _highest_pm_peaks, _phase_splits,
                             _saturation_degree, _vo_vk_ratio]))
    if report not in report_funcs:
        return "No such report format exists"
    if start is None and end is not None:
        # start will be 1 year before end

        start = end - timedelta(days=365)
    elif end is None and start is not None:
        end = start + timedelta(days=365)
    readings_coll = request.db.scats_readings
    query = {'site_no': intersection}

    if start and end:
        query['datetime'] = {'$gte': start, '$lte': end}
    data = readings_coll.find(query)
    return report_funcs[report](data), intersection, start, end


def _get_report_aggregate(request, intersection, report, start=None, end=None):
    """
    Return a report using the aggregate functions
    :param intersection:
    :param report:
    :param start:
    :param end:
    :return:
    """

    report_funcs = dict(zip(map(lambda x: x.lower().replace(' ', '_'), REPORTS),
                            [_daily_volume_aggregate, _monthly_average, _am_peak, _pm_peak, _highest_peak_volumes,
                             _highest_am_peaks, _highest_pm_peaks, _phase_splits,
                             _saturation_degree, _vo_vk_ratio]))
    if report not in report_funcs:
        return "No such report format exists"
    if start is None and end is not None:
        # start will be 1 year before end
        start = end - timedelta(days=365)
    elif end is None and start is not None:
        end = start + timedelta(days=365)
    try:
        return report_funcs[report](request.db, intersection, start, end), intersection, start, end
    except TypeError:
        log.debug("Falling back to python report: " + report)
        return _get_report(request, intersection, report, start, end)


@view_config(route_name='reports', renderer='views/report.mako')
def show_report(request):
    """
    :param request:
    :return:
    """
    args = request.matchdict
    start, end = datetime.strptime('01/01/2017', fmt), None
    if 'start' in request.GET:
        start = datetime.strptime(request.GET['start'], fmt)
    if 'end' in request.GET:
        end = datetime.strptime(request.GET['end'], fmt)
    start_t = datetime.now()
    data, intersection, start, end = _get_report_aggregate(request, args['intersection'], args['report'], start,
                                                           end)
    print("Query took: {}".format(datetime.now() - start_t))
    # output should be a list of tuples: (date, count)
    if type(data) is CommandCursor:
        data = [(date(**d['_id']), d['total']) for d in data]
    if len(data):
        arr = np.array(data)[:, 1]
        stats = {'Standard Deviation': arr.std(), 'Average': arr.mean()}
    else:
        stats = "Error"

    return {
        'data': data,
        'report': args['report'],
        'intersection': intersection,
        'stats': stats,
        'start': start,
        'end': end,
        'reports': REPORTS
    }
