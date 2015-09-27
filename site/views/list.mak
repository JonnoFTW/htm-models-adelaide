<%include file="header.html"/>
<div class="container" id="list_c">
<div class="row">
<div class="col-md-12">
<table class="table table-hover table-bordered table-striped">
<thead>
<tr>
% for i in ('ID', 'LGA', 'SCATS Region', 'Map', 'Charts'):
    <th>${i}</th>
% endfor
</tr>
</thead>
<tbody>
% for i in intersections:
    <tr>
    % for j in ('intersection_no', 'lga', 'scats_region'):
        <td>${i[j]}</td>
    % endfor
    <td><a href="/?site=${i['intersection_no']}"><button type="button" class="btn btn-primary btn-lg">
    <span class="glyphicon glyphicon-map-marker"></span></button></a></td>
    <td><a href="/intersection/${i['intersection_no']}"> <button type="button" class="btn btn-primary btn-lg">
    <span class="glyphicon glyphicon-signal"></span></button></a></td>
    </tr>
% endfor
</tbody>
</table>
</div></div>
</div>
<%include file="footer.html"/>