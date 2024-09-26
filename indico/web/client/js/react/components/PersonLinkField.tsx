// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import validateEmailURL from 'indico-url:events.check_email';

import _ from 'lodash';
import React, {useMemo, useState} from 'react';
import {DndProvider} from 'react-dnd';
import {HTML5Backend} from 'react-dnd-html5-backend';
import {Button, Segment, List, Label, Icon, Popup, Ref} from 'semantic-ui-react';

import {UserSearch} from 'indico/react/components/principals/Search';
import {PrincipalType} from 'indico/react/components/principals/util';
import {FinalField} from 'indico/react/forms';
import {useFavoriteUsers} from 'indico/react/hooks';
import {SortableWrapper, useSortableItem} from 'indico/react/sortable';
import {snakifyKeys} from 'indico/utils/case';
import {getPluginObjects, renderPluginComponents} from 'indico/utils/plugins';

import {Translate} from '../i18n';

import PersonDetailsModal from './PersonDetailsModal';
import {PrincipalItem} from './principals/items';

import './PersonLinkField.module.scss';

interface PersonType {
  userId?: number;
  userIdentifier?: string;
  firstName: string;
  lastName: string;
  name: string;
  email: string;
  affiliation: string;
  avatarURL: string;
  roles: string[];
  displayOrder?: number;
}

interface RoleType {
  name: string;
  label: string;
  plural?: string;
  icon?: string;
  default?: boolean;
  section?: boolean;
}

interface PersonListItemProps {
  person: PersonType;
  roles: RoleType[];
  canEdit?: boolean;
  canDelete?: boolean;
  onDelete?: () => void;
  onEdit: (scope: string) => void;
  onClickRole?: (roleIdx: number, roles: RoleType[]) => void;
  disabled?: boolean;
  extraParams?: object;
}

