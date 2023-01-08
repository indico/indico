// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {Button} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {EmailParticipantRoles} from './EmailParticipantRoles';
import {getIds} from './util';

export function EmailParticipantRolesButton({
  eventId,
  roleId,
  personSelector,
  userSelector,
  triggerSelector,
  noAccount,
  notInvitedOnly,
}) {
  const [open, setOpen] = useState(false);
  const personIds = getIds(personSelector);
  const userIds = getIds(userSelector);

  useEffect(() => {
    if (!triggerSelector) {
      return;
    }
    const handler = () => setOpen(true);
    const element = document.querySelector(triggerSelector);
    element.addEventListener('click', handler);
    return () => element.removeEventListener('click', handler);
  }, [triggerSelector]);

  return (
    <>
      {!triggerSelector && (
        <Translate as={Button} onClick={() => setOpen(true)}>
          Send email
        </Translate>
      )}
      {open && (
        <EmailParticipantRoles
          eventId={eventId}
          personIds={personIds}
          userIds={userIds}
          roleIds={roleId && [roleId]}
          noAccount={noAccount}
          notInvitedOnly={notInvitedOnly}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

EmailParticipantRolesButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  roleId: PropTypes.number,
  personSelector: PropTypes.string,
  userSelector: PropTypes.string,
  triggerSelector: PropTypes.string,
  noAccount: PropTypes.bool,
  notInvitedOnly: PropTypes.bool,
};

EmailParticipantRolesButton.defaultProps = {
  roleId: undefined,
  personSelector: undefined,
  userSelector: undefined,
  triggerSelector: undefined,
  noAccount: false,
  notInvitedOnly: false,
};
