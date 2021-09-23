<%include file="header.mako"/>

<div class="container">
    <div class="row" style="padding-top:20px">
        <div class="col-lg-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-info fa-fw"></i> Users
                    <button type="button" class="btn btn-primary">Add User</button>
                </div>
                <div class="panel-body">
                    <div class="row">
                        <div class="col-6">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Username</th>
                                        <th>Login Type</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    % for user in users:
                                    <tr>
                                        <td>${user['username']}</td>
                                        <td>${user['login']}</td>
                                    </tr>
                                    % endfor
                                </tbody>
                            </table>

                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<script>

</script>