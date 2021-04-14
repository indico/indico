// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';

import {ACLField} from 'indico/react/components';
import {PermissionManager} from 'indico/react/components/principals/util';
import {useFavoriteUsers} from 'indico/react/hooks';

export default function TrackACLField({
  value,
  permissionInfo,
  eventId,
  eventRoles,
  categoryRoles,
  onChange,
}) {
  const [currentValue, setCurrentValue] = useState(value);
  const permissionManager = new PermissionManager(permissionInfo.tree, permissionInfo.default);
  const favoriteUsersController = useFavoriteUsers();
  return (
    <ACLField
      value={currentValue}
      disabled={false}
      onChange={newValue => {
        setCurrentValue(newValue);
        onChange(newValue);
      }}
      onFocus={() => {}}
      onBlur={() => {}}
      favoriteUsersController={favoriteUsersController}
      withGroups
      readAccessAllowed={false}
      fullAccessAllowed={false}
      permissionInfo={permissionInfo}
      permissionManager={permissionManager}
      eventId={eventId}
      eventRoles={eventRoles}
      categoryRoles={categoryRoles}
    />
  );
}

TrackACLField.propTypes = {
  /** Current value of the field, an array of `[identifier, [permissions]]` pairs */
  value: PropTypes.arrayOf(PropTypes.array).isRequired,
  /** Object containing metadata about available permissions */
  permissionInfo: PropTypes.shape({
    permissions: PropTypes.object,
    tree: PropTypes.object,
    default: PropTypes.string,
  }).isRequired,
  eventId: PropTypes.number.isRequired,
  eventRoles: PropTypes.array.isRequired,
  categoryRoles: PropTypes.array.isRequired,
  onChange: PropTypes.func.isRequired,
};
