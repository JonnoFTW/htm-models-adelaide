<%include file="header.mako"/>
<%
from bson import json_util
import json
from pluck import pluck
import time
def mkunix(dt):
    return int(time.mktime(dt.timetuple()))

has_anything = scores_count > 0
pfield = str(intersection['sensors'][0])
if isinstance(intersection['sensors'], str):
    popular_sensors = []
    intersection['sensors'] = []
else:
    popular_sensors = map(int,intersection['sensors'])
    intersection['sensors'] = sorted(map(int,intersection['sensors']))

del intersection['_id']
%>
<script type="text/javascript" src="//cdn.jsdelivr.net/bootstrap.daterangepicker/2/daterangepicker.js"></script>
<script type="text/javascript" src="/assets/fontawesome-markers.min.js"></script>
<div class="container">
    <h1>Intersection: ${intersection['site_no']}</h1>
    <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-info fa-fw"></i> Info
                </div>
                <table class="table table-striped">
                    <thead>
                    <tr>
                        <th>Attribute</th>
                        <th>Value</th>
                    </tr>
                    </thead>
                    <tbody>
                        % for k,v in intersection.items():
                            <%
                                ##                             print k,v
                            %>
                            <tr>
                                % if k in ['scats_diagram']:
                                    <%
                                        continue
                                    %>
                                % endif
                                <td>${k.replace('_',' ').title()}</td>
                                <td>
                                    % if k == 'neighbours':
                                        <select class="select2-from form-control" multiple
                                                style="width:100%; padding-bottom:10px" id="neighbour-list">
                                            %for n in v:
                                                <option selected value="${n['site_no']}">${n['site_no']}</option>
                                            %endfor
                                        </select>
                                        <button id="save-neighbours-list" data-id="${intersection['site_no']}"
                                                type="button" style="margin-top:10px" class="btn btn-primary">Save
                                        </button>
                                        <div class="alert alert-success" id="list-alert" style="display:none"
                                             role="alert"> Saved!
                                        </div>
                                    % elif k == 'neighbours_sensors':
                                    ## make a table neighbour id - from - to
                                    Table of sensors from neighbour intersection to this intersection
                                        <table class="table table-condensed">
                                            <thead>
                                            <tr>
                                                <th style="width: 10%">Intersection</th>
                                                ##                                                 <th style="width: 45%">From</th>

                                                <th style="width: 45%">To</th>
                                            </tr>
                                            </thead>
                                            <tbody id="neighbour-sensors">
                                                % for nid in pluck(intersection['neighbours'], 'site_no'):
                                                    <tr data-intersection="${nid}">
                                                        <td><a href="/intersection/${nid}">${nid}</a></td>
                                                        ##                                                         <td>
                                                        ##                                                             <input class="form-control ">${v.get(nid, '')} </input>
                                                        ##                                                             <select class="select2-from form-control sensor-map"
                                                        ##                                                                     multiple style="width:100%"
                                                        ##                                                                     data-intersection-from="${nid}">
                                                        ##                                                                 <% neighbour_intersection = {k['site_no']:k for k in intersection['neighbours']}[nid] %>
                                                        ##                                                                 % if 'sensors' in neighbour_intersection:
                                                        ## ##                                                                     % for sensor in sorted(neighbour_intersection['sensors'], key=lambda x: int(x)):
                                                        ##                                                                     ## sensors on the other end
                                                        ##                                                                         <%
                                                        ##                                                                         checked = ""
                                                        ##                                                                         ##                                                               print intersection
                                                        ## ##                                                                         if nid in intersection['neighbours_sensors'] and sensor in intersection['neighbours_sensors'][nid]['from']:
                                                        ## ##                                                                     checked = "selected"
                                                        ##                                                                     %>
                                                        ##                                                                         <option ${checked}
                                                        ##                                                                                 value="${sensor}">${sensor}</option>
                                                        ## ##                                                                     % endfor
                                                        ##                                                                 % endif
                                                        ##                                                             </select>

                                                        <td>
                                                            ## sensors on this intersection
                                                              <select class="select2-to form-control sensor-map"
                                                                      multiple
                                                                      style="width:100%" data-intersection-to="${nid}">
                                                            %if 'neighbours_sensors' in intersection and nid in intersection['neighbours_sensors']:
                                                                %for sensor in sorted(intersection['sensors'], key=lambda x: int(x)):
                                                                <% sensor = int(sensor) %>
                                                                ## sensors on the this end
                                                                    <option ${"selected" if   nid in intersection['neighbours_sensors'] and sensor in intersection['neighbours_sensors'][nid]['to'] else ""}
                                                                            value="${sensor}">${sensor}</option>
                                                                % endfor
                                                            %endif
                                                        </select>
                                                    </tr>
                                                % endfor
                                            </tbody>
                                        </table>
                                        <button id="save-neighbours" type="button" class="btn btn-primary">Save</button>
                                        <div class="alert alert-success" id="update-alert" style="display:none"
                                             role="alert"> Saved!
                                        </div>
                                    % elif k == 'loc':
                                        Lat: ${v['coordinates'][1]}, Lng: ${v['coordinates'][0]}
                                    % elif k == 'sensors':
                                        %for sensor in v:
                                            <span
                                                %if str(sensor) == str(pfield):
                                                    class="active"
                                                %endif
                                            ><a href="#observations" class="sensor-swapper">${sensor}</a></span>
                                        %endfor
                                    % elif k == 'strategic_inputs':
                                        <p>Match with strategic_input field in scats_sm data</p>
                                    % for si_config in v:
                                    ##                                                 <div class="panel list-group">
                                    ##                                                     <div class="list-group-item">
                                    ##
                                    ##
                                    ##                                                     </div>
                                    ##                                                 </div>
                                                ${si_config['date']}</br>
                                                <small>${si_config.get('comment','')}</small>
                                        <table class="table table-condensed">
                                            <thead>
                                            <tr>
                                                <th style="width: 10%">SI</th>
                                                <th style="width: 45%">Sensors</th>
                                            </tr>
                                            </thead>
                                            <tbody id="strategic-inputs">
                                                % for si_id, si_data in si_config['si'].items():
                                                    <tr>
                                                        <td><a href="#observations" class="si-swapper">${si_id}</a></td>
                                                        <td>
                                                            % for d in si_data['sensors']:
                                                                <a href="#observations" class="sensor-swapper">${d}</a>
                                                            % endfor
                                                            %if si_data['site_no'] != intersection['site_no']:
                                                                (${si_data['site_no']})
                                                            %endif
                                                        </td>
                                                    </tr>
                                                % endfor
                                            </tbody>
                                        </table>
                                    % endfor
                                    % else:
                                        ${v}
                                    % endif
                                </td>
                            </tr>
                        % endfor
                    </tbody>
                </table>
                <div class="panel list-group" id="accordion">
                    <a href="#" class="list-group-item" data-toggle="collapse" data-target="#sm" data-parent="#menu">Reports
                        <span id="chevron" class="glyphicon glyphicon-chevron-up pull-right"></span>
                    </a>

                    <div id="sm" class="sublinks panel-collapse collapse">
                        % for i in reports:
                            <a href="/reports/${intersection['site_no']}/${i.replace(' ','_').lower()}"
                               class="list-group-item small">${i}</a>
                        %endfor
                    </div>
                </div>
            </div>

        </div>
        <div class="col-lg-6">

                <%include file="time_range_panel.html"/>
        </div>
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading" id="neighbour-prev">
                    <i class="fa fa-line-chart fa-fw"></i>
                    Neighbour Preview
                </div>
                <div class="panel-body">
                    <a href="#" class="pop">
                        <img id="neighbour-preview" class="img-responsive" src=""/>
                    </a>
                </div>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-info fa-fw"></i> SCATS Diagram
                </div>
                <div class="panel-body">
                    ##                         <div style="height:600px">
                    % if 'scats_diagram' in intersection:
                ##                         <div class="tiles">
                ##                        <div class="tile" data-scale="2.4" data-image="data:image/png;base64,${intersection['scats_diagram']}"></div></div>
                        <a href="#" class="pop">
                    <img class="img-responsive" src="data:image/png;base64,${intersection['scats_diagram']}">
                </a>
                    <div class="modal fade" id="imagemodal" tabindex="-1" role="dialog" aria-labelledby="myModalLabel"
                         aria-hidden="true">
                        <div class="modal-dialog modal-huge">
                            <div class="modal-content">
                                <div class="modal-body">
                                    <button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span
                                            class="sr-only">Close</span></button>
                                    <img src="" class="imagepreview" style="width: 100%;">
                                </div>
                            </div>
                        </div>
                    </div>

                %else:
                    <img class="img-responsive" src="/assets/missing.png">
                % endif

                    ##                         </div>
                                        </div>
                <!-- /.panel-body -->
            </div>
        </div>

    </div>
    % if scores_count:
        <div class="row" id="observations" style="margin-top:60px;padding-top:60px;">
            <div class="col-lg-12">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <i class="fa fa-line-chart fa-fw"></i>
                        Observation <i class="fa fa-spinner fa-pulse loaderImage"></i>
                        <div class="dropdown pull-right">
                            <a href="#" class="dropdown-toggle" data-toggle="dropdown"
                               id="sensor-label">Sensors: </a>
                            <select id="sensors-select" style="width:300px" multiple>
                                %for sensor in range(1,25):
                                    <option value="${sensor}"
                                        % if sensor ==1:
                                            selected
                                        % endif
                                    >${sensor}</option>
                                %endfor
                            </select>

                            ##                             <label for="observation-sum">Sum</label><input type="radio" name="observation-sum"/>
                            ##                             <ul class="dropdown-menu" role="menu" aria-labelledby="prediction-sensor-menu">
                            ##                                 %for sensor in sorted(popular_sensors, key=lambda x: int(x)):
                            ##                                     <li
                            ##                                         %if int(sensor) == int(pfield):
                            ##                                             class="active"
                            ##                                         %endif
                            ##                                     ><a class="sensor-swapper">${sensor}</a></li>
                            ##                                 %endfor
                            ##                             </ul>
                        </div>

                    </div>
                    <div class="panel-body">
                        <figure style="width: 100%; height: 300px;" id="prediction-chart"></figure>
                    </div>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-12">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <i class="fa fa-line-chart fa-fw"></i> Anomaly Scores <i
                            class="fa fa-spinner fa-pulse loaderImage"></i>

                        <span id="date-range-text" class="pull-right"></span>
                    </div>
                    <!-- /.panel-heading -->
                    <div class="panel-body">
                        <button type="button" class="btn btn-info btn-arrow-left shift-data">Older</button>
                        <button type="button" class="btn btn-info btn-arrow-right pull-right shift-data">Newer</button>
                        <figure style="width: 100%; height: 300px;" id="anomaly-chart"></figure>
                        <form href="" class="form-inline" id="anomaly-params">
                            <div class="form-group">
                                <label for="threshold">Threshold</label>
                                <input type="text" class="form-control" id="threshold-input" placeholder="0.99"
                                       value="0.99">
                                <label for="threshold">Mean Filter</label>
                                <input type="number" class="form-control" id="mean-filter" placeholder="0" min="1"
                                       value="1">
                            </div>
                            <div class="checkbox">
                                <label><input type="checkbox" id="logarithm-input"> Log of likelihood</label>
                            </div>
                            <div class="form-group">
                                <label id="anomaly-list-label">High Anomaly at: </label>
                                <p id="form-anomalies"></p>
                            </div>

                        </form>

                    </div>
                </div>
            </div>
        </div>
    %else:
        <div class="row">
            <div class="col-lg-12">
                <div class="panel panel-default">
                    <div class="panel-body">
                        <div class="bs-callout bs-callout-danger">
                            <h4>Nothing to Display!</h4>
                            There's no flow data for this intersection!
                        </div>
                    </div>
                </div>
            </div>
        </div>
    %endif
    <div class="row">
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-line-chart fa-fw"></i> Incidents
                </div>
                <!-- /.panel-heading -->
                <table class="table table-striped">
                    <thead>
                    <tr>
                        <th>Time</th>
                        <th>Error</th>
                        <th>Vehicles</th>
                        <th>Weather</th>
                        <th>Crash Type</th>
                        <th>Involves 4WD</th>
                        <th>Severity</th>
                        <th>Total Damage</th>
                    </tr>
                    </thead>
                    <tbody id='incidents-table'>
                    </tbody>
                </table>
            </div>
        </div>
        <div class="col-lg-6">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-map fa-fw"></i> Nearby Accidents
                    <div class="dropdown pull-right">
                        <a href="#" class="dropdown-toggle" data-toggle="dropdown" id="radius-label">Radius: ${radius}
                            m<b class="caret"></b></a>

                        <ul class="dropdown-menu" role="menu" aria-labelledby="radius-label">
                            %for i in [50,100,150,200,250,300]:
                                <li><a class="radius-swapper">${i}</a></li>
                            %endfor
                        </ul>
                    </div>
                </div>
                <div class="panel-body">
                    <div style="height:600px" id="map-incident"></div>
                </div>
                <!-- /.panel-body -->
            </div>
        </div>
        ##         %if 'scats_diagram' in intersection:
        ##              <div class="col-lg-12">
        ##                 <div class="panel panel-default">
        ##                     <div class="panel-heading">
        ##                         <i class="fa fa-info fa-fw"></i> SCATS Diagram
        ##                     </div>
        ##                     <div class="panel-body">
        ## ##                         <div style="height:600px">
        ##                             <img class="img-responsive" src="data:image/png;base64,${intersection['scats_diagram']}">
        ## ##                         </div>
        ##                     </div>
        ##                     <!-- /.panel-body -->
        ##                 </div>
        ##             </div>
        ##          %endif
            </div>
