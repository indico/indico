// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import validateEmailURL from 'indico-url:events.check_email';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useMemo, useState} from 'react';
import {DndProvider} from 'react-dnd';
import {HTML5Backend} from 'react-dnd-html5-backend';
import {Button, Icon, Label, List, Popup, Ref, Segment} from 'semantic-ui-react';

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

const roleSchema = PropTypes.shape({
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  plural: PropTypes.string,
  icon: PropTypes.string,
  active: PropTypes.bool,
  default: PropTypes.bool,
  section: PropTypes.bool,
});

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
  roles: PropTypes.arrayOf(roleSchema).isRequired,
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
  value: _persons,
  onChange,
  eventId,
  sessionUser,
  roles,
  emptyMessage,
  hasPredefinedAffiliations,
  allowCustomAffiliations,
  customPersonsMode,
  requiredPersonFields,
  defaultSearchExternal,
  userSearchDisabled,
  nameFormat,
  extraParams,
  searchToken,
}) {
  const favoriteUsersController = useFavoriteUsers(null, !sessionUser);
  const [modalOpen, setModalOpen] = useState('');
  const [selected, setSelected] = useState(null);
  const [autoSort, _setAutoSort] = useState(_persons.every(p => p.displayOrder === 0));
  const sections = roles.filter(x => x.section);
  const sectionKeys = new Set(sections.map(x => x.name));
  const othersCondition = p => !p.roles || !p.roles.find(r => sectionKeys.has(r));

  const cleanupPersons = persons => {
    return persons.map(p =>
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
  };

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
    onChange(cleanupPersons(_persons.map((x, i) => ({...x, displayOrder: sort ? 0 : i}))));
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

  const persons = (
    autoSort ? _persons.slice().sort((a, b) => a.name.localeCompare(b.name)) : _persons
  ).map(p => ({name: formatName(p), ...p}));
  const others = persons.filter(othersCondition);

  const onAdd = values => {
    const existing = persons.filter(p => !!p.email).map(p => p.email.toLowerCase());
    const hooks = getPluginObjects('onAddPersonLink');
    values.forEach(p => {
      p.name = formatName(p);
      p.roles = roles.filter(x => x.default).map(x => x.name);
      hooks.forEach(f => f(p));
    });
    onChange(
      cleanupPersons([...persons, ...values.filter(v => !existing.includes(v.email.toLowerCase()))])
    );
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
      onChange(cleanupPersons(persons.map((v, idx) => (idx === selected ? value : v))));
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
                onEdit={(idx, scope) =>
                  onEdit(
                    persons.findIndex(p => p === filtered[idx]),
                    scope
                  )
                }
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
              onEdit={(idx, scope) =>
                onEdit(
                  persons.findIndex(p => p === others[idx]),
                  scope
                )
              }
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
            disabled={!sessionUser || !searchToken || userSearchDisabled}
            searchToken={searchToken}
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

PersonLinkField.propTypes = {
  value: PropTypes.array.isRequired,
  onChange: PropTypes.func.isRequired,
  emptyMessage: PropTypes.string,
  sessionUser: PropTypes.object,
  eventId: PropTypes.number,
  roles: PropTypes.arrayOf(roleSchema),
  hasPredefinedAffiliations: PropTypes.bool,
  allowCustomAffiliations: PropTypes.bool,
  customPersonsMode: PropTypes.oneOf(['always', 'after_search', 'never']),
  requiredPersonFields: PropTypes.array,
  defaultSearchExternal: PropTypes.bool,
  userSearchDisabled: PropTypes.bool,
  nameFormat: PropTypes.string,
  extraParams: PropTypes.object,
  searchToken: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
};

PersonLinkField.defaultProps = {
  emptyMessage: null,
  sessionUser: null,
  eventId: null,
  roles: [],
  hasPredefinedAffiliations: false,
  allowCustomAffiliations: true,
  customPersonsMode: 'always',
  requiredPersonFields: [],
  defaultSearchExternal: false,
  userSearchDisabled: false,
  nameFormat: '',
  extraParams: {},
  searchToken: null,
};

export function FinalPersonLinkField({name, ...rest}) {
  return <FinalField name={name} component={PersonLinkField} {...rest} />;
}

FinalPersonLinkField.propTypes = {
  name: PropTypes.string.isRequired,
};

export function FinalAbstractPersonLinkField({allowSpeakers, ...rest}) {
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

FinalAbstractPersonLinkField.propTypes = {
  ...FinalPersonLinkField.propTypes,
  allowSpeakers: PropTypes.bool,
};

FinalAbstractPersonLinkField.defaultProps = {
  allowSpeakers: false,
};

export function FinalContributionPersonLinkField({
  allowAuthors,
  allowSubmitters,
  defaultIsSubmitter,
  defaultIsSpeaker,
  defaultIsAuthor,
  ...rest
}) {
  const roles = [
    {
      name: 'speaker',
      label: Translate.string('Speaker'),
      icon: 'microphone',
      default: defaultIsSpeaker,
    },
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
        default: defaultIsAuthor,
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

FinalContributionPersonLinkField.propTypes = {
  ...FinalPersonLinkField.propTypes,
  allowAuthors: PropTypes.bool,
  allowSubmitters: PropTypes.bool,
  defaultIsSubmitter: PropTypes.bool,
  defaultIsSpeaker: PropTypes.bool,
  defaultIsAuthor: PropTypes.bool,
};

FinalContributionPersonLinkField.defaultProps = {
  allowAuthors: true,
  allowSubmitters: true,
  defaultIsSubmitter: true,
  defaultIsSpeaker: true,
  defaultIsAuthor: false,
};

export function FinalSessionBlockPersonLinkField(props) {
  return <FinalPersonLinkField roles={[]} {...props} />;
}

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
  userSearchDisabled,
  nameFormat,
  extraParams,
  searchToken,
}) {
  const [persons, setPersons] = useState(
    defaultValue.sort((a, b) => a.displayOrder - b.displayOrder)
  );
  const inputField = useMemo(() => document.getElementById(fieldId), [fieldId]);

  const onChange = value => {
    inputField.value = JSON.stringify(snakifyKeys(value));
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
      allowCustomAffiliations={allowCustomAffiliations}
      customPersonsMode={customPersonsMode}
      requiredPersonFields={requiredPersonFields}
      defaultSearchExternal={defaultSearchExternal}
      nameFormat={nameFormat}
      extraParams={extraParams}
      searchToken={searchToken}
      userSearchDisabled={userSearchDisabled}
    />
  );
}

WTFPersonLinkField.propTypes = {
  fieldId: PropTypes.string.isRequired,
  defaultValue: PropTypes.array,
  eventId: PropTypes.number,
  roles: PropTypes.arrayOf(roleSchema),
  sessionUser: PropTypes.object,
  emptyMessage: PropTypes.string,
  hasPredefinedAffiliations: PropTypes.bool,
  allowCustomAffiliations: PropTypes.bool,
  nameFormat: PropTypes.string,
  customPersonsMode: PropTypes.oneOf(['always', 'after_search', 'never']),
  requiredPersonFields: PropTypes.array,
  defaultSearchExternal: PropTypes.bool,
  userSearchDisabled: PropTypes.bool,
  extraParams: PropTypes.object,
  searchToken: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
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
  userSearchDisabled: false,
  nameFormat: '',
  extraParams: {},
  searchToken: null,
};
