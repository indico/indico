// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Checkbox, Select} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import './CalendarLegend.module.scss';

function LegendItem({title, color, checked, url, isSpecial, onChange}) {
  return (
    <div styleName="legend-item">
      <div styleName="color-square" style={{backgroundColor: color}} />
      <span styleName={isSpecial ? 'italic' : undefined} style={{color: 'black'}}>
        {url && !isSpecial ? <a href={url}>{title}</a> : title}
      </span>
      <Checkbox styleName="legend-checkbox" checked={checked} onChange={onChange} />
    </div>
  );
}

LegendItem.propTypes = {
  title: PropTypes.string.isRequired,
  color: PropTypes.string.isRequired,
  url: PropTypes.string,
  checked: PropTypes.bool,
  isSpecial: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
};

LegendItem.defaultProps = {
  url: undefined,
  checked: true,
  isSpecial: false,
};

function CalendarLegend({items, groupBy, onFilterChanged, onElementSelected}) {
  const [isOpen, setIsOpen] = useState(false);
  const parsedItems = items.map(({id, title, checked, url, color, isSpecial}) => (
    <LegendItem
      key={id}
      title={title}
      color={color}
      checked={checked}
      onChange={(_, data) => onElementSelected(id, data.checked)}
      url={url}
      isSpecial={isSpecial}
    />
  ));
  const options = [
    {text: Translate.string('Category'), value: 'category'},
    {text: Translate.string('Venue'), value: 'location'},
  ];
  const onChange = (_, {value}) => {
    onFilterChanged(value);
    setIsOpen(false);
  };
  return (
    <div>
      <h3>{Translate.string('Display by:')}</h3>
      <Select
        value={groupBy || 'category'}
        open={isOpen}
        options={options}
        onClick={() => setIsOpen(!isOpen)}
        onBlur={() => setIsOpen(false)}
        onChange={onChange}
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
