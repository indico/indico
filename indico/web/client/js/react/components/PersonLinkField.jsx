// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useMemo, useState} from 'react';
import {DndProvider} from 'react-dnd';
import {HTML5Backend} from 'react-dnd-html5-backend';
import {Button, Segment, List, Label, Icon, Popup, Ref} from 'semantic-ui-react';

import {UserSearch} from 'indico/react/components/principals/Search';
import {PrincipalType} from 'indico/react/components/principals/util';
import {useFavoriteUsers} from 'indico/react/hooks';
import {SortableWrapper, useSortableItem} from 'indico/react/sortable';
import {snakifyKeys} from 'indico/utils/case';
import {getPluginObjects, renderPluginComponents} from 'indico/utils/plugins';

import {Translate} from '../i18n';

import PersonDetailsModal from './PersonDetailsModal';
import {PrincipalItem} from './principals/items';

import './PersonLinkField.module.scss';

const PersonListItem = ({
  person,
  roles,
  canEdit,
  canDelete,
  onDelete,
  onEdit,
  onClickRole,
  disabled,
  extraParams,
}) => (
  <PrincipalItem as={List.Item} styleName="principal">
    <PrincipalItem.Icon type={PrincipalType.user} avatarURL={person.avatarURL} styleName="icon" />
    <PrincipalItem.Content
      name={person.name}
      detail={
        (person.email ? `${person.email} ` : '') +
        (person.affiliation ? `(${person.affiliation})` : '')
      }
    />
    <div styleName="roles">
      {roles &&
        roles.map(({name, label, icon, active}, idx) => (
          <Popup
            key={name}
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
      {renderPluginComponents('personListItemActions', {person, onEdit, disabled, extraParams})}
      {canEdit && (
        <Icon
          styleName="button edit"
          name="pencil alternate"
          title={Translate.string('Edit person')}
          size="large"
          onClick={() => onEdit('details')}
          disabled={disabled}
        />
      )}
      {canDelete && (
        <Icon
          styleName="button delete"
          name="remove"
          title={Translate.string('Delete person')}
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
  canEdit: PropTypes.bool,
  disabled: PropTypes.bool,
  avatarURL: PropTypes.string,
  onClickRole: PropTypes.func,
  extraParams: PropTypes.object,
};

PersonListItem.defaultProps = {
  canEdit: true,
  canDelete: true,
  disabled: false,
  avatarURL: null,
  onDelete: null,
  onClickRole: null,
  extraParams: {},
};

const DraggablePerson = ({drag, dragType, onMove, index, ...props}) => {
  const [dragRef, itemRef, style] = useSortableItem({
    type: `person-${dragType}`,
    index,
    moveItem: onMove,
    separateHandle: true,
  });
  return (
    <div ref={itemRef} style={style} styleName="person-link">
      {!drag && (
        <Ref innerRef={dragRef}>
          <div className="icon-drag-indicator" styleName="handle" />
        </Ref>
      )}
      <PersonListItem {...props} />
    </div>
  );
};

DraggablePerson.propTypes = {
  drag: PropTypes.bool,
  dragType: PropTypes.string.isRequired,
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
  canEdit,
  canDelete,
  drag,
  dragType,
  extraParams,
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
    <SortableWrapper accept={`person-${dragType}`}>
      {sectionLabel && <div styleName="titled-rule">{sectionLabel}</div>}
      <List divided relaxed>
        {persons.length > 0 ? (
          persons.map((p, idx) => (
            <DraggablePerson
              key={p.userId || p.email || p.firstName + p.lastName}
              index={idx}
              drag={!drag}
              dragType={dragType}
              onMove={moveItem}
              person={p}
              onDelete={() => onChange(persons.filter((__, i) => i !== idx))}
              onEdit={scope => onEdit(idx, scope)}
              onClickRole={(roleIdx, value) => onClickRole(idx, roleIdx, value)}
              canDelete={canDelete}
              canEdit={canEdit || !p.type} // allow editing manually entered persons
              roles={defaultRoles.map(({name, ...rest}) => ({
                ...rest,
                name,
                active: p.roles && p.roles.includes(name),
              }))}
              extraParams={extraParams}
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
  canEdit: PropTypes.bool,
  canDelete: PropTypes.bool,
  drag: PropTypes.bool,
  dragType: PropTypes.string.isRequired,
  extraParams: PropTypes.object,
};

PersonLinkSection.defaultProps = {
  label: undefined,
  persons: [],
  defaultRoles: [],
  canEdit: true,
  canDelete: true,
  drag: false,
  extraParams: {},
};

function PersonLinkField({
  value: persons,
  onChange,
  eventId,
  sessionUser,
  roles,
  emptyMessage,
  autoSort,
  setAutoSort,
  hasPredefinedAffiliations,
  allowCustomAffiliations,
  customPersonsMode,
  requiredPersonFields,
  defaultSearchExternal,
  nameFormat,
  validateEmailUrl,
  extraParams,
}) {
  const favoriteUsersController = useFavoriteUsers(null, !sessionUser);
  const [modalOpen, setModalOpen] = useState('');
  const [selected, setSelected] = useState(null);
  const sections = roles.filter(x => x.section);
  const sectionKeys = new Set(sections.map(x => x.name));
  const othersCondition = p => !p.roles || !p.roles.find(r => sectionKeys.has(r));
  const others = persons.filter(othersCondition);

  const onClose = () => {
    setSelected(null);
    setModalOpen('');
  };

  const onEdit = (idx, scope) => {
    setSelected(idx);
    setModalOpen(scope);
  };

  const formatName = ({firstName, lastName}) => {
    const upperLastName = [
      'first_last_upper',
      'f_last_upper',
      'last_f_upper',
      'last_first_upper',
    ].includes(nameFormat);
    const formattedLastName = upperLastName ? lastName.toUpperCase() : lastName;
    if (!firstName) {
      return formattedLastName;
    }
    const abbreviateFirstName = ['last_f', 'last_f_upper', 'f_last', 'f_last_upper'].includes(
      nameFormat
    );
    const formattedFirstName = abbreviateFirstName ? `${firstName[0].toUpperCase()}.` : firstName;
    const lastNameFirst = ['last_f', 'last_f_upper', 'last_first', 'last_first_upper'].includes(
      nameFormat
    );
    return lastNameFirst
      ? `${formattedLastName}, ${formattedFirstName}`
      : `${formattedFirstName} ${formattedLastName}`;
  };

  const onAdd = values => {
    const existing = persons.filter(p => !!p.email).map(p => p.email.toLowerCase());
    const hooks = getPluginObjects('onAddPersonLink');
    values.forEach(p => {
      p.name = formatName(p);
      p.roles = roles.filter(x => x.default).map(x => x.name);
      hooks.forEach(f => f(p));
    });
    onChange([...persons, ...values.filter(v => !existing.includes(v.email.toLowerCase()))]);
  };

  const onSubmit = value => {
    value.name = formatName(value);
    if (!hasPredefinedAffiliations) {
      // value.affiliation is already there and used
      delete value.affiliationData;
    } else if (value.affiliationData) {
      value.affiliation = value.affiliationData.text.trim();
      value.affiliationId = value.affiliationData.id;
      value.affiliationMeta = value.affiliationData.meta;
      delete value.affiliationData;
    }
    if (selected !== null) {
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
                dragType={name}
                key={name}
                drag={!autoSort}
                label={plural || label}
                persons={filtered}
                defaultRoles={roles}
                onEdit={(idx, scope) => onEdit(persons.findIndex(p => p === filtered[idx]), scope)}
                onChange={values =>
                  onChange(persons.filter(p => !filterCondition(p)).concat(values))
                }
                canEdit={customPersonsMode === 'always'}
                extraParams={extraParams}
              />
            );
          })}
          {others.length > 0 && (
            <PersonLinkSection
              drag={!autoSort}
              dragType="other"
              label={sections.length > 0 ? Translate.string('Others') : undefined}
              persons={others}
              defaultRoles={roles}
              onEdit={(idx, scope) => onEdit(persons.findIndex(p => p === others[idx]), scope)}
              onChange={values => onChange(persons.filter(p => !othersCondition(p)).concat(values))}
              canEdit={customPersonsMode === 'always'}
              extraParams={extraParams}
            />
          )}
          {persons.length === 0 && (emptyMessage || <Translate>There are no persons</Translate>)}
        </Segment>
        <Button.Group size="small" attached="bottom">
          <Button
            toggle
            icon="sort alphabet down"
            type="button"
            active={autoSort}
            onClick={() => setAutoSort && setAutoSort(!autoSort)}
          />
          {sessionUser && (
            <Button
              type="button"
              onClick={() => onAdd([sessionUser])}
              disabled={persons.some(p => p.userId === sessionUser.userId)}
            >
              <Icon name="add user" />
              <Translate>Add myself</Translate>
            </Button>
          )}
          <UserSearch
            favoritesController={favoriteUsersController}
            existing={persons.map(p => p.userIdentifier)}
            onAddItems={onAdd}
            onEnterManually={customPersonsMode === 'never' ? null : () => setModalOpen('details')}
            triggerFactory={props => (
              <Button type="button" {...props}>
                <Icon name="search" />
                <Translate>Add from search</Translate>
              </Button>
            )}
            withExternalUsers
            withEventPersons={eventId !== null}
            initialFormValues={{external: defaultSearchExternal}}
            eventId={eventId}
            disabled={!sessionUser}
          />
          {customPersonsMode === 'always' && (
            <Button type="button" onClick={() => setModalOpen('details')}>
              <Icon name="keyboard" />
              <Translate>Enter manually</Translate>
            </Button>
          )}
          {modalOpen === 'details' && (
            <PersonDetailsModal
              onClose={onClose}
              onSubmit={onSubmit}
              person={persons[selected]}
              otherPersons={selected === null ? persons : _.without(persons, persons[selected])}
              requiredPersonFields={requiredPersonFields}
              hasPredefinedAffiliations={hasPredefinedAffiliations}
              allowCustomAffiliations={allowCustomAffiliations}
              validateEmailUrl={validateEmailUrl}
              extraParams={extraParams}
            />
          )}
        </Button.Group>
      </DndProvider>
      {selected !== null &&
        renderPluginComponents('personLinkFieldModals', {
          persons,
          selected,
          onChange,
          onClose,
          modalOpen,
          extraParams,
        })}
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
  hasPredefinedAffiliations: PropTypes.bool,
  allowCustomAffiliations: PropTypes.bool,
  customPersonsMode: PropTypes.oneOf(['always', 'after_search', 'never']),
  requiredPersonFields: PropTypes.array,
  defaultSearchExternal: PropTypes.bool,
  nameFormat: PropTypes.string,
  validateEmailUrl: PropTypes.string,
  extraParams: PropTypes.object,
};

PersonLinkField.defaultProps = {
  emptyMessage: null,
  sessionUser: null,
  eventId: null,
  roles: [],
  autoSort: true,
  setAutoSort: null,
  hasPredefinedAffiliations: false,
  allowCustomAffiliations: true,
  customPersonsMode: 'always',
  requiredPersonFields: [],
  defaultSearchExternal: false,
  nameFormat: '',
  validateEmailUrl: null,
  extraParams: {},
};

export function WTFPersonLinkField({
  fieldId,
  eventId,
  defaultValue,
  roles,
  sessionUser,
  emptyMessage,
  hasPredefinedAffiliations,
  allowCustomAffiliations,
  customPersonsMode,
  requiredPersonFields,
  defaultSearchExternal,
  nameFormat,
  validateEmailUrl,
  extraParams,
}) {
  const [persons, setPersons] = useState(
    defaultValue.sort((a, b) => a.displayOrder - b.displayOrder)
  );
  const [autoSort, _setAutoSort] = useState(persons.every(p => p.displayOrder === 0));
  const inputField = useMemo(() => document.getElementById(fieldId), [fieldId]);

  const onChange = (value, sort = autoSort) => {
    const picked = value.map(p =>
      _.pick(p, [
        'title',
        'name',
        'firstName',
        'lastName',
        'affiliation',
        'affiliationId',
        'email',
        'address',
        'phone',
        'roles',
        'displayOrder',
        'identifier',
        'type',
        'personId',
        'avatarURL',
        ..._.flatten(getPluginObjects('personLinkCustomFields')),
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
      hasPredefinedAffiliations={hasPredefinedAffiliations}
      allowCustomAffiliations={allowCustomAffiliations}
      customPersonsMode={customPersonsMode}
      requiredPersonFields={requiredPersonFields}
      defaultSearchExternal={defaultSearchExternal}
      nameFormat={nameFormat}
      validateEmailUrl={validateEmailUrl}
      extraParams={extraParams}
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
  hasPredefinedAffiliations: PropTypes.bool,
  allowCustomAffiliations: PropTypes.bool,
  nameFormat: PropTypes.string,
  customPersonsMode: PropTypes.oneOf(['always', 'after_search', 'never']),
  requiredPersonFields: PropTypes.array,
  defaultSearchExternal: PropTypes.bool,
  validateEmailUrl: PropTypes.string,
  extraParams: PropTypes.object,
};

WTFPersonLinkField.defaultProps = {
  defaultValue: [],
  eventId: null,
  roles: [],
  sessionUser: null,
  emptyMessage: null,
  hasPredefinedAffiliations: false,
  allowCustomAffiliations: true,
  customPersonsMode: 'always',
  requiredPersonFields: [],
  defaultSearchExternal: false,
  nameFormat: '',
  validateEmailUrl: null,
  extraParams: {},
};
