// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {Dropdown} from 'semantic-ui-react';

import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {makeAsyncDebounce} from 'indico/utils/debounce';

import './WTFSearchDropdown.module.scss';

const naturalSort = (options, key = 'text') => {
  const collator = new Intl.Collator(undefined, {numeric: true, sensitivity: 'base'});
  return options.sort((a, b) => collator.compare(a[key], b[key]));
};

const highlightSearch = (text, query = '') => {
  const index = text.toLowerCase().indexOf(query);
  if (!query || index === -1) {
    return text;
  }

  return (
    <>
      {text.slice(0, index)}
      <mark>{text.slice(index, index + query.length)}</mark>
      {text.slice(index + query.length)}
    </>
  );
};

/**
 * Dropdown which can be passed the options or dynamically query the backend
 * for results using the search input. This is a replacement
 * for the selectize.js library.
 *
 * It can be both controlled and uncontrolled.
 * To make it controlled pass the value prop to it.
 */
export function SearchDropdown({
  searchUrl,
  searchMethod,
  searchPayload,
  minTriggerLength,
  allowById,
  preload,
  valueField,
  labelField,
  searchField,
  defaultValue,
  value: valueFromProps,
  onChange: onChangeFromProps,
  options: optionsFromProps,
  allowAdditions,
  multiple,
  dropdownProps,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);

  const isControlled = valueFromProps !== undefined;
  const initialValue = defaultValue.map(val => val[valueField]);
  const [internalValue, setInternalValue] = useState(
    initialValue ? (multiple ? initialValue : initialValue[0]) : null
  );
  const value = isControlled ? valueFromProps : internalValue;

  const debounce = useMemo(() => makeAsyncDebounce(200), []);

  const getIdFromQuery = query => (query.match(/^#(\d+)$/) || {1: null})[1];

  if (preload || !searchUrl) {
    // No need to limit the search length when all data is preloaded or static
    minTriggerLength = 0;
  }
  const searchDisabled =
    searchQuery.length < minTriggerLength && (!allowById || getIdFromQuery(searchQuery) === null);

  const filterOptions = (opts, query) => {
    if (searchDisabled) {
      return [];
    }
    query = query.toLowerCase();
    const id = getIdFromQuery(query);
    opts = opts.filter(opt =>
      id === null ? opt.search.includes(query) : +opt['friendly-id'] === +id
    );
    return allowAdditions
      ? opts
      : opts.map(opt => ({
          ...opt,
          // this might lead to some unexpected results when
          // searchField !== labelField, because the filtering is done
          // on searchField but highlighting happens on labelField
          text: highlightSearch(opt.text, query),
        }));
  };

  const transformOptions = useCallback(
    data => {
      if (!Array.isArray(data)) {
        return [];
      }

      const opts = data.map(item => ({
        'key': item[valueField],
        'value': item[valueField],
        'text': item[labelField],
        // extra values passed to <Dropdown.Item>
        'search': item[searchField].toLowerCase(),
        'friendly-id': item.friendly_id,
      }));
      return naturalSort(opts);
    },
    [valueField, labelField, searchField]
  );

  const fetchData = useCallback(
    async (params = {}) => {
      if (!searchUrl) {
        return;
      }

      if (searchPayload) {
        params = {...params, ...searchPayload};
      }

      let response;
      try {
        setLoading(true);
        response = await debounce(() =>
          indicoAxios({
            url: searchUrl,
            method: searchMethod,
            params,
          })
        );
      } catch (error) {
        handleAxiosError(error);
        return;
      } finally {
        setLoading(false);
      }
      if (!preload && multiple) {
        if (response.data.length !== 0) {
          const id = response.data[0][valueField];
          setOptions(prevOptions => {
            const prevKeys = prevOptions.map(opt => opt.key);
            if (prevKeys.includes(id)) {
              return prevOptions;
            }
            return [...prevOptions, ...transformOptions(response.data)];
          });
        }
      } else {
        setOptions(transformOptions(response.data));
      }
    },
    [
      searchUrl,
      searchPayload,
      preload,
      multiple,
      debounce,
      searchMethod,
      valueField,
      transformOptions,
    ]
  );

  useEffect(() => {
    if (optionsFromProps.length !== 0) {
      setOptions(transformOptions(optionsFromProps));
      return;
    }
    if (!preload && defaultValue.length !== 0) {
      setOptions(prevOptions => [...prevOptions, ...transformOptions(defaultValue)]);
    }
    if (preload) {
      fetchData();
    }
  }, [preload, fetchData, optionsFromProps, transformOptions, defaultValue]);

  const onChange = (evt, {value: newValue}) => {
    setSearchQuery('');
    onChangeFromProps(newValue);
    if (!isControlled) {
      setInternalValue(newValue);
    }
  };

  const onAddItem = (evt, {value: newValue}) => {
    const newOption = transformOptions([
      {[labelField]: newValue, [valueField]: newValue, [searchField]: newValue},
    ])[0];
    setOptions(prevOptions => [...prevOptions, newOption]);
  };

  const onSearch = (evt, {searchQuery: newSearchQuery}) => {
    setSearchQuery(newSearchQuery);

    if (preload || optionsFromProps.length !== 0) {
      return;
    }

    let params;
    const id = getIdFromQuery(newSearchQuery);
    if (allowById && id !== null) {
      params = {id};
    } else if (newSearchQuery.length >= minTriggerLength) {
      params = {q: newSearchQuery};
    }

    if (params) {
      fetchData(params);
    }
  };

  const searchDisabledMessage =
    minTriggerLength === 0 ? (
      undefined
    ) : allowById ? (
      <PluralTranslate count={minTriggerLength}>
        <Singular>
          Search requires at least <Param name="count" value={minTriggerLength} /> character or an
          id prefixed with #
        </Singular>
        <Plural>
          Search requires at least <Param name="count" value={minTriggerLength} /> characters or an
          id prefixed with #
        </Plural>
      </PluralTranslate>
    ) : (
      <PluralTranslate count={minTriggerLength}>
        <Singular>
          Search requires at least <Param name="count" value={minTriggerLength} /> character
        </Singular>
        <Plural>
          Search requires at least <Param name="count" value={minTriggerLength} /> characters
        </Plural>
      </PluralTranslate>
    );

  return (
    <Dropdown
      styleName="dropdown"
      fluid
      selection
      clearable={!dropdownProps.required && !multiple}
      selectOnNavigation={false}
      selectOnBlur={false}
      defaultOpen={false}
      openOnFocus={false}
      value={value}
      options={options}
      onChange={onChange}
      search={filterOptions}
      searchQuery={searchQuery}
      onSearchChange={onSearch}
      noResultsMessage={
        loading ? Translate.string('Loading…') : searchDisabled ? searchDisabledMessage : undefined
      }
      loading={loading}
      multiple={multiple}
      allowAdditions={allowAdditions}
      onAddItem={onAddItem}
      renderLabel={label => ({color: 'blue', content: label.text})}
      {...dropdownProps}
    />
  );
}

SearchDropdown.propTypes = {
  /** Number of characters needed to start fetching results. */
  minTriggerLength: PropTypes.number,
  /** The URL used to retrieve items */
  searchUrl: PropTypes.string,
  /** The method used to retrieve items */
  searchMethod: PropTypes.string,
  /** Extra params to attach to the request */
  searchPayload: PropTypes.object,
  /** The property of the response item used as the value */
  valueField: PropTypes.string,
  /** The property of the response used to display the item */
  labelField: PropTypes.string,
  /** The property of the response used to filter the items*/
  searchField: PropTypes.string,
  /** Whether to allow `#123` searches regardless of the trigger length.
      Such searches will be sent as 'id' instead of 'q' in the AJAX request */
  allowById: PropTypes.bool,
  /** Whether to preload all data with a single request. All subsequent searches
      will be done locally on the returned data. This also sets minTriggerLength to zero. */
  preload: PropTypes.bool,
  /** Use this prop to make the component controlled */
  value: PropTypes.oneOfType([PropTypes.bool, PropTypes.string, PropTypes.number, PropTypes.array]),
  /** Called when the value changes with the new value as the first argument */
  onChange: PropTypes.func,
  /** Default value to be set as the first internalValue of the dropdown, if present. */
  defaultValue: PropTypes.array,
  /** Options to pass to the dropdown. If options are passed then the component does not
      dynamically fetch the data */
  options: PropTypes.array,
  /** Allow adding new values to the options */
  allowAdditions: PropTypes.bool,
  /** Allow selecting multiple values */
  multiple: PropTypes.bool,
  /** Extra props to pass to <Dropdown /> */
  dropdownProps: PropTypes.object,
};

SearchDropdown.defaultProps = {
  minTriggerLength: 3,
  searchUrl: null,
  searchMethod: 'GET',
  searchPayload: {},
  valueField: 'id',
  labelField: 'name',
  searchField: 'name',
  allowById: false,
  preload: false,
  defaultValue: [],
  value: undefined,
  onChange: () => {},
  options: [],
  allowAdditions: false,
  multiple: false,
  dropdownProps: {},
};

/**
 * WTForms wrapper for SearchDropdown
 */
export default function WTFSearchDropdown({fieldId, multiple, ...rest}) {
  const field = useMemo(() => document.getElementById(`${fieldId}-data`), [fieldId]);
  const onChange = value => {
    field.value = multiple ? JSON.stringify(value) : value;
    field.dispatchEvent(new Event('change', {bubbles: true}));
  };
  return <SearchDropdown onChange={onChange} multiple={multiple} {...rest} />;
}

WTFSearchDropdown.propTypes = {
  fieldId: PropTypes.string.isRequired,
  multiple: PropTypes.bool,
};

WTFSearchDropdown.defaultProps = {
  multiple: false,
};
