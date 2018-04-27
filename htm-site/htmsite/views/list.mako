<%include file="header.mako"/>
<div class="container" id="list_c">
<div class="row" style="padding-top:20px">
<div class="col-lg-12">
 <div class="panel panel-default">
                    <div class="panel-heading">
                        <i class="fa fa-info fa-fw"></i> Intersections
                    </div>

<div class="input-group"> <span class="input-group-addon"> <i class="fa fa-search fa-fw"></i></span>
<input id="filter" type="text" class="form-control" placeholder="Type here...">
</div>
<table class="table table-hover table-bordered table-striped sortable">
<thead>
<tr>
% for i in ('ID', 'LGA', 'Description','SCATS Region', 'Map', 'Charts', 'Reports'):
    <th data-field="${i.lower().replace(' ','_')}">${i}</th>
% endfor
</tr>
</thead>
<tbody class="searchable">
% for i in sorted(intersections, key=lambda x: int(x['site_no'])):
    <tr>
    % for j in ('site_no','lga','description' , 'scats_region'):
        % if j in i:
        <td>${i[j]}</td>
        % else:
            <td></td>
        % endif
    % endfor
    <td><a href="/?site=${i['site_no']}"><button type="button" class="btn btn-primary btn-lg">
    <span class="glyphicon glyphicon-map-marker"></span></button></a></td>
    <td><a href="/intersection/${i['site_no']}"> <button type="button" class="btn btn-primary btn-lg">
    <span class="glyphicon glyphicon-signal"></span></button></a></td>
    <td>
        <ul class="nav nav-pills" role="tablist">
            <li role="presentation" class="dropdown active">
                <a class="dropdown-toggle" data-toggle="dropdown" href="#" role="button" aria-haspopup="true" aria-expanded="false">
                  Reports<span class="caret"></span>
                </a>
                <ul class="dropdown-menu">
                  % for j in reports:
                    <li><a href="/reports/${i['site_no']}/${j.lower().replace(' ','_')}">${j}</a></li>
                  % endfor
                </ul>
            </li>
         </ul>
    </td>

    </tr>
% endfor
</tbody>
</table>
</div></div>
</div>
</div>
<script type="text/javascript">
$(document).ready(function () {
    $('th').slice(-3).attr('data-defaultsort','disabled');
    (function ($) {

        $('#filter').keyup(function () {

            var rex = new RegExp($(this).val(), 'i');
            $('.searchable tr').hide();
            $('.searchable tr').filter(function () {
                return rex.test($(this).text());
            }).show();

        })

    }(jQuery));

});
</script>
<%include file="footer.html"/>