// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Label, Popup} from 'semantic-ui-react';
import Palette from 'indico/utils/palette';
import {EditableStatus} from '../../models';

import './StateIndicator.module.scss';

const colors = {
  replaced: 'grey',
  needs_submitter_confirmation: 'yellow',
  rejected: 'red',
  accepted: 'green',
  assigned: 'purple',
  needs_submitter_changes: 'orange',
  not_submitted: 'blue',
  ready_for_review: 'olive',
};

const labelColors = {
  replaced: Palette.gray,
  needs_submitter_confirmation: Palette.yellow,
  rejected: Palette.red,
  accepted: Palette.green,
  assigned: Palette.purple,
  needs_submitter_changes: Palette.orange,
  not_submitted: Palette.blue,
  ready_for_review: Palette.olive,
};

export default function StateIndicator({label, circular, tooltip, state, monochrome}) {
  const trigger = (
    <Label size="tiny" color={monochrome ? 'grey' : colors[state]} circular={circular} />
  );

  return (
    <>
      <Popup
        position="bottom center"
        trigger={trigger}
        content={tooltip}
        on="hover"
        disabled={!tooltip}
      />
      {label && (
        <div styleName="label-text" style={{color: monochrome ? Palette.gray : labelColors[state]}}>
          {EditableStatus[state]}
        </div>
      )}
    </>
  );
}

StateIndicator.propTypes = {
  label: PropTypes.bool,
  circular: PropTypes.bool,
  tooltip: PropTypes.string,
  state: PropTypes.oneOf(Object.keys(colors)).isRequired,
  monochrome: PropTypes.bool,
};

StateIndicator.defaultProps = {
  label: false,
  circular: false,
  tooltip: null,
  monochrome: false,
};
