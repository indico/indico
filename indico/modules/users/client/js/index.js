// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  'use strict';

  global.setupRegistrationRequestList = function setupRegistrationRequestList() {
    var container = $('#registration-requests');
    container.on('indico:confirmed', '.js-process-request', function(evt) {
      evt.preventDefault();

      var $this = $(this);
      $.ajax({
        url: $this.data('href'),
        type: $this.data('method'),
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success: function(data) {
          handleFlashes(data);
          $this.closest('tr').remove();
          if (!container.find('tr:not(.js-no-requests)').length) {
            container.find('.js-no-requests').show();
          }
        },
      });
    });
  };
})(window);
