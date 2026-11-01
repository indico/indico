// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Icon} from 'semantic-ui-react';

import {ContainedPopup as Popup} from 'indico/react/components/PopupMountScope';

import './RoomFeatureEntry.module.scss';

export default function RoomFeatureEntry({feature, color, size}) {
  const {icon, title, equipment} = feature;
  const content =
    equipment.length === 1 && equipment[0] === title
      ? title
      : `${title} (${equipment.filter(eq => eq !== title).join(', ')})`;
  const trigger = (
    <button type="button" styleName="feature-trigger">
      <Icon name={icon} color={color} size={size} />
      <span styleName="visually-hidden">{content}</span>
    </button>
  );
  return (
    <Popup trigger={trigger} content={content} position="top center" on={['hover', 'focus']} />
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
