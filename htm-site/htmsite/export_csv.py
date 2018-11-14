from pyramid.renderers import render_to_response
from pyramid.view import view_config
import zipfile
from datetime import datetime
import csv
from io import BytesIO, StringIO
import base64


@view_config(route_name='csv_export', request_method='GET', renderer='views/export_csv.mako')
def export_csv(request):
    return {
        'sites': list(request.db.locations.distinct('site_no'))
    }


@view_config(route_name='csv_export', request_method='POST')
def export_csv_render(request):
    # print(request.POST)
    sites = request.POST.getall('select-sites')
    daterange = request.POST.get('daterange')
    start, end = sorted((datetime.strptime(d, '%d/%m/%Y') for d in daterange.split(' - ')))
    query = {
        'site_no': {'$in': sites},
        'datetime': {
            '$gte': start,
            '$lte': end,

        }
    }
    # print(json_util.dumps(query, indent=4))
    readings_cursor = request.db.scats_readings.find(query)
    csv_io = StringIO()
    writer = csv.DictWriter(csv_io, fieldnames=['datetime', 'site_no'] + [str(i) for i in range(25)])
    writer.writeheader()
    for row in readings_cursor:
        out = {
            'datetime': row['datetime'].isoformat(),
            'site_no': row['site_no'],
        }
        for s, flow in row['readings'].items():
            out[s] = flow

        writer.writerow(out)

    zip_out = BytesIO()
    now = datetime.now().timetuple()
    with zipfile.ZipFile(zip_out, 'w', compression=zipfile.ZIP_BZIP2) as zip_file_obj:
        zip_file_obj.writestr(zipfile.ZipInfo('readings.csv', date_time=now), csv_io.getvalue())
        for site in request.db.locations.find({'site_no': query['site_no']}):
            img64 = site['scats_diagram']
            img_io = BytesIO()
            img_io.write(base64.b64decode(img64))
            zip_file_obj.writestr(zipfile.ZipInfo('{}.png'.format(site["site_no"]), date_time=now), img_io.getvalue())

    request.response.content_type = 'application/zip'
    request.response.content_disposition = 'attachment;filename=scats_vs_export_{}.zip'.format(
        datetime.now().strftime('%Y%m%d_%H%M%S'))
    return render_to_response(
        renderer_name='zip',
        value=zip_out,
        request=request,
        response=request.response
    )
