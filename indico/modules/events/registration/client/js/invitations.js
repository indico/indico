// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */
/* global handleAjaxError:false */

import React from 'react';
import ReactDOM from 'react-dom';

import EmailPendingInvitationsButton from './components/EmailPendingInvitationsButton';

(function(global) {
  global.setupInvitationPage = function setupInvitationPage({
    eventId,
    regformId,
    hasPendingInvitations,
  }) {
    $('#invitation-list').on('indico:confirmed', '.js-invitation-action', function(evt) {
      evt.preventDefault();

      const $this = $(this);
      $.ajax({
        url: $this.data('href'),
        method: $this.data('method'),
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success(data) {
          $('#invitation-list').html(data.invitation_list);
          renderEmailInvitationsBtn({
            eventId,
            regformId,
            hasPendingInvitations: data.has_pending_invitations,
          });
        },
      });
    });

    $('.js-invite-user').ajaxDialog({
      onClose(data) {
        if (data) {
          $('#invitation-list').html(data.invitation_list);
          renderEmailInvitationsBtn({
            eventId,
            regformId,
            hasPendingInvitations: data.has_pending_invitations,
          });
        }
      },
    });

    renderEmailInvitationsBtn({eventId, regformId, hasPendingInvitations});
  };

  function renderEmailInvitationsBtn({eventId, regformId, hasPendingInvitations}) {
    const container = document.getElementById('email-pending-invitations-container');
    ReactDOM.render(
      <EmailPendingInvitationsButton
        eventId={eventId}
        regformId={regformId}
        hasPendingInvitations={hasPendingInvitations}
      />,
      container
    );
  }
})(window);
