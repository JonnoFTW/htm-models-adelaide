<%include file="header.mako"/>

<div class="container">
    <div class="row" style="padding-top:20px">
        <div class="col-lg-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-info fa-fw"></i> Export CSV
                </div>
                <div class="panel-body">
                    <div class="row">
                        <div class="col-6">
                            <!-- Selections -->
                            <form method="post" action="/export">
                                <div class="form-group col-12">
                                    <label for="select-sites" class="col-12 col-form-label">Sites</label>
                                    <select name="select-sites" style="width:500px" multiple id="select-sites">
                                        %for s in sites:
                                            <option value="${s}">${s}</option>
                                        %endfor
                                    </select>
                                </div>
                                <div class="form-group col-6">
                                     <label for="dateinput" class="col-12 col-form-label">Date Range</label>
                                    <div class="input-group">


                                        <span class="input-group-addon"><i class="fa fa-clock-o fa-fw"></i></span>
                                        <input id="dateinput" name="daterange" class="form-control"/>
                                    </div>
                                </div>
                                <div class="form-group col-12">
                                    <div class="form-group">
                                        <input type="submit" id="download" value="Download" name="download"
                                               class="btn btn-primary"/>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript" src="//cdn.jsdelivr.net/bootstrap.daterangepicker/2/daterangepicker.js"></script>
<script>
    $(document).ready(function () {
        $('select').select2();
        $('input[name="daterange"]').daterangepicker({
            locale: {
                format: 'DD/MM/YYYY'
            },
            ##  startDate: '${start_title}',
            ##  endDate: '${end_title}'
        })
    });
</script>