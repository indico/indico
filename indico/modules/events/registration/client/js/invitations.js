// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */
/* global handleAjaxError:false */

import React from 'react';
import ReactDOM from 'react-dom';

import {Translate} from 'indico/react/i18n';
import {camelizeKeys} from 'indico/utils/case';

import EmailPendingInvitationsButton from './components/EmailPendingInvitationsButton';
import InvitationList from './components/InvitationList';

(function(global) {
  global.setupInvitationPage = function setupInvitationPage({
    eventId,
    regformId,
    hasPendingInvitations,
    invitations,
  }) {
    $('#invitation-list-container').on('indico:confirmed', '.js-invitation-action', function(evt) {
      evt.preventDefault();

      const $this = $(this);
      $.ajax({
        url: $this.data('href'),
        method: $this.data('method'),
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success(data) {
          renderInvitationPage({
            eventId,
            regformId,
            hasPendingInvitations: data.has_pending_invitations,
            invitations: data.invitation_list,
          });
        },
      });
    });

    renderInvitationPage({
      eventId,
      regformId,
      hasPendingInvitations,
      invitations,
    });

    $('.js-invite-user').ajaxDialog({
      onClose(data) {
        if (data) {
          renderInvitationPage({
            eventId,
            regformId,
            hasPendingInvitations: data.has_pending_invitations,
            invitations: data.invitation_list,
          });
        }
      },
    });
  };

  function renderEmailInvitationsBtn({eventId, regformId, hasPendingInvitations}) {
    const container = document.getElementById('email-all-pending-invitations-container');
    ReactDOM.render(
      <EmailPendingInvitationsButton
        eventId={eventId}
        regformId={regformId}
        label={Translate.string('Remind all')}
        disabled={!hasPendingInvitations}
      />,
      container
    );
  }

  function renderInvitationsList({eventId, regformId, invitations}) {
    const container = document.getElementById('invitation-list-container');
    ReactDOM.render(
      <InvitationList
        eventId={eventId}
        regformId={regformId}
        invitations={camelizeKeys(invitations)}
      />,
      container
    );
  }

  function renderInvitationPage({eventId, regformId, hasPendingInvitations, invitations}) {
    renderEmailInvitationsBtn({
      eventId,
      regformId,
      hasPendingInvitations,
    });
    renderInvitationsList({
      eventId,
      regformId,
      invitations,
    });
  }
})(window);
