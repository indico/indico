// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState, useEffect} from 'react';
import {Form, Label, Search} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './SearchBar.module.scss';

const resultRenderer = ({title, label}) => (
  <span styleName="placeholder">
    <Label content={title} styleName="label" /> {label}
  </span>
);

export default function SearchBar({onSearch, searchTerm, placeholders}) {
  const [keyword, setKeyword] = useState(searchTerm);
  const [results, setResults] = useState(null);
  const [isSearchOpen, setSearchOpen] = useState(false);

  const handleSubmit = event => {
    event.preventDefault();
    setSearchOpen(false);
    if (keyword.trim()) {
      onSearch(keyword.trim());
    }
  };

  const handleSearchChange = (e, data) => {
    const queries = data.value.split(/\s+/);
    const value = queries[queries.length - 1];
    setResults(placeholders.filter(x => !value || x.key.startsWith(value)));
    setSearchOpen(true);
    setKeyword(data.value);
  };

  const handleResultSelect = (e, data) => {
    const queries = data.value.split(/\s+/).slice(0, -1);
    queries.push(`${data.result.title}:`);
    setKeyword(queries.join(' '));
  };

  useEffect(() => {
    setKeyword(searchTerm);
  }, [searchTerm]);

  useEffect(() => {
    setResults(placeholders);
  }, [placeholders]);

  return (
    <Form onSubmit={handleSubmit}>
      <label styleName="search-field">
        <Translate as="span">Search Indico</Translate>
        <Search
          input={{fluid: true}}
          placeholder={Translate.string('Enter your search term')}
          results={results?.map(x => ({title: x.key, label: x.label}))}
          value={keyword}
          open={isSearchOpen}
          showNoResults={false}
          onResultSelect={handleResultSelect}
          onSearchChange={handleSearchChange}
          resultRenderer={resultRenderer}
          onFocus={() => setSearchOpen(true)}
          onBlur={() => setSearchOpen(false)}
          fluid
        />
      </label>
    </Form>
  );
}

SearchBar.propTypes = {
  onSearch: PropTypes.func.isRequired,
  searchTerm: PropTypes.string.isRequired,
  placeholders: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string,
      label: PropTypes.string,
    })
  ),
};

SearchBar.defaultProps = {
  placeholders: [],
};
