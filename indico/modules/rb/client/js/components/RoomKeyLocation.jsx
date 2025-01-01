// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Icon, Message} from 'semantic-ui-react';

import {Markdown} from 'indico/react/util';

import './RoomKeyLocation.module.scss';

export default function RoomKeyLocation({room}) {
  return (
    room.keyLocation && (
      <Message styleName="message-icon" icon>
        <Icon name="key" />
        <Message.Content>
          <Markdown targetBlank>{room.keyLocation}</Markdown>
        </Message.Content>
      </Message>
    )
  );
}

RoomKeyLocation.propTypes = {
  room: PropTypes.object.isRequired,
};
