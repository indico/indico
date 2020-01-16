// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Button, List} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {UserSearch, GroupSearch} from './Search';
import {useFetchPrincipals} from './hooks';
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
    favoriteUsersController,
  } = props;
  const [favoriteUsers, [handleAddFavorite, handleDelFavorite]] = favoriteUsersController;

  const informationMap = useFetchPrincipals(value);

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
      <List divided relaxed styleName="list">
        {entries.map(data => (
          <PrincipalListItem
            key={data.identifier}
            name={data.name}
            detail={data.detail}
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
          <Button icon="add" as="div" disabled />
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
};

PrincipalListField.defaultProps = {
  withGroups: false,
  withExternalUsers: false,
  readOnly: false,
};

export default React.memo(PrincipalListField);

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
  favoriteUsersController: PropTypes.array.isRequired,
};

FinalPrincipalList.defaultProps = {
  withGroups: false,
  withExternalUsers: false,
  readOnly: false,
};
