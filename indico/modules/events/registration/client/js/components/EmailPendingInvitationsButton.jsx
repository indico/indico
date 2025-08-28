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
import React, {useState} from 'react';

import EmailPendingInvitations from './EmailPendingInvitations';

export default function EmailPendingInvitationsButton({
  eventId,
  regformId,
  selectedInvitations,
  label,
  disabled,
}) {
  const [open, setOpen] = useState(false);
  const metadataURL = emailMetadataURL({event_id: eventId, reg_form_id: regformId});
  const previewURL = emailPreviewURL({event_id: eventId, reg_form_id: regformId});
  const sendURL = emailSendURL({event_id: eventId, reg_form_id: regformId});

  return (
    <>
      <button
        type="button"
        className="i-button icon-mail"
        disabled={disabled}
        onClick={() => setOpen(true)}
      >
        {label}
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
  selectedInvitations: PropTypes.arrayOf(PropTypes.number),
  label: PropTypes.string.isRequired,
  disabled: PropTypes.bool.isRequired,
};

EmailPendingInvitationsButton.defaultProps = {
  selectedInvitations: null,
};
