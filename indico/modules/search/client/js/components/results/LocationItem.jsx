// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {List, Icon, Popup} from 'semantic-ui-react';

export const locationPropType = PropTypes.shape({
  address: PropTypes.string.isRequired,
  roomName: PropTypes.string.isRequired,
  venueName: PropTypes.string.isRequired,
});

export function LocationItem({location: {address, roomName, venueName}}) {
  let location = null;

  if (roomName && venueName) {
    location = `${roomName} (${venueName})`;
  } else if (roomName || venueName) {
    location = roomName || venueName;
  }

  if (location && address) {
    location = (
      <Popup
        content={<span style={{whiteSpace: 'pre-line'}}>{address}</span>}
        trigger={<span>{location}</span>}
      />
    );
  }

  return (
    location && (
      <List.Item>
        <Icon name="map pin" />
        {location}
      </List.Item>
    )
  );
}

LocationItem.propTypes = {
  location: locationPropType.isRequired,
};
