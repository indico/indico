// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Label, Segment, List} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {legendLabelShape} from '../../props';

import './TimelineLegend.module.scss';

export default function TimelineLegend({labels, aside, compact}) {
  if (compact) {
    return labels.length ? (
      <List styleName="legend compact">
        {labels.map(({label, style}) => (
          <List.Item key={label}>
            <List.Content styleName="labels">
              <Label styleName={`compact ${style || ''}`} />
              <span styleName="text">{label}</span>
            </List.Content>
          </List.Item>
        ))}
      </List>
    ) : (
      <Translate>No occurrences</Translate>
    );
  } else {
    return (
      <Segment styleName="legend" basic>
        <Label.Group as="span" size="medium" styleName="labels">
          {labels.map(({label, style}) => (
            <Label styleName={style || ''} key={label}>
              {label}
            </Label>
          ))}
        </Label.Group>
        {aside}
      </Segment>
    );
  }
}

TimelineLegend.propTypes = {
  labels: PropTypes.arrayOf(legendLabelShape).isRequired,
  aside: PropTypes.node,
  compact: PropTypes.bool,
};

TimelineLegend.defaultProps = {
  aside: null,
  compact: false,
};
