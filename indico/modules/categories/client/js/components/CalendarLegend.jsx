// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import './CalendarLegend.module.scss';
import {Select} from "semantic-ui-react";
import {Translate} from "indico/react/i18n";

function LegendItem({title, color, textColor}) {
  return (
    <div styleName="legend-item">
      <div styleName="color-square" style={{ backgroundColor: color }}></div>
      <span style={{color: textColor}}>{title}</span>
    </div>
  );
}

function CalendarLegend({items, groupBy, onFilterChanged}) {
  const parsedItems = items.map(
    ({id, title, color, textColor}) => <LegendItem key={id} title={title} color={color} textColor={textColor} />
  );
  const options = [
    {text: Translate.string('Category'), value: 'category'},
    {text: Translate.string('Location'), value: 'location'},
  ];
  return (
    <div styleName="legend-container">
      <span>{Translate.string('Display by:')}</span>
      <Select
        value={groupBy || 'category'}
        options={options}
        onChange={(event, data) => onFilterChanged(data.value)}
      />
      <div>{parsedItems}</div>
    </div>
  );
}

CalendarLegend.propTypes = {
  items: PropTypes.array.isRequired,
};

CalendarLegend.defaultProps = {
  items: [],
};

export default CalendarLegend;
