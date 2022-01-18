// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useMemo, useState} from 'react';
import {DndProvider} from 'react-dnd';
import {HTML5Backend} from 'react-dnd-html5-backend';
import {Button, Segment, List, Form, Label, Icon, Popup, Message, Ref} from 'semantic-ui-react';

import {UserSearch} from 'indico/react/components/principals/Search';
import {PrincipalType} from 'indico/react/components/principals/util';
import {FinalDropdown, FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {useFavoriteUsers} from 'indico/react/hooks';
import {SortableWrapper, useSortableItem} from 'indico/react/sortable';
import {snakifyKeys} from 'indico/utils/case';

import {Translate} from '../i18n';

import {PrincipalItem} from './principals/items';

import './PersonLinkField.module.scss';

const titles = [
  {text: Translate.string('Mr'), value: 'mr'},
  {text: Translate.string('Ms'), value: 'ms'},
  {text: Translate.string('Mrs'), value: 'mrs'},
  {text: Translate.string('Dr'), value: 'dr'},
  {text: Translate.string('Prof'), value: 'prof'},
  {text: Translate.string('Mx'), value: 'mx'},
];

const ExternalPersonModal = ({onSubmit, onClose, person}) => (
  <FinalModalForm
    id="person-link-details"
    size="tiny"
    onClose={onClose}
    onSubmit={onSubmit}
    header={Translate.string('Enter Person')}
    submitLabel={Translate.string('Save')}
    initialValues={person || {}}
  >
    {/* eslint-disable-next-line eqeqeq */}
    {person && person.userId != null && (
      <Translate as={Message}>
        You are updating details that were originally linked to a user. Please note that its
        identity will remain the same.
      </Translate>
    )}
    <Form.Group widths="equal">
      <Form.Field>
        <Translate as="label">Title</Translate>
        <FinalDropdown name="title" placeholder="Title" fluid search selection options={titles} />
      </Form.Field>
      <Form.Field>
        <Translate as="label">Affiliation</Translate>
        <FinalInput name="affiliation" />
      </Form.Field>
    </Form.Group>
    <Form.Group widths="equal">
      <Form.Field>
        <Translate as="label">First Name</Translate>
        <FinalInput name="firstName" />
      </Form.Field>
      <Form.Field>
        <Translate as="label">Family Name</Translate>
        <FinalInput name="lastName" required />
      </Form.Field>
    </Form.Group>
    <Form.Field>
      <Translate as="label">Email</Translate>
      <FinalInput name="email" required />
    </Form.Field>
    <Form.Group widths="equal">
      <Form.Field>
        <Translate as="label">Address</Translate>
        <FinalTextArea name="address" />
      </Form.Field>
      <Form.Field>
        <Translate as="label">Telephone</Translate>
        <FinalInput name="telephone" />
      </Form.Field>
    </Form.Group>
  </FinalModalForm>
);

ExternalPersonModal.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
  person: PropTypes.object,
};

ExternalPersonModal.defaultProps = {
  person: undefined,
};

