// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Label, Popup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import Palette from 'indico/utils/palette';

import {EditableStatus} from '../../models';

import './StateIndicator.module.scss';

const colors = {
  replaced: 'orange',
  needs_submitter_confirmation: 'yellow',
  rejected: 'black',
  accepted: 'green',
  needs_submitter_changes: 'red',
  ready_for_review: 'grey',
};

const labelColors = {
  replaced: Palette.orange,
  needs_submitter_confirmation: Palette.yellow,
  rejected: Palette.black,
  accepted: Palette.green,
  needs_submitter_changes: Palette.red,
  not_submitted: Palette.black,
  ready_for_review: Palette.blue,
};

export default function StateIndicator({label, circular, tooltip, state, monochrome}) {
  const labelColor = labelColors[state] || Palette.black;
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
        <div styleName="label-text" style={{color: monochrome ? Palette.gray : labelColor}}>
          {EditableStatus[state] || Translate.string('Unknown')}
        </div>
      )}
    </>
  );
}

StateIndicator.propTypes = {
  label: PropTypes.bool,
  circular: PropTypes.bool,
  tooltip: PropTypes.string,
  state: PropTypes.string.isRequired,
  monochrome: PropTypes.bool,
};

StateIndicator.defaultProps = {
  label: false,
  circular: false,
  tooltip: null,
  monochrome: false,
};
