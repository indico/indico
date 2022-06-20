// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useCallback, useEffect, useMemo, useState} from 'react';
import {Dropdown} from 'semantic-ui-react';

import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {makeAsyncDebounce} from 'indico/utils/debounce';

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

export function RemoteSearchDropdown({
  searchUrl,
  searchMethod,
  searchPayload,
  minTriggerLength,
  allowById,
  preload,
  valueField,
  labelField,
  searchField,
  value: valueFromProps,
  onChange: onChangeFromProps,
  ...dropdownProps
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);

  const isControlled = valueFromProps !== undefined;
  const [internalValue, setInternalValue] = useState(null);
  const value = isControlled ? valueFromProps : internalValue;

  const debounce = useMemo(() => makeAsyncDebounce(200), []);

  const getIdFromQuery = query => (query.match(/^#(\d+)$/) || {1: null})[1];

  if (preload) {
    // No need to limit the search length when all data is preloaded
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
    return opts
      .filter(opt => (id === null ? opt.search.includes(query) : +opt['friendly-id'] === +id))
      .map(opt => ({
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
      return _.sortBy(opts, 'text');
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

      setOptions(transformOptions(response.data));
    },
    [searchUrl, searchMethod, searchPayload, transformOptions, debounce]
  );

  useEffect(() => {
    if (preload) {
      fetchData();
    }
  }, [preload, fetchData]);

  useEffect(() => {
    if (preload) {
      return;
    }

    let params;
    const id = getIdFromQuery(searchQuery);
    if (allowById && id !== null) {
      params = {id};
    } else if (searchQuery.length >= minTriggerLength) {
      params = {q: searchQuery};
    }

    if (params) {
      fetchData(params);
    }
  }, [preload, allowById, minTriggerLength, searchQuery, fetchData]);

  const onChange = (evt, {value: newValue}) => {
    setSearchQuery('');
    onChangeFromProps(newValue);
    if (!isControlled) {
      setInternalValue(newValue);
    }
  };

  const onSearch = (evt, {searchQuery: newSearchQuery}) => {
    setSearchQuery(newSearchQuery);
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
      required
      fluid
      selection
      selectOnNavigation={false}
      selectOnBlur={false}
      clearable={false}
      defaultOpen={false}
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
      {...dropdownProps}
    />
  );
}

RemoteSearchDropdown.propTypes = {
  minTriggerLength: PropTypes.number,
  searchUrl: PropTypes.string,
  searchMethod: PropTypes.string,
  searchPayload: PropTypes.object,
  valueField: PropTypes.string,
  labelField: PropTypes.string,
  searchField: PropTypes.string,
  allowById: PropTypes.bool,
  preload: PropTypes.bool,
  value: PropTypes.oneOfType([PropTypes.bool, PropTypes.string, PropTypes.number]),
  onChange: PropTypes.func,
};

RemoteSearchDropdown.defaultProps = {
  minTriggerLength: 3,
  searchUrl: null,
  searchMethod: 'GET',
  searchPayload: {},
  valueField: 'id',
  labelField: 'name',
  searchField: 'name',
  allowById: false,
  preload: false,
  value: undefined,
  onChange: () => {},
};

export default function WTFRemoteSearchDropdown({fieldId, ...rest}) {
  const field = useMemo(() => document.getElementById(`${fieldId}-data`), [fieldId]);
  const onChange = value => {
    field.value = value;
    field.dispatchEvent(new Event('change', {bubbles: true}));
  };
  return <RemoteSearchDropdown onChange={onChange} {...rest} />;
}

WTFRemoteSearchDropdown.propTypes = {
  fieldId: PropTypes.string.isRequired,
};
