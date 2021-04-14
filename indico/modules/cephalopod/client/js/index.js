// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable max-len */

(function(global) {
  'use strict';

  /**
   * Check if the data returned by `cephalopodUrl` matches `localData`
   *
   * Performs an ajax request to retrieve the data to check and return a
   * jQuery promise with the a boolean indicating if the data matches or
   * not. If the ajax request fails, the promise is rejected wit the ajax
   * error. An error flash message is also shown on the page unless the
   * `quiet` option is set to `false` (defaults to `true`).
   */
  function _checkSynced(cephalopodUrl, localData, quiet) {
    quiet = quiet || false;
    var defer = $.Deferred();
    $.ajax({
      url: cephalopodUrl,
      type: 'GET',
      dataType: 'json',
      timeout: 10000, // 10 seconds
    })
      .done(function onSuccess(response) {
        var synced = true;
        _.each(localData, function(localVal, key) {
          if (localVal === response[key]) {
            return;
          }
          synced = false;
        });
        defer.resolve(synced);
      })
      .fail(function onError(xhr, status) {
        var errMsg = $T.gettext('Unknown error while contacting the Community Hub');
        if (xhr.state() === 'rejected' && xhr.status === 200 && status === 'parsererror') {
          errMsg = $T.gettext('Internal error: Parse error on the reply of the Community Hub.');
        } else if (xhr.state() === 'rejected' && xhr.status === 0 && status === 'error') {
          errMsg = $T.gettext('Unable to contact the Community Hub.');
        } else if (xhr.state() === 'rejected' && xhr.status === 0 && status === 'timeout') {
          errMsg = $T.gettext('The connection to the Community Hub timed out.');
        } else if (
          (xhr.state() === 'rejected' && xhr.status === 404) ||
          xhr.statusText === 'NOT FOUND'
        ) {
          errMsg = $T.gettext('Your server is not registered with the Community Hub.');
        }
        if (!quiet) {
          $('<div>', {class: 'message-text', html: errMsg}).appendTo(
            $('<div>', {class: 'error-message-box fixed-width'}).appendTo($('#flashed-messages'))
          );
        }
        defer.reject(errMsg);
      });
    return defer.promise();
  }

  global.setupCephalopodSettings = function setupCephalopodSettings(cephalopodUrl, enabled) {
    var $joined = $('#joined');

    $joined.on('change', function() {
      $('#sync-button').prop('disabled', !this.checked);
    });

    var dfd = $.Deferred();
    $.when(dfd).always(function(label) {
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
      dfd.resolve({
        title: $T.gettext('Disabled'),
        subtitle: $T.gettext('This server is not registered as part of the community.'),
        class: 'disabled',
        icon: 'icon-close',
      });
      return;
    }

    _checkSynced(
      cephalopodUrl,
      {
        enabled: $('#joined').prop('checked'),
        contact: $('#contact_name').val(),
        email: $('#contact_email').val(),
        url: $('#server-url').html(),
        organization: $('#affiliation').html(),
      },
      true
    )
      .done(function(synced) {
        if (synced) {
          dfd.resolve({
            title: $T.gettext('Synchronized'),
            subtitle: $T.gettext(
              'This server is registered as part of the community and is up to date.'
            ),
            class: 'highlight',
            icon: 'icon-checkmark',
          });
        } else {
          $('#sync-tracking').show();
          dfd.resolve({
            title: $T.gettext('Out of sync'),
            subtitle: $T.gettext(
              'Your Indico server is out of sync. Synchronize it with the button on the right.'
            ),
            class: 'warning',
            icon: 'icon-warning',
          });
        }
      })
      .fail(function(err) {
        dfd.reject({
          title: $T.gettext('Error!'),
          subtitle: err,
          class: 'danger',
          icon: 'icon-disable',
        });
      });
  };

  global.checkCephalopodSynced = function checkCephalopodSynced(
    cephalopodUrl,
    checkData,
    settingsUrl
  ) {
    _checkSynced(cephalopodUrl, checkData).done(function(synced) {
      if (!synced) {
        $('<div>', {
          class: 'message-text',
          html: $T
            .gettext(
              'Your Indico server is not synchronized with the Community Hub! You can solve this <a href="{0}">here</a>.'
            )
            .format(settingsUrl),
        }).appendTo(
          $('<div>', {class: 'warning-message-box fixed-width'}).appendTo($('#flashed-messages'))
        );
      }
    });
  };
})(window);
