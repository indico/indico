// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */

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
    renderEmailInvitationsBtn({
      containerId: 'email-all-pending-invitations-container',
      eventId,
      regformId,
      hasPendingInvitations,
    });

    renderInvitationsList({
      containerId: 'invitation-list-container',
      eventId,
      regformId,
      invitations,
    });
  };

  function renderEmailInvitationsBtn({containerId, eventId, regformId, hasPendingInvitations}) {
    const container = document.getElementById(containerId);
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

  function renderInvitationsList({containerId, eventId, regformId, invitations}) {
    const container = document.getElementById(containerId);
    ReactDOM.render(
      <InvitationList
        eventId={eventId}
        regformId={regformId}
        invitations={camelizeKeys(invitations)}
      />,
      container
    );
  }
})(window);
