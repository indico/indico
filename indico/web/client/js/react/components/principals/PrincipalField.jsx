// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import principalsURL from 'indico-url:core.principals';

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {Icon, List} from 'semantic-ui-react';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import {FinalField} from '../../forms';

import {EmptyPrincipalListItem, PendingPrincipalListItem, PrincipalListItem} from './items';
import {UserSearch} from './Search';

import './items.module.scss';

/**
 * A field that lets the user select a user.
 */
const PrincipalField = props => {
  const {
    value,
    disabled,
    required,
    onChange,
    onFocus,
    onBlur,
    favoriteUsersController,
    withExternalUsers,
    className,
    searchToken,
  } = props;
  const [favoriteUsers, [handleAddFavorite, handleDelFavorite]] = favoriteUsersController;

  const [details, setDetails] = useState(null);

  const markTouched = () => {
    onFocus();
    onBlur();
  };

  useEffect(() => {
    if (!value) {
      if (details) {
        // clear old details
        setDetails(null);
      }
      return;
    }
    if (details && details.identifier === value) {
      // nothing to do
      return;
    }
    const controller = new AbortController();
    (async () => {
      let response;
      try {
        response = await indicoAxios.post(
          principalsURL(),
          {values: [value]},
          {signal: controller.signal}
        );
      } catch (error) {
        handleAxiosError(error);
        return;
      }
      setDetails(camelizeKeys(response.data[value]));
    })();

    return () => {
      controller.abort();
    };
  }, [details, value]);

  const handleAddItem = principal => {
    onChange(principal.identifier);
    markTouched();
  };
  const handleClear = () => {
    onChange(null);
    markTouched();
  };

  const searchTrigger = triggerProps => (
    <Icon styleName="button" name="search" size="large" {...triggerProps} />
  );
  const userSearch = (
    <UserSearch
      searchToken={searchToken}
      triggerFactory={searchTrigger}
      existing={value ? [value] : []}
      onAddItems={handleAddItem}
      onOpen={onFocus}
      onClose={onBlur}
      favoritesController={favoriteUsersController}
      disabled={disabled}
      withExternalUsers={withExternalUsers}
      single
    />
  );

  return (
    <div className="ui input">
      <div className="fake-input">
        <List relaxed className={className}>
          {!value ? (
            <EmptyPrincipalListItem search={userSearch} />
          ) : details ? (
            <PrincipalListItem
              name={details.name}
              detail={details.detail}
              favorite={details.identifier in favoriteUsers}
              isPendingUser={details.userId === null}
              invalid={details.invalid}
              canDelete={!required}
              onDelete={() => !disabled && handleClear()}
              onAddFavorite={() => !disabled && handleAddFavorite(details.identifier)}
              onDelFavorite={() => !disabled && handleDelFavorite(details.identifier)}
              disabled={disabled}
              search={userSearch}
            />
          ) : (
            <PendingPrincipalListItem />
          )}
        </List>
      </div>
    </div>
  );
};

PrincipalField.propTypes = {
  value: PropTypes.string,
  required: PropTypes.bool,
  disabled: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
  favoriteUsersController: PropTypes.array.isRequired,
  withExternalUsers: PropTypes.bool,
  className: PropTypes.string,
  searchToken: PropTypes.string,
};

PrincipalField.defaultProps = {
  value: null,
  required: false,
  withExternalUsers: false,
  className: '',
  searchToken: null,
};

export default React.memo(PrincipalField);

/**
 * Like `FinalField` but for a `PrincipalField`.
 */
export function FinalPrincipal({name, ...rest}) {
  return <FinalField name={name} component={PrincipalField} {...rest} />;
}

FinalPrincipal.propTypes = {
  name: PropTypes.string.isRequired,
  withExternalUsers: PropTypes.bool,
  favoriteUsersController: PropTypes.array.isRequired,
};

FinalPrincipal.defaultProps = {
  withExternalUsers: false,
};
