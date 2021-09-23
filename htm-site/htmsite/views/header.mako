<!DOCTYPE html>
<html lang="en">
    <head>
        <link rel="icon" href="/assets/favicon.ico" type="image/x-icon"/>
        <link rel="shortcut icon" href="/assets/favicon.ico" type="image/x-icon"/>
        <meta http-equiv="content-type" content="text/html; charset=UTF-8">
        <meta charset="utf-8">
        <title>HTM Adelaide</title>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
        <meta name="description" content="A basic template for Bootstrap 3.0" />
         <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.3/jquery.min.js"></script>
        <script type='text/javascript' src="//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js"></script>
        <script src="https://maps.googleapis.com/maps/api/js?key=${request.registry.settings['gmaps_api_key']}"></script>
        <script src="//cdnjs.cloudflare.com/ajax/libs/gmaps.js/0.4.19/gmaps.js"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.3/css/select2.min.css">
        <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.3/js/select2.full.min.js"></script>
        <link href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css" rel="stylesheet">
##         <script type="text/javascript" src="//cdn.jsdelivr.net/momentjs/latest/moment.min.js"></script>
        <script type="text/javascript" src="https://momentjs.com/downloads/moment-with-locales.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.6/d3.min.js" charset="utf-8"></script>
        <link rel="stylesheet" type="text/css" href="//cdn.jsdelivr.net/bootstrap.daterangepicker/2/daterangepicker.css" />
        <link rel="stylesheet" type="text/css" href="/assets/site.css" />
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/4.4.0/css/font-awesome.min.css">
        <link href="/assets/bootstrap-sortable/bootstrap-sortable.css" rel="stylesheet">
        <script src="/assets/bootstrap-sortable/bootstrap-sortable.js"></script>
        <script src="//cdnjs.cloudflare.com/ajax/libs/dygraph/1.1.1/dygraph-combined.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.8.3/underscore-min.js"></script>
        <script>
            String.prototype.format = function () {
              var i = 0, args = arguments;
              return this.replace(/{}/g, function () {
                return typeof args[i] != 'undefined' ? args[i++] : '';
              });
            };
        </script>
        <style type="text/css">
            body, html {
              height: 100%;
              width: 100%;
              margin: 0;
              padding:0;
            }

            div#map_c {
                width: 100%;
                height: 100%;
                padding:0;
                margin:auto;
            }
            div#list_c {

            }
            body {
                padding-top: 50px;
            }
            #map {
                width:100%;
                height:100%;
            }
            span.active {
                font-weight: bold;
            }
            .modal-huge {
                width: 95%;
            }
        </style>
    </head>
    <body>
        <div class="navbar navbar-inverse navbar-fixed-top">
          <div class="container">
            <div class="navbar-header">
              <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-collapse">
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
              </button>
              <a class="navbar-brand" href="/">HTM Adelaide</a>
            </div>
            <div class="collapse navbar-collapse">
              <ul class="nav navbar-nav nav-pills">
                <li><a href="/intersections">Intersections</a></li>
                <li><a href="/incidents">Incidents</a></li>
                <li><a href="/crashes">Crashes</a></li>
                <li><a href="/export">Export</a></li>
              </ul>
                <ul class="nav navbar-nav navbar-right">
                %if request.authenticated_userid:
                    <li class="nav-item"><a class="nav-link" href="/logout">Logout</a></li>
                %endif

            </ul>
            </div><!--/.nav-collapse -->
          </div>
        </div>

