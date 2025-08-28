// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {Message} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {toClasses} from 'indico/react/util';

import EmailPendingInvitationsButton from './EmailPendingInvitationsButton';

interface Invitation {
  id: number;
  state: 'pending' | 'accepted' | 'declined';
  firstName: string;
  lastName: string;
  email: string;
  affiliation: string;
  registrationDetailsURL?: string;
  declineURL: string;
  deleteURL: string;
}

function InvitationRow({
  invitation,
  selected,
  onChange,
}: {
  invitation: Invitation;
  selected: number[];
  onChange?: (selected: number[]) => void;
}) {
  const {
    id,
    state,
    firstName,
    lastName,
    email,
    affiliation,
    registrationDetailsURL,
    declineURL,
    deleteURL,
  } = invitation;

  const name = registrationDetailsURL ? (
    <a href={registrationDetailsURL}>
      {firstName} {lastName}
    </a>
  ) : (
    `${firstName} ${lastName}`
  );

  const handleChange = () => {
    if (!onChange) {
      return;
    }
    const newSelected = selected.includes(id)
      ? selected.filter(selectedId => id !== selectedId)
      : [...selected, id];
    onChange(newSelected);
  };

  return (
    <tr>
      {onChange && (
        <td className="select">
          <input
            type="checkbox"
            name="invitation_ids"
            className="hide-if-locked"
            autoComplete="off"
            id={`invitation-${id}`}
            checked={selected.includes(id)}
            onChange={handleChange}
          />
        </td>
      )}
      <td className="name" onClick={handleChange}>
        {name}
      </td>
      <td className="email" onClick={handleChange}>
        {email}
      </td>
      <td className="affiliation" onClick={handleChange}>
        {affiliation}
      </td>
      <td className="actions hide-if-locked">
        {state === 'pending' && (
          <a
            className="icon-disable js-invitation-action"
            title={Translate.string('Mark as declined')}
            data-href={declineURL}
            data-method="POST"
            data-title={Translate.string('Mark invitation as declined')}
            data-confirm={Translate.string(
              'Do you really want to mark this invitation as declined by the invitee?'
            )}
          />
        )}
        <a
          className="icon-remove js-invitation-action"
          title={Translate.string('Delete invitation')}
          data-href={deleteURL}
          data-method="DELETE"
          data-title={Translate.string('Delete invitation')}
          data-confirm={Translate.string('Do you really want to delete this invitation?')}
        />
      </td>
    </tr>
  );
}

function InvitationsBlock({
  title,
  invitations,
  selected = [],
  onChange,
}: {
  title: string;
  invitations: Invitation[];
  selected?: number[];
  onChange?: (selected: number[]) => void;
}) {
  return (
    <>
      <div className="titled-rule">{title}</div>
      <table className={toClasses({'invitation-table': true, selectable: !!onChange})}>
        <tbody>
          {invitations.map(invitation => (
            <InvitationRow
              key={invitation.id}
              invitation={invitation}
              selected={selected}
              onChange={onChange}
            />
          ))}
        </tbody>
      </table>
    </>
  );
}

export default function InvitationList({
  eventId,
  regformId,
  invitations,
}: {
  eventId: number;
  regformId: number;
  invitations: Invitation[];
}) {
  const [_selectedInvitations, setSelectedInvitations] = useState<number[]>([]);
  const invitationIds = new Set(invitations.map(inv => inv.id));
  const selectedInvitations = _selectedInvitations.filter(inv => invitationIds.has(inv));
  const pendingInvitations = invitations.filter(i => i.state === 'pending');
  const acceptedInvitations = invitations.filter(i => i.state === 'accepted');
  const declinedInvitations = invitations.filter(i => i.state === 'declined');

  if (invitations.length === 0) {
    return (
      <Message icon="info circle" content={Translate.string('Nobody has been invited yet.')} info />
    );
  }

  return (
    <div
      className={toClasses({
        'i-box': true,
        'invitation-list': true,
        titled: pendingInvitations.length === 0,
      })}
    >
      {pendingInvitations.length > 0 && (
        <>
          <div className="toolbar hide-if-locked">
            <EmailPendingInvitationsButton
              eventId={eventId}
              regformId={regformId}
              selectedInvitations={selectedInvitations}
              label={Translate.string('Send reminders')}
              disabled={selectedInvitations.length === 0}
            />
          </div>
          <InvitationsBlock
            title={Translate.string('Pending invitations')}
            invitations={pendingInvitations}
            selected={selectedInvitations}
            onChange={setSelectedInvitations}
          />
        </>
      )}
      {acceptedInvitations.length > 0 && (
        <InvitationsBlock
          title={Translate.string('Accepted invitations')}
          invitations={acceptedInvitations}
        />
      )}
      {declinedInvitations.length > 0 && (
        <InvitationsBlock
          title={Translate.string('Declined invitations')}
          invitations={declinedInvitations}
        />
      )}
    </div>
  );
}
