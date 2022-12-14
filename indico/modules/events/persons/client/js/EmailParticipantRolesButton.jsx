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
  personIdentifiers,
  personSelector,
  userSelector,
  triggerSelector,
  noAccount,
  notInvitedOnly,
  onSubmitSucceded,
  successTimeout,
  ...rest
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
        <Button
          onClick={() => setOpen(true)}
          disabled={!(personIds.length || userIds.length || roleId || personIdentifiers.length)}
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
          personIdentifiers={personIdentifiers}
          noAccount={noAccount}
          notInvitedOnly={notInvitedOnly}
          onClose={() => setOpen(false)}
          onSubmitSucceded={onSubmitSucceded}
          successTimeout={successTimeout}
        />
      )}
    </>
  );
}

EmailParticipantRolesButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  roleId: PropTypes.number,
  personIdentifiers: PropTypes.arrayOf(PropTypes.string),
  personSelector: PropTypes.string,
  userSelector: PropTypes.string,
  triggerSelector: PropTypes.string,
  noAccount: PropTypes.bool,
  notInvitedOnly: PropTypes.bool,
  onSubmitSucceded: PropTypes.func,
  successTimeout: PropTypes.number,
};

EmailParticipantRolesButton.defaultProps = {
  roleId: undefined,
  personIdentifiers: [],
  personSelector: undefined,
  userSelector: undefined,
  triggerSelector: undefined,
  noAccount: false,
  notInvitedOnly: false,
  onSubmitSucceded: undefined,
  successTimeout: undefined,
};
