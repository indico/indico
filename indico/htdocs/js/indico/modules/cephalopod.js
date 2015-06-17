/**
 * Check if the data returned by `cephalopodUrl` matches `localData`
 *
 * Performs an ajax request to retrieve the data to check and return a
 * jQuery promise with the a boolean indicating if the data matches or
 * not. If the ajax request fails, the promise is rejected wit the ajax
 * error. An error flash message is also shown on the page unless the
 * `quiet` option is set to `false` (defaults to `true`).
 */
function _isSynced(cephalopodUrl, localData, quiet) {
    quiet = quiet || false;
    var defer = $.Deferred();
    $.ajax({
        url: cephalopodUrl,
        type: 'GET',
        dataType: 'json',
        timeout: 10000 // 10 seconds
    }).done(function onSuccess(response) {
        var synced = true;
        _.each(localData, function(localVal, key) {
            if (localVal === response[key]) { return; }
            synced = false;
        });
        defer.resolve(synced);
    }).fail(function onError(xhr, status, error) {
        var errMsg = $T('Unknown error while contacting the Community Hub');
        if (xhr.state() === 'rejected' && xhr.status === 200 && status === 'parsererror') {
            errMsg = $T('Internal error: Parse error on the reply of the Community Hub.');
        } else if (xhr.state() === 'rejected' && xhr.status === 0 && status === 'error') {
            errMsg = $T('Unable to contact the Community Hub.');
        } else if (xhr.state() === 'rejected' && xhr.status === 0 && status === 'timeout') {
            errMsg = $T('The connection to the Community Hub timed out.');
        } else if ((xhr.state() === 'rejected' && xhr.status === 404) || xhr.statusText === 'NOT FOUND') {
            errMsg = $T('Your server is not registered with the Community Hub.');
        }
        if (!quiet) {
            $('<div>', { 'class': 'message-text', 'html' : errMsg })
                .appendTo(
                    $('<div>', { 'class': 'error-message-box' })
                        .appendTo($('#flashed-messages'))
            );
        }
        defer.reject(errMsg);
    });
    return defer.promise();
}

function initCephalopdOnSettingsPage(cephalopodUrl) {
    var $joined = $('#joined');
    var enabled = $joined.prop('checked');

    $joined.on('change', function() {
        enabled = $(this).prop('checked');
        $('#sync-button').prop('disabled', !enabled);
    });

    var defer = $.Deferred();
    $.when(defer).always(function(label) {
        $('#tracking-status')
            .attr('class', 'action-box ' + label.class)
            .find('.section > .icon')
                .attr('class', 'icon ' + label.icon)
                .next('.text')
                .children('.label')
                    .html(label.title)
                    .next()
                    .html(label.subtitle);
    });

    // Only check if synced, if enabled;
    if (!enabled) {
        defer.resolve({
            'title'   : $T('Disabled'),
            'subtitle': $T('Your are not part of the community.'),
            'class'   : 'disabled',
            'icon'    : 'icon-close'
        });
        return;
    }

    _isSynced(cephalopodUrl, {
        'enabled'     : $('#joined').prop('checked'),
        'contact'     : $('#contact_name').val(),
        'email'       : $('#contact_email').val(),
        'url'         : $('#server-url').html(),
        'organisation': $('#affiliation').html()
    }, true).done(function onSuccess(synced) {
        if (synced) {
            defer.resolve({
                'title'   : $T('Synchronized'),
                'subtitle': $T('You are part of the community and your Indico server is up to date.'),
                'class'   : 'highlight',
                'icon'    : 'icon-checkmark'
            });
        } else {
            $('#sync-tracking').show();
            defer.resolve({
                'title'   : $T('Out of sync'),
                'subtitle': $T('Your Indico server is out of sync. Synchronize it with the button on the right.'),
                'class'   : 'warning',
                'icon'    : 'icon-warning'
            });
        }
    }).fail(function onError(err) {
        defer.reject({
            'title'   : $T('Error!'),
            'subtitle': err,
            'class'   : 'danger',
            'icon'    :'icon-disable'});
    });
}

function initCephalopodOnAdminPage(cephalopodUrl, checkData, settingsUrl) {
    _isSynced(cephalopodUrl, checkData).done(function onSuccess(synced) {
        if (!synced) {
            $('<div>', {
                'class': 'message-text',
                'html' : $T('Your Indico server is not synchronized with the Community Hub! You can solve this <a href="{0}">here</a>.')
                            .format(settingsUrl)
            }).appendTo(
                $('<div>', { 'class': 'warning-message-box' })
                    .appendTo($('#flashed-messages'))
            );
        }
    });
}