const PersonListItem = ({
  person: {avatarURL, firstName, lastName, affiliation, email},
  roles,
  canDelete,
  onDelete,
  onEdit,
  onClickRole,
  disabled,
}) => (
  <PrincipalItem as={List.Item}>
    <PrincipalItem.Icon type={PrincipalType.user} avatarURL={avatarURL} styleName="icon" />
    <PrincipalItem.Content
      name={firstName ? `${firstName} ${lastName}` : lastName}
      detail={affiliation ? `${email} (${affiliation})` : email}
    />
    <div styleName="roles">
      {roles &&
        roles.map(({name: roleName, label, icon, active}, idx) => (
          <Popup
            key={roleName}
            trigger={
              <Label
                as="a"
                size="small"
                color={active ? 'blue' : undefined}
                onClick={() => onClickRole && onClickRole(idx, roles)}
              >
                {icon ? <Icon styleName="label-icon" name={icon} /> : label}
              </Label>
            }
            disabled={!icon}
            content={label}
            size="tiny"
          />
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
  person: PropTypes.object.isRequired,
  roles: PropTypes.array.isRequired,
  onDelete: PropTypes.func,
  canDelete: PropTypes.bool,
  onEdit: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  avatarURL: PropTypes.string,
  onClickRole: PropTypes.func,
};

PersonListItem.defaultProps = {
  canDelete: true,
  disabled: false,
  avatarURL: null,
  onDelete: null,
  onClickRole: null,
};

const DraggablePerson = ({drag, onMove, index, ...props}) => {
  const [dragRef, itemRef, style] = useSortableItem({
    type: 'person',
    index,
    moveItem: onMove,
    separateHandle: true,
  });
  return (
    <div ref={itemRef} style={style} styleName="drag-item">
      {!drag && (
        <Ref innerRef={dragRef}>
          <div className="icon-drag-indicator" styleName="handle" />
        </Ref>
      )}
      <div styleName="preview">
        <PersonListItem {...props} />
      </div>
    </div>
  );
};

DraggablePerson.propTypes = {
  drag: PropTypes.bool,
  onMove: PropTypes.func.isRequired,
  index: PropTypes.number.isRequired,
};

DraggablePerson.defaultProps = {
  drag: true,
};

const PersonLinkSection = ({
  label: sectionLabel,
  persons,
  defaultRoles,
  onChange,
  onEdit,
  canDelete,
  drag,
}) => {
  const onClickRole = (personIndex, roleIndex, value) => {
    const role = defaultRoles[roleIndex];
    const roles = value
      .filter((r, i) =>
        // ensure only a single section is selected at a time
        roleIndex === i ? !r.active : r.active && (!role.section || !defaultRoles[i].section)
      )
      .map(r => r.name);
    onChange(persons.map((v, i) => (i === personIndex ? {...v, roles} : v)));
  };

  const moveItem = (dragIndex, hoverIndex) => {
    const result = persons.slice();
    result.splice(hoverIndex, 0, ...result.splice(dragIndex, 1));
    onChange(result);
  };

  return (
    <SortableWrapper accept="person">
      {sectionLabel && <div styleName="titled-rule">{sectionLabel}</div>}
      <List divided relaxed>
        {persons.length > 0 ? (
          persons.map((p, idx) => (
            <DraggablePerson
              key={p.userId || p.email}
              index={idx}
              drag={!drag}
              onMove={moveItem}
              person={p}
              onDelete={() => onChange(persons.filter((__, i) => i !== idx))}
              onEdit={() => onEdit(idx)}
              onClickRole={(roleIdx, value) => onClickRole(idx, roleIdx, value)}
              canDelete={canDelete}
              roles={defaultRoles.map(({name, ...rest}) => ({
                ...rest,
                name,
                active: p.roles && p.roles.includes(name),
              }))}
            />
          ))
        ) : (
          <Translate>There are no persons</Translate>
        )}
      </List>
    </SortableWrapper>
  );
};

PersonLinkSection.propTypes = {
  label: PropTypes.string,
  persons: PropTypes.array,
  defaultRoles: PropTypes.array,
  onChange: PropTypes.func.isRequired,
  onEdit: PropTypes.func.isRequired,
  canDelete: PropTypes.bool,
  drag: PropTypes.bool,
};

PersonLinkSection.defaultProps = {
  label: undefined,
  persons: [],
  defaultRoles: [],
  canDelete: true,
  drag: false,
};

export default function PersonLinkField({
  value: persons,
  onChange,
  eventId,
  sessionUser,
  roles,
  emptyMessage,
  autoSort,
  setAutoSort,
}) {
  const [favoriteUsers] = useFavoriteUsers(null, !sessionUser);
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
    const existing = persons.map(p => p.email);
    values.forEach(p => (p.roles = roles.filter(x => x.default).map(x => x.name)));
    onChange([...persons, ...values.filter(v => !existing.includes(v.email))]);
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
      <DndProvider backend={HTML5Backend}>
        <Segment attached="top" styleName="segment">
          {sections.map(({name, label, plural}) => {
            const filterCondition = p => p.roles?.includes(name);
            const filtered = persons.filter(filterCondition);
            return filtered.length === 0 ? null : (
              <PersonLinkSection
                key={name}
                drag={!autoSort}
                label={plural || label}
                persons={filtered}
                defaultRoles={roles}
                onEdit={idx => onEdit(persons.findIndex(p => p === filtered[idx]))}
                onChange={values =>
                  onChange(persons.filter(p => !filterCondition(p)).concat(values))
                }
              />
            );
          })}
          {others.length > 0 && (
            <PersonLinkSection
              drag={!autoSort}
              label={sections.length > 0 ? Translate.string('Others') : undefined}
              persons={others}
              defaultRoles={roles}
              onEdit={idx => onEdit(persons.findIndex(p => p === others[idx]))}
              onChange={values => onChange(persons.filter(p => !othersCondition(p)).concat(values))}
            />
          )}
          {persons.length === 0 && (emptyMessage || <Translate>There are no persons</Translate>)}
        </Segment>
        <Button.Group size="small" attached="bottom" floated="right">
          <Button
            toggle
            icon="sort alphabet down"
            type="button"
            active={autoSort}
            onClick={() => setAutoSort && setAutoSort(!autoSort)}
          />
          {sessionUser && (
            <Translate
              as={Button}
              type="button"
              onClick={() => onAdd([sessionUser])}
              disabled={persons.some(p => p.userId === sessionUser.userId)}
            >
              Add myself
            </Translate>
          )}
          <UserSearch
            favorites={favoriteUsers}
            existing={persons.map(p => p.userIdentifier)}
            onAddItems={onAdd}
            triggerFactory={props => (
              <Button type="button" {...props}>
                <Translate>Search</Translate>
              </Button>
            )}
            withEventPersons={eventId !== null}
            eventId={eventId}
            disabled={!sessionUser}
          />
          <Translate as={Button} type="button" onClick={() => setModalOpen(true)}>
            Enter manually
          </Translate>
          {modalOpen && (
            <ExternalPersonModal onClose={onClose} onSubmit={onSubmit} person={persons[selected]} />
          )}
        </Button.Group>
      </DndProvider>
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
  autoSort: PropTypes.bool,
  setAutoSort: PropTypes.func,
};

PersonLinkField.defaultProps = {
  emptyMessage: null,
  sessionUser: null,
  eventId: null,
  roles: [],
  autoSort: true,
  setAutoSort: null,
};

export function WTFPersonLinkField({
  fieldId,
  eventId,
  defaultValue,
  roles,
  sessionUser,
  emptyMessage,
}) {
  const [persons, setPersons] = useState(
    defaultValue.sort((a, b) => a.displayOrder - b.displayOrder)
  );
  const [autoSort, _setAutoSort] = useState(persons.every(p => p.displayOrder === 0));
  const inputField = useMemo(() => document.getElementById(fieldId), [fieldId]);

  const onChange = (value, sort = autoSort) => {
    const picked = value.map(p =>
      _.pick(p, [
        'firstName',
        'lastName',
        'affiliation',
        'email',
        'address',
        'phone',
        'roles',
        'displayOrder',
      ])
    );
    inputField.value = JSON.stringify(
      snakifyKeys(picked.map((x, i) => ({...x, displayOrder: sort ? 0 : i})))
    );
    setPersons(value);
    inputField.dispatchEvent(new Event('change', {bubbles: true}));
  };

  const setAutoSort = value => {
    _setAutoSort(value);
    onChange(persons, value);
  };

  return (
    <PersonLinkField
      value={!autoSort ? persons : persons.slice().sort((a, b) => a.name.localeCompare(b.name))}
      eventId={eventId}
      onChange={onChange}
      roles={roles}
      sessionUser={sessionUser}
      emptyMessage={emptyMessage}
      autoSort={autoSort}
      setAutoSort={setAutoSort}
    />
  );
}

WTFPersonLinkField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  defaultValue: PropTypes.array,
  eventId: PropTypes.number,
  roles: PropTypes.array,
  sessionUser: PropTypes.object,
  emptyMessage: PropTypes.string,
};

WTFPersonLinkField.defaultProps = {
  defaultValue: [],
  eventId: null,
  roles: [],
  sessionUser: null,
  emptyMessage: null,
};
