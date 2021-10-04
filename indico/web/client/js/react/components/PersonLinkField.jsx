// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details

import PropTypes from 'prop-types';
import React, {useMemo, useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Segment, List, Modal, Form} from 'semantic-ui-react';

import {UserSearch} from 'indico/react/components/principals/Search';
import {FinalDropdown, FinalInput} from 'indico/react/forms';
import {useFavoriteUsers} from 'indico/react/hooks';
import {snakifyKeys} from 'indico/utils/case';

import {Translate} from '../i18n';

import {PersonListItem} from './principals/items';
import {PrincipalType} from './principals/util';

import './PersonLinkField.module.scss';

const titles = [
  {text: 'None', value: ''},
  {text: 'Mr', value: 'Mr'},
  {text: 'Ms', value: 'Ms'},
  {text: 'Mrs', value: 'Mrs'},
  {text: 'Dr', value: 'Dr'},
  {text: 'Prof', value: 'Prof'},
  {text: 'Mx', value: 'Mx'},
];

function ExternalPersonModal({open, onSubmit, onClose, person}) {
  const modal = ({handleSubmit}) => (
    <Modal as={Form} size="tiny" open={open} onClose={onClose} onSubmit={handleSubmit}>
      <Translate as={Modal.Header}>Enter Person</Translate>
      <Modal.Content>
        <Form.Group widths="equal">
          <Form.Field>
            <Translate as="label">Title</Translate>
            <FinalDropdown
              name="title"
              placeholder="Title"
              fluid
              search
              selection
              options={titles}
            />
          </Form.Field>
          <Form.Field>
            <Translate as="label">Family Name</Translate>
            <FinalInput name="lastName" required />
          </Form.Field>
        </Form.Group>
        <Form.Group widths="equal">
          <Form.Field>
            <Translate as="label">First Name</Translate>
            <FinalInput name="firstName" />
          </Form.Field>
          <Form.Field>
            <Translate as="label">Affiliation</Translate>
            <FinalInput name="affiliation" />
          </Form.Field>
        </Form.Group>
        <Form.Field>
          <Translate as="label">Email</Translate>
          <FinalInput name="email" />
        </Form.Field>
        <Form.Group widths="equal">
          <Form.Field>
            <Translate as="label">Address</Translate>
            <FinalInput name="address" />
          </Form.Field>
          <Form.Field>
            <Translate as="label">Telephone</Translate>
            <FinalInput name="telephone" />
          </Form.Field>
        </Form.Group>
      </Modal.Content>
      <Modal.Actions>
        <Translate as={Button} type="submit" primary>
          Confirm
        </Translate>
        <Translate as={Button} onClick={onClose}>
          Cancel
        </Translate>
      </Modal.Actions>
    </Modal>
  );

  return <FinalForm initialValues={person} onSubmit={onSubmit} render={modal} />;
}

ExternalPersonModal.propTypes = {
  open: PropTypes.bool,
  onSubmit: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
  person: PropTypes.object,
};

ExternalPersonModal.defaultProps = {
  open: false,
  person: undefined,
};

export function WTFPersonLinkField({fieldId, eventId, defaultValue, roles}) {
  const [persons, setPersons] = useState(defaultValue);
  const inputField = useMemo(() => document.getElementById(fieldId), [fieldId]);

  const onChange = value => {
    // TODO: displayOrder
    inputField.value = JSON.stringify(snakifyKeys(value));
    setPersons(value);
    inputField.dispatchEvent(new Event('change', {bubbles: true}));
  };

  return <PersonLinkField value={persons} eventId={eventId} onChange={onChange} roles={roles} />;
}

WTFPersonLinkField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  defaultValue: PropTypes.array,
  eventId: PropTypes.number,
  roles: PropTypes.array,
};

WTFPersonLinkField.defaultProps = {
  defaultValue: [],
  eventId: null,
  roles: [],
};

// TODO: strip out unnecessary person data
export default function PersonLinkField({
  value: persons,
  onChange,
  emptyMessage,
  eventId,
  sessionUser,
  roles,
}) {
  const [favoriteUsers] = useFavoriteUsers();
  const [modalOpen, setModalOpen] = useState(false);
  const [selected, setSelected] = useState(null);

  const onClose = () => {
    setSelected(null);
    setModalOpen(false);
  };

  const onEdit = idx => {
    setSelected(idx);
    setModalOpen(true);
  };

  const onSubmit = data => {
    onChange(
      selected !== null
        ? persons.map((v, idx) => (idx === selected ? data : v))
        : [...persons, data]
    );
    onClose();
  };

  const onChangeRoles = (idx, value) => {
    const keys = value.filter(r => r.active).map(r => r.value);
    onChange(persons.map((v, i) => (i === idx ? {...v, roles: keys} : v)));
  };

  return (
    <>
      <Segment attached="top">
        {persons.length > 0 ? (
          <List divided relaxed>
            {persons.map(
              (
                {userId, firstName, lastName, email, affiliation, avatarURL, roles: roleKeys},
                idx
              ) => (
                <PersonListItem
                  key={userId || email}
                  type={PrincipalType.user}
                  name={firstName ? `${firstName} ${lastName}` : lastName}
                  detail={affiliation ? `${email} (${affiliation})` : email}
                  avatarURL={avatarURL}
                  onDelete={() => onChange(persons.filter(p => p.userId !== userId))}
                  onEdit={() => onEdit(idx)}
                  roles={roles.map(({value, label}) => ({
                    value,
                    label,
                    active: roleKeys && roleKeys.includes(value),
                  }))}
                  onChangeRoles={v => onChangeRoles(idx, v)}
                  canDelete
                />
              )
            )}
          </List>
        ) : (
          emptyMessage || <Translate>There are currently no persons</Translate>
        )}
      </Segment>
      <Button.Group size="small" attached="bottom" floated="right">
        {sessionUser && (
          <Button type="button" onClick={() => onChange([...persons, sessionUser])}>
            Add myself
          </Button>
        )}
        <UserSearch
          favorites={favoriteUsers}
          existing={persons.map(u => `User:${u.userId}`)}
          onAddItems={i => onChange([...persons, ...i])}
          triggerFactory={props => (
            // eslint-disable-next-line react/react-in-jsx-scope
            <Button {...props} type="button">
              Search
            </Button>
          )}
          withEventPersons={eventId !== null}
          eventId={eventId}
        />
        <Button type="button" onClick={() => setModalOpen(true)}>
          Enter manually
        </Button>
        <ExternalPersonModal
          open={modalOpen}
          onClose={onClose}
          onSubmit={onSubmit}
          person={persons[selected]}
        />
      </Button.Group>
    </>
  );
}

PersonLinkField.propTypes = {
  value: PropTypes.array.isRequired,
  onChange: PropTypes.func.isRequired,
  emptyMessage: PropTypes.string,
  sessionUser: PropTypes.object,
  eventId: PropTypes.number,
  roles: PropTypes.array,
};

PersonLinkField.defaultProps = {
  emptyMessage: null,
  sessionUser: null,
  eventId: null,
  roles: [],
};
