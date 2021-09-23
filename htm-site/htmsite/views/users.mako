<%include file="header.mako"/>

<div class="container">
    <div class="row" style="padding-top:20px">
        <div class="col-lg-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <i class="fa fa-info fa-fw"></i> Users
                    <button type="button" class="btn btn-primary" data-toggle="modal" data-target="#addUserModal">Add
                        User
                    </button>
                    <!-- Modal -->
                    <div class="modal fade" id="addUserModal" tabindex="-1" role="dialog"
                         aria-labelledby="AddUserModal" aria-hidden="true">
                        <div class="modal-dialog" role="document">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title" id="exampleModalLabel">Add User</h5>
                                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                        <span aria-hidden="true">&times;</span>
                                    </button>
                                </div>
                                <div class="modal-body">
                                        <div class="form-group">
                                            <label for="inputFan">FAN</label>
                                            <input type="email" class="form-control" id="inputFan"
                                                   aria-describedby="fanHelp" placeholder="Enter FAN">
                                        </div>
                                        <div class="alert alert-danger collapse" id="input-error"></div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                                    <button type="button" class="btn btn-primary" id="add-user">Save</button>
                                </div>
                            </div>
                        </div>
                    </div>
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
    $('#add-user').click(function() {
        // post and see if we get a result back, on success dismiss and reload the page
        var btn = $(this)
        $('#input-error').hide()
        btn.addClass('disabled')
        $.post('/users', {
            fan: $('#inputFan').val(),
            login_type: 'ldap'
        }, function(data) {
            console.log(data)
            window.location.reload(false);
        }, 'json').fail(function(res) {
            $('#input-error').show()
            $('#input-error').text(res.responseJSON['message'])
        }).always(function() {
            btn.removeClass('disabled')
        })
    })
</script>