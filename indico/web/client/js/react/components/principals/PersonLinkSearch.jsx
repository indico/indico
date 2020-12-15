// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {useFavoriteUsers} from 'indico/react/hooks';

import {UserSearch} from './Search';

export const PersonLinkSearch = ({
  existing,
  onAddItems,
  disabled,
  withExternalUsers,
  withEventPersons,
  eventId,
  single,
  triggerFactory,
  ...rest
}) => {
  const [favoriteUsers] = useFavoriteUsers();
  return (
    <UserSearch
      existing={existing}
      onAddItems={onAddItems}
      favorites={favoriteUsers}
      disabled={disabled}
      withExternalUsers={withExternalUsers}
      withEventPersons={withEventPersons}
      eventId={eventId}
      triggerFactory={triggerFactory}
      single={single}
      {...rest}
    />
  );
};

PersonLinkSearch.propTypes = {
  onAddItems: PropTypes.func.isRequired,
  existing: PropTypes.arrayOf(PropTypes.string).isRequired,
  disabled: PropTypes.bool,
  withExternalUsers: PropTypes.bool,
  withEventPersons: PropTypes.bool,
  eventId: PropTypes.number,
  single: PropTypes.bool,
  triggerFactory: PropTypes.func,
};

PersonLinkSearch.defaultProps = {
  disabled: false,
  withExternalUsers: false,
  withEventPersons: false,
  eventId: null,
  single: false,
  triggerFactory: null,
};
