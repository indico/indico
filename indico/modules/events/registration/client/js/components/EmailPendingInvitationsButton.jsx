// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import emailMetadataURL from 'indico-url:event_registration.api_invitations_reminders_metadata';
import emailPreviewURL from 'indico-url:event_registration.api_invitations_reminders_preview';
import emailSendURL from 'indico-url:event_registration.api_invitations_reminders_send';

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';

import {Translate} from 'indico/react/i18n';

import EmailPendingInvitations from './EmailPendingInvitations';

const getIds = checkboxes =>
  Array.from(checkboxes)
    .filter(e => e.checked && (e.offsetWidth > 0 || e.offsetHeight > 0))
    .map(e => +e.value);

export default function EmailPendingInvitationsButton({
  eventId,
  regformId,
  checkboxSelector,
  hasPendingInvitations,
}) {
  const [open, setOpen] = useState(false);
  const metadataURL = emailMetadataURL({event_id: eventId, reg_form_id: regformId});
  const previewURL = emailPreviewURL({event_id: eventId, reg_form_id: regformId});
  const sendURL = emailSendURL({event_id: eventId, reg_form_id: regformId});
  const [selectedInvitations, setSelectedInvitations] = useState([]);

  useEffect(() => {
    if (!checkboxSelector) {
      return;
    }
    const checkboxes = document.querySelectorAll(checkboxSelector);
    const handler = () => setSelectedInvitations(getIds(checkboxes));
    checkboxes.forEach(c => c.addEventListener('change', handler));
    return () => checkboxes.forEach(c => c.removeEventListener('change', handler));
  }, [checkboxSelector]);

  return (
    <>
      <button
        type="button"
        className="i-button icon-mail"
        disabled={!hasPendingInvitations || (checkboxSelector && !selectedInvitations.length)}
        onClick={() => setOpen(true)}
      >
        {checkboxSelector ? Translate.string('Send reminders') : Translate.string('Remind all')}
      </button>
      {open && (
        <EmailPendingInvitations
          metadataURL={metadataURL}
          previewURL={previewURL}
          sendURL={sendURL}
          selectedInvitations={selectedInvitations}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

EmailPendingInvitationsButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  regformId: PropTypes.number.isRequired,
  checkboxSelector: PropTypes.string,
  hasPendingInvitations: PropTypes.bool.isRequired,
};

EmailPendingInvitationsButton.defaultProps = {
  checkboxSelector: '',
};
