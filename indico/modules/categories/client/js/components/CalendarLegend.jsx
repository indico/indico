// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useRef, useState} from 'react';
import {Select} from 'semantic-ui-react';

import {Checkbox} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import './CalendarLegend.module.scss';

function LegendItem({
  title,
  color,
  checked,
  url,
  isSpecial,
  onChange,
  depth,
  indeterminate,
  hasSubitems,
}) {
  const checkboxRef = useRef(null);
  const handleDivClick = () => {
    if (checkboxRef.current) {
      checkboxRef.current.handleChange();
    }
  };
  const textStyle = {color: 'black'};
  if (hasSubitems) {
    textStyle.fontWeight = 'bold';
  }
  return (
    <div styleName="legend-item" onClick={handleDivClick} style={{marginLeft: depth * 30}}>
      {color ? <div styleName="color-square" style={{backgroundColor: color}} /> : undefined}
      {hasSubitems ? <div styleName="color-square" /> : undefined}
      <span styleName={isSpecial ? 'italic' : undefined} style={textStyle}>
        {url && !isSpecial ? (
          <a href={url} onClick={e => e.stopPropagation()}>
            {title}
          </a>
        ) : (
          title
        )}
      </span>
      <Checkbox
        ref={checkboxRef}
        styleName="legend-checkbox"
        checked={checked}
        onChange={onChange}
        indeterminate={indeterminate}
      />
    </div>
  );
}

LegendItem.propTypes = {
  title: PropTypes.string.isRequired,
  color: PropTypes.string,
  url: PropTypes.string,
  checked: PropTypes.bool,
  isSpecial: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  depth: PropTypes.number,
  indeterminate: PropTypes.bool,
  hasSubitems: PropTypes.bool,
};

LegendItem.defaultProps = {
  url: undefined,
  checked: true,
  isSpecial: false,
  depth: 0,
  color: undefined,
  indeterminate: false,
  hasSubitems: false,
};

function mapPlainItemToLegendItem(item, onElementSelected, depth) {
  const hasSubitems = item.subitems.length > 0;
  const indeterminate =
    hasSubitems && item.subitems.some(si => si.checked) && item.subitems.some(si => !si.checked);
  const result = (
    <LegendItem
      key={item.id}
      title={item.title}
      color={item.color}
      checked={item.checked}
      onChange={(_, data) => onElementSelected(item, data.checked)}
      url={item.url}
      isSpecial={item.isSpecial}
      depth={depth}
      indeterminate={indeterminate}
      hasSubitems={hasSubitems}
    />
  );
  return [
    result,
    ...item.subitems.map(si => mapPlainItemToLegendItem(si, onElementSelected, depth + 1)),
  ];
}

function CalendarLegend({
  items,
  groupBy,
  onFilterChanged,
  onElementSelected,
  selectAll,
  deselectAll,
  filterByKeywords,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const parsedItems = items.map(item => mapPlainItemToLegendItem(item, onElementSelected, 0));
  const options = [
    {text: Translate.string('Category'), value: 'category'},
    {text: Translate.string('Venue'), value: 'location'},
    {text: Translate.string('Room'), value: 'room'},
  ];
  if (filterByKeywords) {
    options.push({text: Translate.string('Keywords'), value: 'keywords'});
  }
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
      <div styleName="toggle-container">
        <span onClick={selectAll} style={{cursor: 'pointer', marginRight: '8px'}}>
          <Translate>Select all</Translate>
        </span>
        {' | '}
        <span onClick={deselectAll} style={{cursor: 'pointer', marginLeft: '8px'}}>
          <Translate>Clear</Translate>
        </span>
      </div>
      <div>{parsedItems}</div>
    </div>
  );
}

CalendarLegend.propTypes = {
  items: PropTypes.array.isRequired,
  groupBy: PropTypes.string.isRequired,
  onFilterChanged: PropTypes.func.isRequired,
  onElementSelected: PropTypes.func.isRequired,
  selectAll: PropTypes.func.isRequired,
  deselectAll: PropTypes.func.isRequired,
  filterByKeywords: PropTypes.bool,
};

CalendarLegend.defaultProps = {
  filterByKeywords: false,
};

export default CalendarLegend;
