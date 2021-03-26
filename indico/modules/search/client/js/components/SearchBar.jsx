// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState, useEffect} from 'react';
import {Form, Label, Search} from 'semantic-ui-react';
import './SearchBar.module.scss';

import {Translate} from 'indico/react/i18n';

// TODO: query from indico
const placeholders = [
  {title: 'title:', label: 'An entry title (such as: event, contribution, attachment, event_note)'},
  {title: 'person:', label: "A speaker, author or event chair's name"},
  {title: 'affiliation:', label: "A speaker, author or event chair's affiliation"},
  {title: 'type:', label: 'An entry type (such as: conference, meeting, link, PDF)'},
  {title: 'venue:', label: "The event's venue name"},
  {title: 'keyword:', label: 'A keyword associated with an event'},
];

const resultRenderer = ({title, label}) => (
  <span styleName="placeholder">
    <Label content={title} styleName="label" /> {label}
  </span>
);

export default function SearchBar({onSearch, searchTerm}) {
  const [keyword, setKeyword] = useState(searchTerm);
  const [results, setResults] = useState(placeholders);
  const [isSearchOpen, setSearchOpen] = useState(false);

  const handleSubmit = event => {
    event.preventDefault();
    setSearchOpen(false);
    onSearch(keyword);
  };

  const handleSearchChange = (e, data) => {
    const queries = data.value.split(/\s+/);
    const value = queries[queries.length - 1];
    setResults(placeholders.filter(x => !value || x.title.startsWith(value)));
    setSearchOpen(true);
    setKeyword(data.value);
  };

  const handleResultSelect = (e, data) => {
    const queries = data.value.split(/\s+/).slice(0, -1);
    queries.push(data.result.title);
    setKeyword(queries.join(' '));
  };

  useEffect(() => {
    setKeyword(searchTerm);
  }, [searchTerm]);

  return (
    <Form onSubmit={handleSubmit}>
      <Search
        input={{fluid: true}}
        placeholder={Translate.string('Enter your search term')}
        results={results}
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
    </Form>
  );
}

SearchBar.propTypes = {
  onSearch: PropTypes.func.isRequired,
  searchTerm: PropTypes.string.isRequired,
};
