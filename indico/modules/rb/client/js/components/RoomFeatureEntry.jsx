// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Icon, Popup} from 'semantic-ui-react';

export default function RoomFeatureEntry({feature, color, size}) {
  const {icon, title, equipment} = feature;
  const trigger = <Icon name={icon} color={color} size={size} />;
  if (equipment.length === 1 && equipment[0] === title) {
    return <Popup trigger={trigger} content={title} position="top center" />;
  }
  return (
    <Popup trigger={trigger} position="top center">
      {title} ({equipment.filter(eq => eq !== title).join(', ')})
    </Popup>
  );
}

RoomFeatureEntry.propTypes = {
  feature: PropTypes.shape({
    icon: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    equipment: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  color: PropTypes.string.isRequired,
  size: PropTypes.string,
};

RoomFeatureEntry.defaultProps = {
  size: undefined,
};
