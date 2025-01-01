// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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
  persons,
  personSelector,
  triggerSelector,
  noAccount,
  notInvitedOnly,
  onSubmitSucceeded,
  successTimeout,
  ...rest
}) {
  const [open, setOpen] = useState(false);
  persons = personSelector ? getIds(personSelector, false) : persons;

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
        <Button onClick={() => setOpen(true)} disabled={!(roleId || persons.length)} {...rest}>
          <Translate>Send email</Translate>
        </Button>
      )}
      {open && (
        <EmailParticipantRoles
          eventId={eventId}
          roleIds={roleId && [roleId]}
          persons={persons}
          noAccount={noAccount}
          notInvitedOnly={notInvitedOnly}
          onClose={() => setOpen(false)}
          onSubmitSucceeded={onSubmitSucceeded}
          successTimeout={successTimeout}
        />
      )}
    </>
  );
}

EmailParticipantRolesButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  roleId: PropTypes.number,
  persons: PropTypes.arrayOf(PropTypes.string),
  personSelector: PropTypes.string,
  triggerSelector: PropTypes.string,
  noAccount: PropTypes.bool,
  notInvitedOnly: PropTypes.bool,
  onSubmitSucceeded: PropTypes.func,
  successTimeout: PropTypes.number,
};

EmailParticipantRolesButton.defaultProps = {
  roleId: undefined,
  persons: [],
  personSelector: undefined,
  triggerSelector: undefined,
  noAccount: false,
  notInvitedOnly: false,
  onSubmitSucceeded: undefined,
  successTimeout: undefined,
};
