 var stoi = function (x) {
        return parseInt(x)
    };
var showSuccess = function (id, res) {
        var msg = "Saved";
        var box = $(id);
        box.removeClass('alert-success alert-danger');
        if (_.has(res, 'error')) {
            msg = res.error;
            box.addClass('alert-danger');
        } else {
            box.addClass('alert-success');
        }
        box.text(msg).fadeIn(1000).delay(2000).fadeOut(1000);
    }

    $('#save-neighbours-list').click(function (e) {
        var data = _.map($('select[id^="neighbour-list"]').val(), stoi).join();
        var site_no = $(this).data('id');
        $.post('/intersection/{}/update_neighbours_list'.format(site_no), {'neighbours': data}
        ).success(function (res) {
            showSuccess('#list-alert', res);
            // refresh the page
            console.log(res);
            if (_.has(res, 'success') && !mainMap)
                window.location.reload();
        });
    });
