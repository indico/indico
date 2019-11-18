// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Label, Popup} from 'semantic-ui-react';

const colors = {
  replaced: 'grey',
  needs_confirmation: 'yellow',
  rejected: 'red',
  accepted: 'green',
  assigned: 'purple',
};

export default function StateIndicator({text, circular, tooltip, state}) {
  const trigger = (
    <Label size="small" color={colors[state]} circular={circular}>
      {text}
    </Label>
  );

  return (
    <Popup
      position="bottom center"
      trigger={trigger}
      content={tooltip}
      on="hover"
      disabled={!tooltip}
    />
  );
}

StateIndicator.propTypes = {
  text: PropTypes.string,
  circular: PropTypes.bool,
  tooltip: PropTypes.string,
  state: PropTypes.oneOf(Object.keys(colors)).isRequired,
};

StateIndicator.defaultProps = {
  text: null,
  circular: false,
  tooltip: null,
};
