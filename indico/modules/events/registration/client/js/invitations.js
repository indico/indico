// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  'use strict';

  global.setupInvitationPage = function setupInvitationPage() {
    $('#invitation-list').on('indico:confirmed', '.js-invitation-action', function(evt) {
      evt.preventDefault();

      var $this = $(this);
      $.ajax({
        url: $this.data('href'),
        method: $this.data('method'),
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success: function(data) {
          $('#invitation-list').html(data.invitation_list);
        },
      });
    });

    $('.js-invite-user').ajaxDialog({
      onClose: function(data) {
        if (data) {
          $('#invitation-list').html(data.invitation_list);
        }
      },
    });
  };
})(window);
