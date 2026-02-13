// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Icon} from 'semantic-ui-react';

import {Colors} from 'indico/modules/events/timetable/types';

import './SessionIcon.module.scss';

export function SessionIcon({colors, ...rest}: {colors: Colors}) {
  const {color: subColor, backgroundColor: color} = colors || {};

  return (
    <Icon.Group {...rest}>
      <Icon name="circle" style={{color}} />
      <Icon name="circle" styleName="session-sub-icon" size="mini" style={{color: subColor}} />
    </Icon.Group>
  );
}