const PersonListItem = ({
  person,
  roles,
  canEdit = true,
  canDelete = true,
  onDelete = null,
  onEdit,
  onClickRole = null,
  disabled = false,
  extraParams = {},
}: PersonListItemProps) => (
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

interface DraggablePersonProps extends PersonListItemProps {
  drag?: boolean;
  dragType: string;
  onMove: (dragIndex: number, hoverIndex: number) => void;
  index: number;
}

const DraggablePerson = ({drag = true, dragType, onMove, index, ...props}: DraggablePersonProps) => {
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

interface PersonLinkSectionProps {
  label?: string;
  persons?: PersonType[];
  defaultRoles?: RoleType[];
  onChange: (persons: PersonType[]) => void;
  onEdit: (idx: number, scope: string) => void;
  canEdit?: boolean;
  canDelete?: boolean;
  drag?: boolean;
  dragType: string;
  extraParams?: object;
}

const PersonLinkSection = ({
  label: sectionLabel,
  persons = [],
  defaultRoles = [],
  onChange,
  onEdit,
  canEdit = true,
  canDelete = true,
  drag = false,
  dragType,
  extraParams = {},
}: PersonLinkSectionProps) => {
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
              canEdit={canEdit}
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

interface PersonLinkFieldProps {
  eventId?: number;
  sessionUser?: PersonType;
  roles?: RoleType[];
  emptyMessage?: string;
  hasPredefinedAffiliations?: boolean;
  canEnterManually?: boolean;
  defaultSearchExternal?: boolean;
  nameFormat?: string;
  extraParams?: object;
}

interface PersonLinkFieldComponentProps extends PersonLinkFieldProps {
  value: PersonType[];
  onChange: (value: PersonType[]) => void;
}

function PersonLinkField({
  value: _persons,
  onChange,
  eventId = null,
  sessionUser = null,
  roles = [],
  emptyMessage = null,
  hasPredefinedAffiliations = false,
  canEnterManually = true,
  defaultSearchExternal = false,
  nameFormat = '',
  extraParams = {},
}: PersonLinkFieldComponentProps) {
  const [favoriteUsers] = useFavoriteUsers(null, !sessionUser);
  const [modalOpen, setModalOpen] = useState('');
  const [selected, setSelected] = useState(null);
  const [autoSort, _setAutoSort] = useState(_persons.every(p => p.displayOrder === 0));
  const sections = roles.filter(x => x.section);
  const sectionKeys = new Set(sections.map(x => x.name));
  const othersCondition = p => !p.roles || !p.roles.find(r => sectionKeys.has(r));

  const onClose = () => {
    setSelected(null);
    setModalOpen('');
  };

  const onEdit = (idx, scope) => {
    setSelected(idx);
    setModalOpen(scope);
  };

  const setAutoSort = sort => {
    _setAutoSort(sort);
    onChange(_persons.map((x, i) => ({...x, displayOrder: sort ? 0 : i})));
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

  const persons = (autoSort
    ? _persons.slice().sort((a, b) => a.name.localeCompare(b.name))
    : _persons
  ).map(p => ({name: formatName(p), ...p}));
  const others = persons.filter(othersCondition);

  const onAdd = values => {
    const existing = persons.filter(p => !!p.email).map(p => p.email);
    const hooks = getPluginObjects('onAddPersonLink');
    values.forEach(p => {
      p.name = formatName(p);
      p.roles = roles.filter(x => x.default).map(x => x.name);
      hooks.forEach(f => f(p));
    });
    onChange([...persons, ...values.filter(v => !existing.includes(v.email))]);
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
                canEdit={canEnterManually}
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
              canEdit={canEnterManually}
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
            onClick={() => setAutoSort(!autoSort)}
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
            favorites={favoriteUsers}
            existing={persons.map(p => p.userIdentifier)}
            onAddItems={onAdd}
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
          {canEnterManually && (
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
              hasPredefinedAffiliations={hasPredefinedAffiliations}
              validateEmailUrl={eventId && validateEmailURL({event_id: eventId})}
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

interface FinalPersonLinkFieldProps extends PersonLinkFieldProps {
  name: string;
}

export function FinalPersonLinkField({name, ...rest}: FinalPersonLinkFieldProps) {
  return <FinalField name={name} component={PersonLinkField} {...rest} />;
}

interface FinalAbstractPersonLinkFieldProps extends FinalPersonLinkFieldProps {
  allowSpeakers?: boolean;
}

export function FinalAbstractPersonLinkField({allowSpeakers = false, ...rest}: FinalAbstractPersonLinkFieldProps) {
  const roles = [
    {
      name: 'primary',
      label: Translate.string('Author'),
      plural: Translate.string('Authors'),
      section: true,
      default: true,
    },
    {
      name: 'secondary',
      label: Translate.string('Co-author'),
      plural: Translate.string('Co-authors'),
      section: true,
    },
  ];
  if (allowSpeakers) {
    roles.push({name: 'speaker', label: Translate.string('Speaker'), icon: 'microphone'});
  }
  return <FinalPersonLinkField roles={roles} {...rest} />;
}

interface FinalContributionPersonLinkFieldProps extends FinalPersonLinkFieldProps {
  allowAuthors?: boolean;
  allowSubmitters?: boolean;
  defaultIsSubmitter?: boolean;
}

export function FinalContributionPersonLinkField({
  allowAuthors = true,
  allowSubmitters = true,
  defaultIsSubmitter = true,
  ...rest
}: FinalContributionPersonLinkFieldProps) {
  const roles = [
    {name: 'speaker', label: Translate.string('Speaker'), icon: 'microphone', default: true},
  ];
  if (allowSubmitters) {
    roles.push({
      name: 'submitter',
      label: Translate.string('Submitter'),
      icon: 'paperclip',
      default: defaultIsSubmitter,
    });
  }
  if (allowAuthors) {
    roles.push(
      {
        name: 'primary',
        label: Translate.string('Author'),
        plural: Translate.string('Authors'),
        section: true,
      },
      {
        name: 'secondary',
        label: Translate.string('Co-author'),
        plural: Translate.string('Co-authors'),
        section: true,
      }
    );
  }
  return <FinalPersonLinkField roles={roles} {...rest} />;
}

interface WTFPersonLinkFieldProps extends PersonLinkFieldProps {
  fieldId: string;
  defaultValue?: PersonType[];
}

export function WTFPersonLinkField({
  fieldId,
  eventId = null,
  defaultValue = [],
  roles = [],
  sessionUser = null,
  emptyMessage = null,
  hasPredefinedAffiliations = false,
  canEnterManually = true,
  defaultSearchExternal = false,
  nameFormat = '',
  extraParams = {},
}: WTFPersonLinkFieldProps) {
  const [persons, setPersons] = useState(
    defaultValue.sort((a, b) => a.displayOrder - b.displayOrder)
  );
  const inputField = useMemo(() => document.getElementById(fieldId), [fieldId]);

  const onChange = value => {
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
    inputField.value = JSON.stringify(snakifyKeys(picked));
    setPersons(value);
    inputField.dispatchEvent(new Event('change', {bubbles: true}));
  };

  return (
    <PersonLinkField
      value={persons}
      eventId={eventId}
      onChange={onChange}
      roles={roles}
      sessionUser={sessionUser}
      emptyMessage={emptyMessage}
      hasPredefinedAffiliations={hasPredefinedAffiliations}
      canEnterManually={canEnterManually}
      defaultSearchExternal={defaultSearchExternal}
      nameFormat={nameFormat}
      extraParams={extraParams}
    />
  );
}
