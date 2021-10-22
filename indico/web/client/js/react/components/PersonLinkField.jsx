// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details

import PropTypes from 'prop-types';
import React, {useMemo, useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Segment, List, Modal, Form, Label, Icon} from 'semantic-ui-react';

import {UserSearch} from 'indico/react/components/principals/Search';
import {PrincipalType} from 'indico/react/components/principals/util';
import {FinalDropdown, FinalInput} from 'indico/react/forms';
import {useFavoriteUsers} from 'indico/react/hooks';
import {snakifyKeys} from 'indico/utils/case';

import {Translate} from '../i18n';

import {PrincipalItem} from './principals/items';

import './PersonLinkField.module.scss';

const titles = [
  {text: Translate.string('None'), value: ''},
  {text: Translate.string('Mr'), value: 'Mr'},
  {text: Translate.string('Ms'), value: 'Ms'},
  {text: Translate.string('Mrs'), value: 'Mrs'},
  {text: Translate.string('Dr'), value: 'Dr'},
  {text: Translate.string('Prof'), value: 'Prof'},
  {text: Translate.string('Mx'), value: 'Mx'},
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

const PersonListItem = ({
  meta,
  invalid,
  name,
  detail,
  avatarURL,
  canDelete,
  onDelete,
  onEdit,
  disabled,
  roles,
  onChangeRoles,
}) => (
  <PrincipalItem as={List.Item}>
    <PrincipalItem.Icon
      type={PrincipalType.user}
      meta={meta}
      invalid={invalid}
      avatarURL={avatarURL}
      styleName="icon"
    />
    <PrincipalItem.Content name={name} detail={detail} />
    <div styleName="roles">
      {roles &&
        roles.map(({name: roleName, label, icon, active}, idx) => (
          <Label
            as="a"
            size="small"
            key={roleName}
            color={active ? 'blue' : undefined}
            onClick={() =>
              onChangeRoles &&
              onChangeRoles(idx, roles.map((r, i) => (i === idx ? {...r, active: !active} : r)))
            }
          >
            {icon ? <Icon styleName="label-icon" name={icon} /> : label}
          </Label>
        ))}
    </div>
    <div styleName="actions">
      <Icon
        styleName="button edit"
        name="pencil alternate"
        size="large"
        onClick={onEdit}
        disabled={disabled}
      />
      {canDelete && (
        <Icon
          styleName="button delete"
          name="remove"
          size="large"
          onClick={onDelete}
          disabled={disabled}
        />
      )}
    </div>
  </PrincipalItem>
);

PersonListItem.propTypes = {
  invalid: PropTypes.bool,
  name: PropTypes.string.isRequired,
  detail: PropTypes.string,
  meta: PropTypes.object,
  onDelete: PropTypes.func,
  canDelete: PropTypes.bool,
  onEdit: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  avatarURL: PropTypes.string,
  roles: PropTypes.array,
  onChangeRoles: PropTypes.func,
};

PersonListItem.defaultProps = {
  canDelete: true,
  disabled: false,
  invalid: false,
  detail: null,
  meta: {},
  avatarURL: null,
  onDelete: null,
  roles: null,
  onChangeRoles: null,
};

const PersonLinkSection = ({
  label: sectionLabel,
  persons,
  defaultRoles,
  onChange,
  onEdit,
  canDelete,
}) => {
  const onChangeRoles = (personIndex, roleIndex, roles) => {
    const role = defaultRoles[roleIndex];
    const keys = roles
      .filter((r, i) => r.active && (roleIndex === i || !role.section || !defaultRoles[i].section))
      .map(r => r.name);
    onChange(persons.map((v, i) => (i === personIndex ? {...v, roles: keys} : v)));
  };

  const renderPersons = () =>
    persons.map(({userId, firstName, lastName, email, affiliation, avatarURL, roles}, idx) => (
      <PersonListItem
        key={userId || email}
        name={firstName ? `${firstName} ${lastName}` : lastName}
        detail={affiliation ? `${email} (${affiliation})` : email}
        avatarURL={avatarURL}
        onDelete={() => onChange(persons.filter((_, i) => i !== idx))}
        onEdit={() => onEdit(idx)}
        roles={defaultRoles.map(({name, ...rest}) => ({
          ...rest,
          name,
          active: roles && roles.includes(name),
        }))}
        onChangeRoles={(roleIdx, value) => onChangeRoles(idx, roleIdx, value)}
        canDelete={canDelete}
      />
    ));

  return (
    <>
      {sectionLabel && <div styleName="titled-rule">{sectionLabel}</div>}
      <List divided relaxed>
        {persons.length > 0 ? renderPersons() : <Translate>There are no persons</Translate>}
      </List>
    </>
  );
};

PersonLinkSection.propTypes = {
  label: PropTypes.string,
  persons: PropTypes.array,
  defaultRoles: PropTypes.array,
  onChange: PropTypes.func.isRequired,
  onEdit: PropTypes.func.isRequired,
  canDelete: PropTypes.bool,
};

PersonLinkSection.defaultProps = {
  label: undefined,
  persons: [],
  defaultRoles: [],
  canDelete: true,
};

// TODO: Disable user search when not logged-in
export default function PersonLinkField({value: persons, onChange, eventId, sessionUser, roles}) {
  const [favoriteUsers] = useFavoriteUsers();
  const [modalOpen, setModalOpen] = useState(false);
  const [selected, setSelected] = useState(null);
  const sections = roles.filter(x => x.section);
  const sectionKeys = new Set(sections.map(x => x.name));
  const othersCondition = p => !p.roles || !p.roles.find(r => sectionKeys.has(r));
  const others = persons.filter(othersCondition);

  const onClose = () => {
    setSelected(null);
    setModalOpen(false);
  };

  const onEdit = idx => {
    setSelected(idx);
    setModalOpen(true);
  };

  const onAdd = values => {
    values.forEach(p => (p.roles = roles.filter(x => x.default).map(x => x.name)));
    onChange([...persons, ...values]);
  };

  const onSubmit = value => {
    if (selected !== null) {
      value.roles = roles.filter(x => x.default).map(x => x.name);
      onChange(persons.map((v, idx) => (idx === selected ? value : v)));
    } else {
      onAdd([value]);
    }
    onClose();
  };

  return (
    <div styleName="person-link-field">
      <Segment attached="top">
        {sections.map(({name, label}) => {
          const filterCondition = p => p.roles && p.roles.includes(name);
          const filtered = persons.filter(filterCondition);
          return (
            <PersonLinkSection
              key={name}
              label={label}
              persons={filtered}
              defaultRoles={roles}
              onEdit={idx => onEdit(persons.findIndex(p => p === filtered[idx]))}
              onChange={values => onChange(persons.filter(p => !filterCondition(p)).concat(values))}
            />
          );
        })}
        {others.length > 0 && (
          <PersonLinkSection
            label={sections.length > 0 ? Translate.string('Others') : undefined}
            persons={others}
            defaultRoles={roles}
            onEdit={idx => onEdit(persons.findIndex(p => p === others[idx]))}
            onChange={values => onChange(persons.filter(p => !othersCondition(p)).concat(values))}
          />
        )}
      </Segment>
      <Button.Group size="small" attached="bottom" floated="right">
        {sessionUser && (
          <Translate as={Button} type="button" onClick={() => onChange([...persons, sessionUser])}>
            Add myself
          </Translate>
        )}
        <UserSearch
          favorites={favoriteUsers}
          existing={persons.map(u => `User:${u.userId}`)}
          onAddItems={onAdd}
          triggerFactory={props => (
            // eslint-disable-next-line react/react-in-jsx-scope
            <Translate as={Button} {...props} type="button" disabled={!sessionUser}>
              Search
            </Translate>
          )}
          withEventPersons={eventId !== null}
          eventId={eventId}
        />
        <Translate as={Button} type="button" onClick={() => setModalOpen(true)}>
          Enter manually
        </Translate>
        <ExternalPersonModal
          open={modalOpen}
          onClose={onClose}
          onSubmit={onSubmit}
          person={persons[selected]}
        />
      </Button.Group>
    </div>
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
  emptyMessage: Translate.string('There are no persons'),
  sessionUser: null,
  eventId: null,
  roles: [],
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
