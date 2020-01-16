// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  'use strict';

  global.setupPrincipalWidget = function setupPrincipalWidget(options) {
    options = $.extend(
      true,
      {
        fieldId: null,
        eventId: null,
        required: false,
        allowExternal: false,
      },
      options
    );

    var field = $('#' + options.fieldId);
    var button = $('#choose-' + options.fieldId);
    var display = $('#display-' + options.fieldId);

    if (!options.required) {
      display.clearableinput({
        clearOnEscape: false,
        focusOnClear: false,
        onClear: function() {
          field.principalfield('remove');
        },
      });
    }

    field.principalfield({
      eventId: options.eventId,
      allowExternalUsers: options.allowExternal,
      enableGroupsTab: false,
      render: function(users) {
        var name = users[0] ? users[0].name : '';
        if (!options.required) {
          display.clearableinput('setValue', name);
        } else {
          display.val(name);
        }
      },
    });

    display.add(button).on('click', function() {
      field.principalfield('choose');
    });
  };
})(window);
