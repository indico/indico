// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import './CalendarLegend.module.scss';
import {Checkbox, Select} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

function LegendItem({title, color, textColor, checked, onChange}) {
  return (
    <div styleName="legend-item">
      <div styleName="color-square" style={{backgroundColor: color}} />
      <span style={{color: textColor}}>{title}</span>
      <div style={{marginLeft: 'auto'}}>
        <Checkbox checked={checked} onChange={onChange} />
      </div>
    </div>
  );
}

LegendItem.propTypes = {
  title: PropTypes.string.isRequired,
  color: PropTypes.string.isRequired,
  textColor: PropTypes.string.isRequired,
  checked: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
};

function CalendarLegend({items, groupBy, onFilterChanged, onElementSelected}) {
  const parsedItems = items.map(({id, title, checked, color, textColor}) => (
    <LegendItem
      key={id}
      title={title}
      color={color}
      textColor={textColor}
      checked={checked}
      onChange={(_, data) => onElementSelected(id, data.checked)}
    />
  ));
  const options = [
    {text: Translate.string('Category'), value: 'category'},
    {text: Translate.string('Location'), value: 'location'},
  ];
  return (
    <div>
      <h3>{Translate.string('Display by:')}</h3>
      <Select
        value={groupBy || 'category'}
        options={options}
        onChange={(_, {value}) => onFilterChanged(value)}
      />
      <div>{parsedItems}</div>
    </div>
  );
}

CalendarLegend.propTypes = {
  items: PropTypes.array.isRequired,
  groupBy: PropTypes.string.isRequired,
  onFilterChanged: PropTypes.func.isRequired,
  onElementSelected: PropTypes.func.isRequired,
};

export default CalendarLegend;
