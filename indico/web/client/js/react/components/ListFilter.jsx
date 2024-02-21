// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {Icon, Input, Dropdown, Label} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './ListFilter.module.scss';

const optionSchema = PropTypes.shape({
  value: PropTypes.string.isRequired,
  text: PropTypes.string.isRequired,
  exclusive: PropTypes.bool,
  color: PropTypes.string,
});

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
  options: PropTypes.arrayOf(optionSchema).isRequired,
  onClick: PropTypes.func.isRequired,
};

export default function ListFilter({
  name,
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
  const [loadedFilters, setLoadedFilters] = useState(false);
  const filters = onChangeFilters ? externalFilters : internalFilters;
  const searchText = onChangeSearchText ? externalSearchText : internalSearchText;
  const optionsMap = useMemo(() => new Map(filterOptions.map(o => [o.key, o])), [filterOptions]);

  const matchFilters = useCallback(
    (value, e) =>
      filterOptions.every(
        ({key, isMatch}) => !value[key] || !isMatch || isMatch(e, Object.keys(value[key] || {}))
      ),
    [filterOptions]
  );

  const matchSearch = useCallback(
    (value, e) => {
      if (!value) {
        return true;
      }
      if (searchableId) {
        const match = value.match(/^#(\d+)$/);
        if (match) {
          return searchableId(e) === +match[1];
        }
      }
      return (
        !searchableFields ||
        searchableFields(e).some(f => f.toLowerCase().includes(value.toLowerCase()))
      );
    },
    [searchableId, searchableFields]
  );

  const setFilters = useCallback(
    value => {
      if (onChangeFilters) {
        onChangeFilters(value);
        return;
      }
      setInternalFilters(value);
      const filtered = list.filter(e => matchFilters(value, e) && matchSearch(searchText, e));
      onChangeList(new Set(filtered.map(e => e.id)));
    },
    [onChangeFilters, onChangeList, list, matchFilters, matchSearch, searchText]
  );

  const getLabelOpts = color => {
    if (color === 'default') {
      return {empty: true, circular: true};
    } else if (color) {
      return {color, empty: true, circular: true};
    }
    return null;
  };

  const setSearchText = useCallback(
    value => {
      if (onChangeSearchText) {
        onChangeSearchText(value);
        return;
      }
      setInternalSearchText(value);
      value = value.toLowerCase().trim();
      const filtered = list.filter(e => matchFilters(filters, e) && matchSearch(value, e));
      onChangeList(new Set(filtered.map(e => e.id)));
    },
    [onChangeSearchText, onChangeList, list, matchFilters, matchSearch, filters]
  );

  const toggleFilter = (filterKey, optionValue) => {
    const optionObject = optionsMap.get(filterKey).options.find(x => x.value === optionValue);
    let selectedOptions = filters[filterKey] || {};
    if (optionValue in selectedOptions) {
      if (Object.keys(selectedOptions).length === 1) {
        const {[filterKey]: __, ...rest} = filters;
        setFilters(rest);
        return;
      }
      const {[optionValue]: __, ...rest} = selectedOptions;
      selectedOptions = rest;
    } else if (optionObject.exclusive) {
      selectedOptions = {[optionValue]: optionObject};
    } else {
      selectedOptions = {...selectedOptions, [optionValue]: optionObject};
    }
    setFilters({...filters, [filterKey]: selectedOptions});
  };

  // store filters in the local storage
  useEffect(() => {
    if (loadedFilters) {
      localStorage.setItem(name, JSON.stringify({filters, searchText}));
      return;
    }
    const storedFilters = JSON.parse(localStorage.getItem(name));
    if (storedFilters) {
      setFilters(_.pickBy(storedFilters.filters, (__, key) => optionsMap.has(key)));
      setSearchText(storedFilters.searchText);
    }
    setLoadedFilters(true);
  }, [filters, loadedFilters, name, optionsMap, searchText, setFilters, setSearchText]);

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
        loading={!loadedFilters || filterOptions.length === 0}
      >
        <Dropdown.Menu styleName="filters-menu">
          {Object.keys(filters).length > 0 ? (
            <>
              <div styleName="active-filters">
                {Object.entries(filters)
                  .sort(([a], [b]) => optionsMap.get(a).text.localeCompare(optionsMap.get(b).text))
                  .map(([key, filter]) => (
                    <FilterLabel
                      key={key}
                      text={optionsMap.get(key).text}
                      options={Object.values(filter)}
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
                      active={option in (filters[key] || {})}
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
                      active={option in (filters[key] || {})}
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
  name: PropTypes.string.isRequired,
  list: PropTypes.array.isRequired,
  filters: PropTypes.objectOf(PropTypes.objectOf(optionSchema)),
  searchText: PropTypes.string,
  filterOptions: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      text: PropTypes.string.isRequired,
      options: PropTypes.arrayOf(optionSchema).isRequired,
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
  filters: undefined,
  searchText: undefined,
  searchableId: undefined,
  searchableFields: undefined,
  onChangeList: undefined,
  onChangeFilters: undefined,
  onChangeSearchText: undefined,
};
