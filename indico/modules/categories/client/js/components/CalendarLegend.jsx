// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.


import PropTypes from 'prop-types';
import React from 'react';

import './CalendarLegend.module.scss';

function LegendItem({title, color, textColor}) {
  return (
    <div styleName="legend-item">
      <div styleName="color-square" style={{ backgroundColor: color }}></div>
      <span style={{color: textColor}}>{title}</span>
    </div>
  );
}

function CalendarLegend({items}) {
  console.log(items)
  const parsedItems = items.map(
    ({id, title, color, textColor}) => <LegendItem key={id} title={title} color={color} textColor={textColor} />
  );
  return (
    <div styleName="legend-container">
      {parsedItems}
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
