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
  personIds,
  userIds,
  personSelector,
  userSelector,
  triggerSelector,
  noAccount,
  notInvitedOnly,
  ...rest
}) {
  const [open, setOpen] = useState(false);
  personIds = personSelector ? getIds(personSelector) : personIds;
  userIds = userSelector ? getIds(userSelector) : userIds;

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
        <Button
          onClick={() => setOpen(true)}
          disabled={!(personIds.length || userIds.length || roleId)}
          {...rest}
        >
          <Translate>Send emails</Translate>
        </Button>
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
  personIds: PropTypes.arrayOf(PropTypes.number),
  userIds: PropTypes.arrayOf(PropTypes.number),
  personSelector: PropTypes.string,
  userSelector: PropTypes.string,
  triggerSelector: PropTypes.string,
  noAccount: PropTypes.bool,
  notInvitedOnly: PropTypes.bool,
};

EmailParticipantRolesButton.defaultProps = {
  roleId: undefined,
  personIds: [],
  userIds: [],
  personSelector: undefined,
  userSelector: undefined,
  triggerSelector: undefined,
  noAccount: false,
  notInvitedOnly: false,
};