</div>
<script type="text/javascript">
    var None = null;
    var True = true;
    var mainMap = false;
    var False = false;
    var anomalyChart, predictionChart;
    var mapCrash;
    var lat = ${intersection['loc']['coordinates'][1]};
    var lng = ${intersection['loc']['coordinates'][0]};
    var incidents = ${json.dumps(incidents,default=json_util.default)|n};
    var radius = ${radius};
    var pfield = '${pfield}';
    var crashMarkers = [];
    var crashDefault = '#B71C1C';
    var crashSelected = '#D9EDF7';
    var stoi = function (x) {
        return parseInt(x)
    };

    // highlight the ith incident in the map
    // and on the table
        ##     console.log("Select2 running");
    $('select').select2({
        tags: true
    });
    mapCrash = new GMaps({
        lat: lat,
        lng: lng,
        div: '#map-incident',
        zoom: 15
    });
    var markerIcon = function (selected) {
        return {
            path: fontawesome.markers.EXCLAMATION_CIRCLE,
            scale: 0.5,
            strokeWeight: 0.2,
            strokeColor: 'black',
            strokeOpacity: 1,
            fillColor: selected ? crashSelected : crashDefault,
            fillOpacity: 1,
        };
    };
    var mapCircle = null;
    var setupIncidents = function (newRadius) {
        radius = newRadius;
        var mainMarker = {
            lat: lat,
            lng: lng,
            title: '${intersection['site_no']}'
        };
        mapCrash.removeMarkers();
        mapCrash.addMarker(mainMarker);
        %for i in intersection['neighbours']:
        <%
            if 'loc' not in i:
                    continue
        %>
            mapCrash.addMarker({
                lat: ${i['loc']['coordinates'][1]},
                lng: ${i['loc']['coordinates'][0]},
                title: '${i['site_no']}',
                infoWindow: {
                    content: '<a href="/intersection/'+${i['site_no']}+
                    '">'+${i['site_no']}+'</a>'
                }
            });
        %endfor
        if (mapCircle != null) {
            mapCircle.setRadius(radius);
        }
        else {
            mapCircle = mapCrash.drawCircle({
                lat: lat,
                lng: lng,
                radius: radius,
                editable: false,
                fillColor: '#004de8',
                fillOpacity: 0.27,
                strokeColor: '#004de8',
                strokeOpacity: 0.62,
                strokeWeight: 1

            });
        }
        $.each(incidents, function (idx, obj) {
            var windowStr = '<b>Damage:</b> $' + this.Total_Damage +
                    '<br><b>Vehicles:</b> ' + this.Total_Vehicles_Involved +
                    '<br><b>Cause:</b> ' + this.App_Error +
                    '<br><b>Type:</b> ' + this.Crash_Type +
                    '<br><b>Date:</b> ' + moment.utc(this.datetime['$date']).format('LLL');
            var m = mapCrash.addMarker({
                lat: this.loc['coordinates'][1],
                lng: this.loc['coordinates'][0],
                infoWindow: {content: windowStr},
                icon: markerIcon(false),
                click: function (e) {
                    highlightAccident(1 + idx);
                }
            });
            crashMarkers.push(m);
        });

        // populate the table and the anomalychart
        $('#incidents-table').empty();
        $.each(incidents, function (idx1, value) {
            var row = $('<tr></tr>');
            $.each(['datetime', 'App_Error', 'Total_Vehicles_Involved',
                'Weather_Cond - Moisture_Cond', 'Crash_Type', 'Involves_4WD', 'CSEF_Severity','Total_Damage'], function (idx2, field) {

                row.append('<td>' + _.map(field.split('-'), function (x) {
                    if (x == 'datetime') return moment.utc(value[x]['$date']).format('LLLL'); else return value[x.trim()];
                }).join(' - ') + '</td>');
            });
            $('#incidents-table').append(row);
        });
        if (anomalyChart)
            anomalyChart.updateOptions({'file': makeAnomalyReadingArrays(pfield, 'anomaly').aData});

    };

    var highlightAccident = function (idx) {
        var query = '#incidents-table > tr:nth-child(' + idx + ')';
        $(query).addClass('info').siblings().removeClass('info');
        $.each(crashMarkers, function (index, obj) {
            obj.setIcon(markerIcon(index == idx - 1));
        });
    };
