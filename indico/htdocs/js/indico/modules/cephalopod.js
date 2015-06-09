function _isSynced(cephalopodUrl, localData) {
    var defer = $.Deferred();
    $.ajax({
        url: cephalopodUrl,
        type: 'GET',
        dataType: 'json',
    }).done(function onSuccess(response) {
        var synced = true;
        _.each(localData, function(localVal, key) {
            if (localVal === response[key]) { return; }
            synced = false;
        });
        defer.resolve(synced);
    }).fail(function onError(response, status, error) {
        $('<span>', { 'class': 'mono', 'text': error }).appendTo(
            $('<div>', {
                'class': 'message-text',
                'html' : $T('Something went wrong while contacting the instance tracker.<br>It returned the following error: ')
            }).appendTo(
                $('<div>', { 'class': 'error-message-box'})
                    .appendTo($('#flashed-messages')))
        );
        defer.reject(error);
    });
    return defer.promise();
}

function initCephalopdOnSettingsPage(cephalopodUrl) {
    var $tracked = $('#tracked');
    var enabled = $tracked.prop('checked');

    $('#tracked').on('change', function() {
        enabled = $(this).prop('checked');
        $('#sync-button').prop('disabled', !enabled);
    });

    // Only check if synced, if enabled;
    if (!enabled) { return; }

    var defer = $.Deferred();
    _isSynced(cephalopodUrl, {
        'enabled'     : $('#tracked').prop('checked'),
        'contact'     : $('#contact_name').val(),
        'email'       : $('#contact_email').val(),
        'url'         : $('#instance-url').html(),
        'organisation': $('#affiliation').html()
    }).done(function onSuccess(synced) {
        $('<span>', {'class' : 'i-label'})
        defer.resolve(synced ? $T('Synchronized') : $T('Out of sync'))
        $('#tracking-status').html();
    }).fail(function onError(err) {
        defer.reject(err);
    });
}

function initCephalopodOnAdminPage(cephalopodUrl, checkData, settingsUrl) {
    _isSynced(cephalopodUrl, checkData).done(function onSuccess(synced) {
        if (!synced) {
            $('<div>', {
                'class': 'message-text',
                'html' : $T('Instance tracking data is out-of-sync! You can solve this <a href="{0}">here</a>.')
                            .format(settingsUrl)
            }).appendTo(
                $('<div>', { 'class': 'warning-message-box' })
                    .appendTo($('#flashed-messages'))
            );
        }
    });
}
