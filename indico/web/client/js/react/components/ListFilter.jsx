// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
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

export default function ListFilter({list, filterOptions, onChange}) {
  const [activeFilters, setActiveFilters] = useState({search: '', filters: []});
  const [openSubmenu, setOpenSubmenu] = useState(-1);

  const handleChange = value => {
    const searchValue = value.search.toLowerCase().trim();

    const isMatchingEntry = entry => {
      if (searchValue) {
        if (entry.searchableId) {
          const match = searchValue.match(/^#(\d+)$/);
          if (match) {
            return entry.searchableId === +match[1];
          }
        }
        if (
          entry.searchableFields &&
          !entry.searchableFields.some(f => f.toLowerCase().includes(searchValue))
        ) {
          return false;
        }
      }
      return filterOptions.every(({key, isMatch}) => {
        const filter = value.filters.find(f => f.filter.key === key);
        return !filter || isMatch(entry, filter.selectedOptions);
      });
    };
    onChange(new Set(list.filter(isMatchingEntry).map(e => e.id)));
  };

  const handleSearchChange = search => {
    const newActiveFilters = {search, filters: activeFilters.filters};
    setActiveFilters(newActiveFilters);
    handleChange(newActiveFilters);
  };
  const handleFiltersChange = filters => {
    const newActiveFilters = {search: activeFilters.search, filters};
    setActiveFilters(newActiveFilters);
    handleChange(newActiveFilters);
  };

  const addFilter = (filter, selectedOptions) =>
    handleFiltersChange([...activeFilters.filters, {filter, selectedOptions}]);

  const removeFilter = key =>
    handleFiltersChange(activeFilters.filters.filter(f => f.filter.key !== key));

  const modifyFilter = (filter, selectedOptions) =>
    handleFiltersChange([
      ...activeFilters.filters.filter(f => f.filter.key !== filter.key),
      {filter, selectedOptions},
    ]);

  const toggleFilter = (filter, option, isExclusive) => {
    const activeFilter = activeFilters.filters.find(f => f.filter.key === filter.key);
    if (activeFilter) {
      if (activeFilter.selectedOptions.length === 1 && activeFilter.selectedOptions[0] === option) {
        removeFilter(filter.key);
      } else if (
        (isExclusive ||
          activeFilter.selectedOptions.some(so =>
            filter.options.find(o => o.value === so && o.exclusive)
          )) &&
        activeFilter.selectedOptions.find(o => o !== option)
      ) {
        modifyFilter(filter, [option]);
      } else {
        const selectedOptions = activeFilter.selectedOptions.includes(option)
          ? activeFilter.selectedOptions.filter(o => o !== option)
          : [...activeFilter.selectedOptions, option];
        modifyFilter(filter, selectedOptions);
      }
    } else {
      addFilter(filter, [option]);
    }
  };

  const isSelectedOption = (filterKey, option) =>
    activeFilters.filters.find(f => f.filter.key === filterKey)?.selectedOptions.includes(option);

  return (
    <div>
      <Dropdown
        text={Translate.string('Filter')}
        icon="filter"
        direction="left"
        labeled
        button
        className={activeFilters.filters.length > 0 ? 'orange icon' : 'icon'}
        onClose={() => setOpenSubmenu(-1)}
      >
        <Dropdown.Menu styleName="filters-menu">
          {activeFilters.filters.length > 0 ? (
            <>
              <div styleName="active-filters">
                {_.sortBy(activeFilters.filters, 'filter.text').map(({filter, selectedOptions}) => (
                  <Label key={filter.key} styleName="filter" className="fluid" color="orange" basic>
                    <p>{filter.text}</p>
                    <Label.Detail className="float right">
                      {_.sortBy(
                        filter.options.filter(o => selectedOptions.includes(o.value)),
                        'text'
                      ).map(o => (
                        <p key={o.value}>{o.text}</p>
                      ))}
                    </Label.Detail>
                    <Icon
                      name="delete"
                      styleName="right"
                      onClick={evt => {
                        evt.stopPropagation();
                        setOpenSubmenu(-1);
                        removeFilter(filter.key);
                      }}
                    />
                  </Label>
                ))}
              </div>
              <Dropdown.Item
                text={Translate.string('Clear all filters')}
                onClick={() => handleFiltersChange([])}
              />
            </>
          ) : (
            <Dropdown.Item text={Translate.string('No filters were added yet')} disabled />
          )}
          <Dropdown.Divider />
          {_.sortBy(filterOptions, 'text').map(filter => (
            <Dropdown
              key={filter.key}
              scrolling
              icon={null}
              className="item"
              direction="right"
              onOpen={() => setOpenSubmenu(filter.key)}
              onBlur={evt => evt.stopPropagation()}
              open={openSubmenu === filter.key}
              disabled={filter.options.length === 0}
              trigger={<Dropdown.Item text={filter.text} icon="plus" />}
            >
              <Dropdown.Menu>
                {_.sortBy(filter.options.filter(o => !o.exclusive), 'text').map(({value, text}) => (
                  <Dropdown.Item
                    key={value}
                    value={value}
                    text={text}
                    active={isSelectedOption(filter.key, value)}
                    onClick={(evt, {value: v}) => toggleFilter(filter, v, !filter.multi)}
                  />
                ))}
                {!!filter.options.find(o => o.exclusive) && <Dropdown.Divider />}
                {filter.options
                  .filter(o => o.exclusive)
                  .map(({value, text}) => (
                    <Dropdown.Item
                      key={value}
                      value={value}
                      text={text}
                      active={isSelectedOption(filter.key, value)}
                      onClick={(evt, {value: v}) => toggleFilter(filter, v, true)}
                    />
                  ))}
              </Dropdown.Menu>
            </Dropdown>
          ))}
        </Dropdown.Menu>
      </Dropdown>
      <Input
        placeholder={Translate.string('Enter #id or search string')}
        onChange={(evt, {value}) => handleSearchChange(value)}
        value={activeFilters.search}
        style={{width: '14em'}}
        icon={
          activeFilters.search
            ? {
                name: 'close',
                link: true,
                onClick: () => handleSearchChange(''),
              }
            : undefined
        }
      />
    </div>
  );
}

ListFilter.propTypes = {
  list: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      searchableId: PropTypes.number,
      searchableFields: PropTypes.arrayOf(PropTypes.string),
    })
  ),
  filterOptions: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      text: PropTypes.string.isRequired,
      options: PropTypes.arrayOf(
        PropTypes.shape({
          value: PropTypes.string.isRequired,
          text: PropTypes.string.isRequired,
          exclusive: PropTypes.bool,
        })
      ).isRequired,
      multi: PropTypes.bool,
      isMatch: PropTypes.func.isRequired,
    })
  ).isRequired,
  onChange: PropTypes.func.isRequired,
};

ListFilter.defaultProps = {list: []};