<%
    if scores_count == 0:
        start_title = incidents[0]['datetime'].strftime('%d/%m/%Y')
        end_title = incidents[-1]['datetime'].strftime('%d/%m/%Y')
%>
    var annotations = [];
    var neighbour_diagrams = {
        % for s in intersection['neighbours']:
            % if 'scats_diagram' in s:
                ${s['site_no']}:
                "data:image/png;base64,${s['scats_diagram']}",
            %else:
                ${s['site_no']}:
                "/assets/missing.png",
            % endif

        % endfor
    }
        %if has_anything: ## anything related to sensor readings goes here
        var allData, anomalyData;

        var hideLoader = function () {
            $('.loaderImage').hide();
        };
        var modelRunning = ${'running' in intersection};
        var loadData = function (from, to, callback) {
            console.log("Loading data from json", from, to);
            var args = {
                'from': from,
                'to': to,
            };
            $('.loaderImage').show();
            $.getJSON('/get_readings_anomaly_${intersection['site_no']}.json', args,
                    function (data) {
                        if (data.length === 0) {
                            // no data!
                            console.log('No data');
                        } else {
                            $.getJSON('/get_anomaly_${intersection['site_no']}.json', args, function (dataAnom) {
                                anomalyData = dataAnom;
                                allData = data;
                                var txt = moment.utc(data[0]["datetime"]["$date"]).format('LLL') + " - " + moment.utc(data[data.length - 1]["datetime"]["$date"]).format('LLL');

                                $('#date-range-text').text(txt);
                                if (callback)
                                    callback();
                                anomalyChart.updateOptions({
                                    dateWindow: null,
                                    valueRange: null
                                });
                                predictionChart.updateOptions({
                                    dateWindow: null,
                                    valueRange: null
                                });
                            });

                        }
                        hideLoader();
                    }).fail(function () {
                hideLoader();
            });

        };

        function Queue(size) {
            this.queue = [];
            this.size = size;
        }
        ;
        Queue.prototype.push = function (item) {
            this.queue.push(item);
            if (this.queue.length > this.size)
                this.queue.shift();
        };
        Queue.prototype.shift = function () {
            return this.queue.shift();
        }
        Queue.prototype.avg = function () {
            return _.reduce(this.queue, function (x, y) {
                return x + y
            }, 0) / this.queue.length;
        }
        var makeAnomalyReadingArrays = function (sensor, only) {
            var threshold = parseFloat($('#threshold-input').val());
            var meanFilter = parseInt($('#mean-filter').val());
            var logarithm = $('#logarithm-input').is(':checked');
            console.log("threshold:", threshold, "log", logarithm, "mean filter size", meanFilter);
            //return an array made from all data
            var aData = new Array(allData.length);
            var pData = new Array(allData.length);
            var multiSensors = $('#sensors-select').select2('val');
            var out;
            var queue = null;
            if (meanFilter > 1) {
                queue = new Queue(meanFilter);
            }
            if (only === 'anomaly')
                out = {'aData': aData};
            else if (only === 'readings')
                out = {'pData': pData};
            else
                out = {'aData': aData, 'pData': pData};
            annotations = [];
            allData.forEach(function (row, index, in_array) {
                // columns are: date,anomaly, likelihood, incident, incident_predict],

                var row_time = row["datetime"]["$date"];

                if (only !== 'anomaly') {
                    var value;
                    if (multiSensors) {
                        value = 0;
                        multiSensors.forEach(function (el) {
                            var v = row['readings'][el];
                            if (v < ${max_vehicles})
                                value += v;
                        });
                    } else
                        value = row['readings'][sensor] < ${max_vehicles}? row['readings'][sensor] : null;
                    var mean_value = null;
                    if (queue) {
                        queue.push(value);
                        mean_value = queue.avg();
                    }
                    pData[index] = [new Date(row_time), value, mean_value];
                }
                if (row['anomalies'] !== undefined && only !== 'readings') {
                    anomalyCount = _.filter(row['anomalies'], function (n) {
                        return n['likelihood'] > threshold;
                    }).length;
                    aData[index] = [new Date(row_time),
                        row['anomalies'][sensor]['score'],
                        !logarithm ? row['anomalies'][sensor]['likelihood'] :
                                Math.log(1.0 - row['anomalies'][sensor]['likelihood']) / -23.02585084720009,
                        _.find(incidents, function (n) {
                            return Math.round(n['datetime']['$date'] / 300000) * 300000 === row_time;
                        }) ? 1.1 : null,
                        anomalyCount >= 1 ? anomalyCount / Object.keys(row['anomalies']).length : null
                    ];
                } else {
                    var nowAnoms = _.filter(anomalyData, function (n) {
                        return n['datetime']['$date'] === row_time;
                    });
                    var htmAnomVS = null;
                    var htmAnomSM = null;
                    var shesdAnomVS = null;
                    var shesdAnomSM = null;
                    var shesdtsAnomVS = null;
                    var shesdtsAnomSM = null;

                    _.forEach(nowAnoms, function (x) {
                        if (x.algorithm === 'HTM') {

                            if (x.ds === 'sm') {
                                htmAnomSM = 1.1
                            } else {
                                htmAnomVS = 1.0
                            }
                            annotations.push({
                                series: 'HTM_Anomaly',
                                x: new Date(row_time),
                                shortText: x.strategic_input,
                                text: 'HTM Anomaly {}'.format(x.strategic_input)
                            });

                        } else if (x.algorithm === 'shesd') {
                            if (x.ds ==='sm') {
                                shesdAnomSM = 0.9
                            } else {
                                shesdAnomVS = 0.8
                            }
                            annotations.push({
                                series: 'SHESD_Anomaly',
                                x: new Date(row_time),
                                shortText: x.strategic_input,
                                text: 'SHESD Anomaly {}'.format(x.strategic_input)
                            });
                        } else if (x.algorithm === 'shesd-ts') {
                            if (x.ds ==='sm') {
                                shesdtsAnomSM = 0.7
                            } else {
                                shesdtsAnomVS = 0.6
                            }
                            annotations.push({
                                series: 'SHESD-ts_Anomaly',
                                x: new Date(row_time),
                                shortText: x.strategic_input,
                                text: 'SHESD-ts Anomaly {}'.format(x.strategic_input)
                            });
                        }

                    });

                    aData[index] = [new Date(row_time),
                        htmAnomVS ,
                        htmAnomSM ,
                        shesdAnomVS ,
                        shesdAnomSM ,
                        shesdtsAnomVS,
                        shesdtsAnomSM,
                        _.find(incidents, function (n) {
                            return n['datetime']['$date'] === row_time;
                        }) ? 1.2 : null
                    ];
                }
            });
            return out
        };

        var setupDygraphs = function () {

            loadData(${mkunix(time_start)},${mkunix(time_end)}, function () {
                var arReadings = makeAnomalyReadingArrays(pfield);
                if (arReadings.aData.length == 0) {
                    console.log("no anomaly data");
                    $('#anomaly-chart').before('<div class="bs-callout bs-callout-danger">\
                 <h4>Nothing to Display!</h4>\
              There\'s no anomaly values for this time period. It might not have been analysed yet.\
            </div>').height('0');
                } else {
                    anomalyChart = new Dygraph(document.getElementById('anomaly-chart'), arReadings.aData, {
                        title: 'Incidents and Anomalies for intersection ${intersection['site_no']}',
                        ylabel: 'Anomaly',
                        xlabel: 'Date',
                        HTM_Anomaly_VS: {
                            color: "blue"
                        },
                        SHESD_Anomaly_VS: {
                            color: "red"
                        },
                        Incident: {
                            color: "green",
                            strokeWidth: 0.0,
                            pointSize: 4
                        },
                        axes: {
                            y: {
                                valueRange: [0, 1.3]
                            }
                        },
                        zoomCallback: function (min, max, yRanges) {
                            zoomGraph(predictionChart, min, max);
                        },
                        highlightCallback: function (event, x, points, row, seriesName) {
                            highlightX(predictionChart, row);
                            if (points[2].xval) {
                                // find idx of point[2] in incidents array
                                // using xval
                                var accidentIdx = 1 + _.findIndex(incidents, function (x) {
                                    return Math.round(x["datetime"]["$date"] / 300000) * 300000 === points[2].xval;
                                });
                                //console.log("Moused over", accidentIdx);
                                highlightAccident(accidentIdx);
                            }
                            [0,1].forEach(function(p) {
                                if (points[p].yval) {
                                    $('#anomaly-list-label').text("High Anomaly at " + moment.utc(points[p].xval).format('LLLL'));
                                    var threshold = parseFloat($('#threshold-input').val());
                                    var sensors = [];
                                    _.each(anomalyData, function (val) {
                                        if (val.datetime.$date === points[p].xval)
                                            sensors.push([val.algorithm, val.strategic_input]);
                                    });
                                    var anomaly_list = $('p#form-anomalies');
                                    anomaly_list.empty();
                                    $.each(sensors, function (i, val) {
                                        anomaly_list.append(val[0]+'<a href="#observations" class="si-swapper">' + val[1] + '</a> <br/>');
                                    });
                                }
                            })

                        },
                        labels: ['UTC',
                            'HTM_Anomaly_VS',
                            'HTM_Anomaly_SM',
                            'SHESD_Anomaly_VS',
                            'SHESD_Anomaly_SM',
                            'SHESD-ts_Anomaly_VS',
                            'SHESD-ts_Anomaly_SM',
                            'Incident'
                        ],
                        <%include file="dygraph_weekend.js"/>
                    });
                }
                predictionChart = new Dygraph(document.getElementById('prediction-chart'), arReadings.pData, {
                    labels: ['UTC', 'Reading', 'Mean'],
                    title: 'Observation on Sensor: ' + pfield,

                    ylabel: 'Volume',
                    xlabel: 'Date',
                    zoomCallback: function (min, max, yRanges) {
                        zoomGraph(anomalyChart, min, max);
                    },
                    highlightCallback: function (event, x, point, row, seriesName) {
                        highlightX(anomalyChart, row);
                    },
                    <%include file="dygraph_weekend.js"/>
                });


            });

        };
        if (!${has_anything}) {
            console.log("no readings data");
            $('#prediction-chart').before('<div class="bs-callout bs-callout-danger">\
          <h4>Nothing to Display!</h4>\
          There\'s no readings for this time period. It might not have been analysed yet.\
        </div>').height('0');
        }
        var zoomGraph = function (graph, min, max) {
            if (graph)
                graph.updateOptions({
                    dateWindow: [min, max]
                });
        };
        var highlightX = function (graph, row) {
            if (graph)
                graph.setSelection(row);
        };

        var dispFormat = "%d/%m/%y %H:%M";


        var opts = {
            "dataFormatX": function (x) {
                return d3.time.format('${date_format}').parse(x);
            },
            "tickFormatX": function (x) {
                return d3.time.format(dispFormat)(x);
            },
            "mouseover": function (d, i) {
                var pos = $(this).offset();
                $(tt).text(d3.time.format(dispFormat)(d.x) + ': ' + d.y)
                        .css({top: topOffset + pos.top, left: pos.left + leftOffset})
                        .show();
            },
            "mouseout": function (x) {
                $(tt).hide();
            }
        };
        <%
            start_title = time_start.strftime('%d/%m/%Y %H:%M')
            end_title = time_end.strftime('%d/%m/%Y %H:%M')
        %>



        var daterangepickerformat = 'DD/MM/YYYY H:mm';
        $('input[name="daterange"]').daterangepicker({
            timePicker: true,
            timePickerIncrement: 5,
            locale: {
                format: daterangepickerformat
            },
            startDate: '${start_title}',
            endDate: '${end_title}'
        }).on('apply.daterangepicker', function (env, picker) {
            var dates = $('#dateinput').val().split('-');
            loadData(moment.utc(dates[0].trim(), daterangepickerformat).unix(),
                    moment.utc(dates[1].trim(), daterangepickerformat).unix(),
                    setChartsFromMake);
        });
        $('#sensors-select').on("change", function (e) {
            setChartsFromMake();
        });
        var setChartsFromMake = function () {
            var arReadings = makeAnomalyReadingArrays(pfield);
            var title = pfield;
            var multi = $('#sensors-select').select2("val");
            if (multi) {
                title = multi.join(",");
            }
            predictionChart.updateOptions({'file': arReadings.pData, 'title': 'Observation on Sensor: ' + title});
            anomalyChart.updateOptions({'file': arReadings.aData, axes: {y: {valueRange: [0, 1.3]}}});
            anomalyChart.setAnnotations(annotations);
            updateIncidents();

        };
        $(document).ready(function () {
            if (${scores_count}>
            0
        )
            setupDygraphs();
            $('.shift-data').click(function (e) {
                // determine if we are older or newer
                var older = $(this).text() === 'Older';
                var from, to;
                if (older) {
                    to = predictionChart.getValue(0, 0) / 1000; // lowest reading
                    from = to - (${day_range}* 24 * 60 * 60
                )
                    ;// lowest reading in chart - ${day_range} days
                } else {
                    to = predictionChart.getValue(predictionChart.numRows() - 1, 0) / 1000;
                    from = to + (${day_range}* 24 * 60 * 60
                )
                    ;
                }
                loadData(from, to, setChartsFromMake);
                // load accidents from the new timeframe too
                updateIncidents(radius, from, to);
            });
            % if 'running' in intersection:
                var intervalId = window.setInterval(function () {
                    console.log("reloading because site is running");
                    from = predictionChart.getValue(0, 0) / 1000;
                    to = predictionChart.getValue(predictionChart.numRows() - 1, 0) / 1000;
                    loadData(from, to, setChartsFromMake);

                    $.getJSON('/intersection_${intersection['site_no']}.json', function (data) {
                        if (!data.hasOwnProperty('running')) {
                            console.log("Stopping reloading");
                            clearInterval(intervalId);
                        }
                    });
                }, 1000 * 10);
            %endif


            $('#anomaly-params').change(function () {
                console.log("Anomaly chart params updated");
                setChartsFromMake();
            }).on('submit', function (ev) {
                ev.preventDefault();
            });
        });

        %endif
    setupIncidents(radius);

    function toggleChevron(e) {
        $(e.target)
                .parent()
                .find('span.glyphicon')
                .toggleClass('glyphicon-chevron-down glyphicon-chevron-up');
    }

    $('#accordion').on('hidden.bs.collapse', toggleChevron);
    $('#accordion').on('shown.bs.collapse', toggleChevron);

    $('body').on('click', '.sensor-swapper', function () {
        var sensorId = $(this).text();
        var oldValues = $("#sensors-select").val();
        oldValues.push(sensorId);
        var uniqueArray = oldValues.filter(function (item, pos) {
            return oldValues.indexOf(item) == pos;
        });
        $('#sensors-select').select2().val(uniqueArray).trigger('change');
        console.log('adding sensor to', sensorId);
        setChartsFromMake();

        ##  $('#sensor-label').html('Sensor: ' + pfield + ' <b class="caret"></b>');
        $('.sensor-swapper:contains("' + pfield + '")').parent().addClass('active').siblings().removeClass('active');
    });
    $('body').on('click', '.si-swapper', function () {
        $('#sensors-select').select2().val($(this).parent().next().text().replace(/\s+/g, ' ').trim().split(" ")).trigger('change');
        setChartsFromMake();
    });
    $('.radius-swapper').click(function () {
        radius = $(this).text();
        $('#radius-label').html('Radius: ' + radius + 'm <b class="caret"></b>');
        updateIncidents(radius);
    });
    $('#incidents-table').on('mouseover', 'tr', function () {
        var idx = $(this).index();

        highlightAccident(idx + 1);
        // highlight the one on the chart too
        if (anomalyChart)
            anomalyChart.setSelection(incidents[idx]);
    });
    $('tbody#neighbour-sensors > tr').hover(function (e) {
        var img = neighbour_diagrams[$(this).data('intersection')];
        ##     console.log(num, neighbour_diagrams[num]);
            if (img === undefined)
            img = '/assets/missing.png';
        $('#neighbour-preview').attr('src', img);

    }, function (e) {
        ;
    });
    var updateIncidents = function (radius, start, end) {
        if (!radius) {
            radius = $('#radius-label').text().split(' ')[1].slice(0, -1);
        }
        if (!start) {
            start = $('input[name="daterange"]').data('daterangepicker').startDate.unix();
            end = $('input[name="daterange"]').data('daterangepicker').endDate.unix();
        }
        console.log("Updating incidents in radius ", radius, "from ", start, " to ", end);
        $.getJSON('/accidents/${intersection['site_no']}/' + start + '/' + end + '/' + radius, function (data) {
            // repopulate table and markers
            incidents = data[0];
            radius = data[1];
            crashMarkers = [];
            setupIncidents(radius);
        });
    };
    $('#save-neighbours').click(function (e) {
        // ajax save the new neighbour organisation

        var data = {}
        _.each(_.keys(neighbour_diagrams), function (elem) {
            data[elem] = {
                'from': $('input[data-intersection-from="' + elem + '"]').val(),
                'to': _.map($('select[data-intersection-to="' + elem + '"]').val(), stoi)
            }
        });
        console.log(data);
        $.ajax({
            url: '/intersection/${intersection["site_no"]}/update_neighbours',
            type: 'POST',
            data: JSON.stringify(data),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            success: function (res) {
                showSuccess('#update-alert', res);
            }
        })
    });

    $('.pop').on('click', function () {
        $('.imagepreview').attr('src', $(this).find('img').attr('src'));
        $('#imagemodal').modal('show').on('click', function () {
            $('#imagemodal').modal('hide');
        });

    });


        <%include file="neighbour_save.mako" />

</script>


