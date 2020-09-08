// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Button, Dropdown, List} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {UserSearch, GroupSearch} from './Search';
import {useFetchPrincipals, useFetchAvailablePrincipals} from './hooks';
import {PendingPrincipalListItem, PrincipalListItem} from './items';
import {getPrincipalList, PrincipalType} from './util';
import {FinalField} from '../../forms';

import './PrincipalListField.module.scss';

/**
 * A field that lets the user select a list of users/groups.
 *
 * Setting the `readOnly` prop hides all UI elements used to modify
 * the entries, so it can be used to just display the current contents
 * outside editing mode.
 */
const PrincipalListField = props => {
  const {
    value,
    disabled,
    readOnly,
    onChange,
    onFocus,
    onBlur,
    withGroups,
    withExternalUsers,
    withEventRoles,
    withCategoryRoles,
    withRegistrants,
    eventId,
    favoriteUsersController,
    className,
  } = props;
  const [favoriteUsers, [handleAddFavorite, handleDelFavorite]] = favoriteUsersController;

  const usedIdentifiers = new Set(value);
  const informationMap = useFetchPrincipals(value, eventId);
  const {
    eventRoles,
    categoryRoles,
    registrationForms,
    loading: loadingAvailablePrincipals,
  } = useFetchAvailablePrincipals({
    eventId,
    withEventRoles,
    withCategoryRoles,
    withRegistrants,
  });

  const asOptions = (data, getText = null) =>
    data
      .filter(r => !usedIdentifiers.has(r.identifier))
      .map(r => ({
        value: r.identifier,
        text: getText ? getText(r.name) : r.name,
      }));

  const markTouched = () => {
    onFocus();
    onBlur();
  };
  const handleDelete = identifier => {
    onChange(value.filter(x => x !== identifier));
    markTouched();
  };
  const handleAddItems = data => {
    onChange([...value, ...data.map(x => x.identifier)]);
    markTouched();
  };

  const [entries, pendingEntries] = getPrincipalList(value, informationMap);

  return (
    <>
      <List divided relaxed styleName="list" className={className}>
        {entries.map(data => (
          <PrincipalListItem
            key={data.identifier}
            name={data.name}
            detail={data.detail}
            meta={data.meta}
            type={data.type}
            invalid={data.invalid}
            isPendingUser={data.type === PrincipalType.user && data.userId === null}
            favorite={data.type === PrincipalType.user && data.userId in favoriteUsers}
            onDelete={() => !disabled && handleDelete(data.identifier)}
            onAddFavorite={() => !disabled && handleAddFavorite(data.userId)}
            onDelFavorite={() => !disabled && handleDelFavorite(data.userId)}
            disabled={disabled}
            readOnly={readOnly}
          />
        ))}
        {pendingEntries.map(data => (
          <PendingPrincipalListItem key={data.identifier} type={data.type} />
        ))}
        {!value.length && (
          <List.Item styleName="empty">
            <Translate>This list is currently empty</Translate>
          </List.Item>
        )}
      </List>
      {!readOnly && (
        <Button.Group>
          <Button icon="add" as="div" disabled loading={loadingAvailablePrincipals} />
          {!loadingAvailablePrincipals && (
            <>
              <UserSearch
                existing={value}
                onAddItems={handleAddItems}
                favorites={favoriteUsers}
                disabled={disabled}
                withExternalUsers={withExternalUsers}
                onOpen={onFocus}
                onClose={onBlur}
              />
              {withGroups && (
                <GroupSearch
                  existing={value}
                  onAddItems={handleAddItems}
                  disabled={disabled}
                  onOpen={onFocus}
                  onClose={onBlur}
                />
              )}
              {eventRoles.length !== 0 && (
                <AddPrincipalDropdown
                  text={Translate.string('Event Role')}
                  options={asOptions(eventRoles)}
                  onChange={handleAddItems}
                  disabled={disabled}
                />
              )}
              {categoryRoles.length !== 0 && (
                <AddPrincipalDropdown
                  text={Translate.string('Category Role')}
                  options={asOptions(categoryRoles)}
                  onChange={handleAddItems}
                  disabled={disabled}
                />
              )}
              {registrationForms.length !== 0 && (
                <AddPrincipalDropdown
                  text={Translate.string('Registrants')}
                  options={asOptions(registrationForms, form =>
                    Translate.string('Registrants in "{form}"', {form})
                  )}
                  onChange={handleAddItems}
                  disabled={disabled}
                />
              )}
            </>
          )}
        </Button.Group>
      )}
    </>
  );
};

PrincipalListField.propTypes = {
  value: PropTypes.arrayOf(PropTypes.string).isRequired,
  disabled: PropTypes.bool.isRequired,
  readOnly: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
  favoriteUsersController: PropTypes.array.isRequired,
  withGroups: PropTypes.bool,
  withExternalUsers: PropTypes.bool,
  withEventRoles: PropTypes.bool,
  withCategoryRoles: PropTypes.bool,
  withRegistrants: PropTypes.bool,
  eventId: PropTypes.number,
  className: PropTypes.string,
};

PrincipalListField.defaultProps = {
  withGroups: false,
  withExternalUsers: false,
  withEventRoles: false,
  withCategoryRoles: false,
  withRegistrants: false,
  eventId: null,
  readOnly: false,
  className: undefined,
};

export default React.memo(PrincipalListField);

function AddPrincipalDropdown({text, options, disabled, onChange}) {
  return (
    <Dropdown
      text={text}
      button
      upward
      floating
      disabled={disabled || options.length === 0}
      options={options}
      openOnFocus={false}
      selectOnBlur={false}
      selectOnNavigation={false}
      value={null}
      onChange={(e, data) => onChange([{identifier: data.value}])}
    />
  );
}
AddPrincipalDropdown.propTypes = {
  text: PropTypes.string.isRequired,
  options: PropTypes.array.isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
};

/**
 * Like `FinalField` but for a `PrincipalListField`.
 */
export function FinalPrincipalList({name, ...rest}) {
  return (
    <FinalField
      name={name}
      component={PrincipalListField}
      isEqual={(a, b) => _.isEqual((a || []).sort(), (b || []).sort())}
      {...rest}
    />
  );
}

FinalPrincipalList.propTypes = {
  name: PropTypes.string.isRequired,
  readOnly: PropTypes.bool,
  withGroups: PropTypes.bool,
  withExternalUsers: PropTypes.bool,
  withEventRoles: PropTypes.bool,
  withCategoryRoles: PropTypes.bool,
  withRegistrants: PropTypes.bool,
  eventId: PropTypes.number,
  favoriteUsersController: PropTypes.array.isRequired,
};

FinalPrincipalList.defaultProps = {
  withGroups: false,
  withExternalUsers: false,
  withEventRoles: false,
  withCategoryRoles: false,
  withRegistrants: false,
  eventId: null,
  readOnly: false,
};
