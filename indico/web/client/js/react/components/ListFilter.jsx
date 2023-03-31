// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Icon, Input, Dropdown, Label} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './ListFilter.module.scss';

const FilterLabel = ({text, options, onClick}) => (
  <Label styleName="filter" className="fluid" color="orange" basic>
    <p>{text}</p>
    <Label.Detail className="float right">
      {_.sortBy(options, 'text').map(o => (
        <p key={o.value}>{o.text}</p>
      ))}
    </Label.Detail>
    <Icon name="delete" styleName="right" onClick={onClick} />
  </Label>
);

FilterLabel.propTypes = {
  text: PropTypes.string.isRequired,
  options: PropTypes.array.isRequired,
  onClick: PropTypes.func.isRequired,
};

export default function ListFilter({
  list,
  filters: externalFilters,
  searchText: externalSearchText,
  filterOptions,
  searchableId,
  searchableFields,
  onChangeFilters,
  onChangeSearchText,
  onChangeList,
}) {
  const [internalFilters, setInternalFilters] = useState({});
  const [internalSearchText, setInternalSearchText] = useState('');
  const [openSubmenu, setOpenSubmenu] = useState(-1);
  const filters = onChangeFilters ? externalFilters : internalFilters;
  const searchText = onChangeSearchText ? externalSearchText : internalSearchText;

  const setFilters = value => {
    if (onChangeFilters) {
      onChangeFilters(value);
      return;
    }
    setInternalFilters(value);
    const filtered = list.filter(x =>
      filterOptions.every(
        ({key, isMatch}) => !value[key] || !isMatch || isMatch(x, value[key] || [])
      )
    );
    onChangeList(new Set(filtered.map(e => e.id)));
  };

  const getLabelOpts = color => {
    if (color === 'default') {
      return {empty: true, circular: true};
    } else if (color) {
      return {color, empty: true, circular: true};
    }
    return null;
  };

  const setSearchText = value => {
    if (onChangeSearchText) {
      onChangeSearchText(value);
      return;
    }
    setInternalSearchText(value);
    value = value.toLowerCase().trim();
    let filtered = list;
    if (value) {
      filtered = list.filter(e => {
        if (searchableId) {
          const match = value.match(/^#(\d+)$/);
          if (match) {
            return searchableId(e) === +match[1];
          }
        }
        return !searchableFields || searchableFields(e).some(f => f.toLowerCase().includes(value));
      });
    }
    onChangeList(new Set(filtered.map(e => e.id)));
  };

  const toggleFilter = (key, option) => {
    const filter = filterOptions.find(x => x.key === key);
    const exclusive =
      filters[key] &&
      filter.options.find(
        o => (option === o.value || filters[key].includes(o.value)) && o.exclusive
      );
    const options = filters[key] || [];
    let selected = [...options, option];
    if (options.includes(option)) {
      selected = options.filter(x => x !== option);
    } else if (exclusive) {
      selected = [option];
    }
    if (!selected.length) {
      const {[key]: __, ...rest} = filters;
      setFilters(rest);
    } else {
      setFilters({...filters, [key]: selected});
    }
  };

  return (
    <div styleName="filters-container">
      <Dropdown
        text={Translate.string('Filter')}
        icon="filter"
        direction="left"
        labeled
        button
        className={Object.keys(filters).length > 0 ? 'orange icon' : 'icon'}
        onClose={() => setOpenSubmenu(-1)}
      >
        <Dropdown.Menu styleName="filters-menu">
          {Object.keys(filters).length > 0 ? (
            <>
              <div styleName="active-filters">
                {_.sortBy(filterOptions, 'text')
                  .filter(({key}) => filters[key])
                  .map(({key, text, options}) => (
                    <FilterLabel
                      key={key}
                      text={text}
                      options={options.filter(o => filters[key].includes(o.value))}
                      onClick={() => {
                        setOpenSubmenu(-1);
                        const {[key]: __, ...rest} = filters;
                        setFilters(rest);
                      }}
                    />
                  ))}
              </div>
              <Dropdown.Item
                text={Translate.string('Clear all filters')}
                onClick={() => setFilters({})}
              />
            </>
          ) : (
            <Dropdown.Item text={Translate.string('No filters were added yet')} disabled />
          )}
          <Dropdown.Divider />
          {_.sortBy(filterOptions, 'text').map(({key, text: filterText, options}) => (
            <Dropdown
              key={key}
              scrolling
              icon={null}
              className="item"
              direction="right"
              onOpen={() => setOpenSubmenu(key)}
              onBlur={evt => evt.stopPropagation()}
              open={openSubmenu === key}
              disabled={options.length === 0}
              trigger={<Dropdown.Item text={filterText} icon="plus" />}
            >
              <Dropdown.Menu>
                {_.sortBy(options.filter(o => !o.exclusive), 'text').map(
                  ({value: option, text, color}) => (
                    <Dropdown.Item
                      key={option}
                      value={option}
                      text={text}
                      label={getLabelOpts(color)}
                      active={filters[key]?.includes(option)}
                      onClick={(e, {value}) => toggleFilter(key, value)}
                    />
                  )
                )}
                {!!options.find(o => o.exclusive) && !!options.find(o => !o.exclusive) && (
                  <Dropdown.Divider />
                )}
                {options
                  .filter(o => o.exclusive)
                  .map(({value: option, text, color}) => (
                    <Dropdown.Item
                      key={option}
                      value={option}
                      text={text}
                      label={getLabelOpts(color)}
                      active={filters[key]?.includes(option)}
                      onClick={(e, {value}) => toggleFilter(key, value)}
                    />
                  ))}
              </Dropdown.Menu>
            </Dropdown>
          ))}
        </Dropdown.Menu>
      </Dropdown>
      <Input
        placeholder={Translate.string('Enter #id or search string')}
        onChange={(e, {value}) => setSearchText(value)}
        value={searchText}
        style={{width: '14em'}}
        icon={
          searchText
            ? {
                name: 'close',
                link: true,
                onClick: () => setSearchText(''),
              }
            : undefined
        }
      />
    </div>
  );
}

ListFilter.propTypes = {
  list: PropTypes.array,
  filters: PropTypes.object,
  searchText: PropTypes.string,
  filterOptions: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      text: PropTypes.string.isRequired,
      options: PropTypes.arrayOf(
        PropTypes.shape({
          value: PropTypes.string.isRequired,
          text: PropTypes.string.isRequired,
          exclusive: PropTypes.bool,
          color: PropTypes.string,
        })
      ).isRequired,
      isMatch: PropTypes.func,
    })
  ).isRequired,
  searchableId: PropTypes.func,
  searchableFields: PropTypes.func,
  onChangeList: PropTypes.func,
  onChangeFilters: PropTypes.func,
  onChangeSearchText: PropTypes.string,
};

ListFilter.defaultProps = {
  list: [],
  filters: undefined,
  searchText: undefined,
  searchableId: undefined,
  searchableFields: undefined,
  onChangeList: undefined,
  onChangeFilters: undefined,
  onChangeSearchText: undefined,
};
