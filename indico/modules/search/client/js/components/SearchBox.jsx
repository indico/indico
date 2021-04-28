// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Form, Icon, Label, Search} from 'semantic-ui-react';
import './SearchBox.module.scss';

import {Translate} from 'indico/react/i18n';

const resultRenderer = ({label}, keyword) => (
  <div styleName="option">
    <span>
      <Icon name="search" />
      {keyword}
    </span>
    <Label content={label} size="small" />
  </div>
);

export default function SearchBox({onSearch, category}) {
  const [keyword, setKeyword] = useState('');
  const options = !category.isRoot
    ? [
        {value: 'category', title: category.title, label: 'In this category ↵'},
        {value: 'global', title: 'Global', label: 'All Indico ↵'},
      ]
    : [];

  const handleSearchChange = event => {
    setKeyword(event.target.value);
  };

  // form submit happens when no option is selected in search (eg. in home category)
  const handleSubmit = () => {
    if (!keyword) {
      return;
    }

    console.log('handleSubmit', keyword, category.isRoot);
    onSearch(keyword, category.isRoot);
  };

  const handleResultSelect = (e, data) => {
    onSearch(keyword, data.result.value === 'global');
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Search
        input={{fluid: true}}
        placeholder={Translate.string('Enter your search term')}
        results={options}
        value={keyword}
        showNoResults={false}
        onResultSelect={handleResultSelect}
        onSearchChange={handleSearchChange}
        resultRenderer={results => resultRenderer(results, keyword)}
        fluid
        selectFirstResult
      />
    </Form>
  );
}

SearchBox.propTypes = {
  onSearch: PropTypes.func.isRequired,
  category: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    isRoot: PropTypes.bool.isRequired,
  }).isRequired,
};
