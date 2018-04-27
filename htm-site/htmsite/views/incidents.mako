<%include file="header.mako"/>

<div class="container" id="list_c">
<div class="row" style="padding-top:20px">
<div class="col-lg-12">
 <div class="panel panel-default">
                    <div class="panel-heading">
                        <i class="fa fa-info fa-fw"></i> Incidents (${len(incidents)})
                        <div class="pull-right btn-group"><a href="#" id="filterbtn" class="btn btn-default btn-sm">Show on threshold</a></div>
                    </div>

<div class="input-group"> <span class="input-group-addon"> <i class="fa fa-search fa-fw"></i></span>
<input id="filter" type="text" class="form-control" placeholder="Type here...">
</div>
<table class="table table-hover table-bordered table-striped sortable">
<thead>
<tr>
% for i in ('Date', 'Intersection','Distance', 'Description', 'Likelihood 1', 'Likelihood 2', 'Likelihood 3'):
    <th data-field="${i.lower().replace(' ','_')}">${i}</th>
% endfor
</tr>
</thead>
<tbody class="searchable">
<%
count = 0
count_other = 0
%>
% for i in incidents:
    %if len(i[1]):
    <tr>
        <td>${i[0]['datetime'].strftime(date_format)}</td>
        <td><a href="/intersection/${i[2]['site_no']}">${i[2]['site_no']}</a></td>
        <td>${"%.2f" %i[3]}m</td>
        <td>${i[0]['App_Error']}</td>
        <%
        triggered = False
        %>
        %for j in i[1]:
            <td >
            %if 'anomalies' in j:
            <b>${j['datetime'].strftime("%H:%M")}</b></br><p>
            ${", ".join([k+": "+str(v['likelihood']) for k,v in j['anomalies'].items() if v['likelihood'] > 0.99])}
            <%
                if any(map(lambda x: x[1]['likelihood']>0.99, j['anomalies'].items())):
                    triggered = True
            %>
            </p>
            %endif
            </td>
        %endfor
        <%
            if triggered:
                count +=1
            else:
                count_other += 1
        %>
    </tr>
    %endif
% endfor
</tbody>
</table>
Incidents exceeding threshold: ${count}, none exceeding: ${count_other}
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
    $('#filterbtn').click(function() {
        // hide rows without sensor passing the threshold
        $('tbody > tr').each(function() {
            if(!($(this).find('p').text().trim())) {
                $(this).toggle();
            }
        });
    });
    
});
</script>
<%include file="footer.html"/>
