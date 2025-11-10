// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';

import {Translate} from 'indico/react/i18n';

import InviteDialog from './InviteDialog';

export default function InviteDialogButton({eventId, regformId, onInvitationsChanged}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button type="button" className="i-button icon-user" onClick={() => setOpen(true)}>
        <Translate>Invite</Translate>
      </button>
      {open && (
        <InviteDialog
          eventId={eventId}
          regformId={regformId}
          onSuccess={onInvitationsChanged}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

InviteDialogButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  regformId: PropTypes.number.isRequired,
  onInvitationsChanged: PropTypes.func.isRequired,
};
