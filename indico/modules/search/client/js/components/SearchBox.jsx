// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Checkbox, Form, Icon, Label, Search} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './SearchBox.module.scss';

const renderResult = ({label}, keyword) => (
  <div styleName="search-type-option">
    <span>
      <Icon name="search" />
      {keyword}
    </span>
    <Label content={label} size="small" />
  </div>
);

export default function SearchBox({onSearch, category, isAdmin}) {
  const [keyword, setKeyword] = useState('');
  const [adminOverrideEnabled, setAdminOverrideEnabled] = useState(false);
  const options =
    category && !category.isRoot
      ? [
          {
            value: 'category',
            label: Translate.string('In this category ↵'),
            title: category.title,
            renderer: props => renderResult(props, keyword),
          },
          {
            value: 'global',
            label: Translate.string('All Indico ↵'),
            title: 'Global',
            renderer: props => renderResult(props, keyword),
          },
        ]
      : [];
  if (isAdmin) {
    options.push({
      value: 'enableAdminOverride',
      title: 'Enable admin override',
      className: 'cursor-default',
      onClick: () => {},
      // eslint-disable-next-line react/display-name
      renderer: () => (
        <div styleName="search-type-option">
          <Label content={Translate.string('ADMIN')} size="small" color="red" />
          <Checkbox
            id="checkbox-admin-search"
            styleName="checkbox-admin-search"
            label={Translate.string('Skip access checks')}
            checked={adminOverrideEnabled}
            onChange={e => {
              e.stopPropagation();
              setAdminOverrideEnabled(!adminOverrideEnabled);
            }}
          />
        </div>
      ),
    });
  }

  const handleSearchChange = event => {
    setKeyword(event.target.value);
  };

  const handleSubmit = () => {
    if (keyword.trim()) {
      onSearch(keyword.trim(), category ? category.isRoot : true, adminOverrideEnabled);
    }
  };

  const handleResultSelect = (e, data) => {
    if (data.result.value === 'enableAdminOverride') {
      setAdminOverrideEnabled(!adminOverrideEnabled);
    } else if (keyword.trim()) {
      onSearch(keyword.trim(), data.result.value === 'global', adminOverrideEnabled);
    }
  };

  return (
    <Form onSubmit={handleSubmit}>
      <label styleName="search-field">
        <Translate as="span">Search Indico</Translate>
        <Search
          input={{fluid: true}}
          placeholder={Translate.string('Enter your search term')}
          results={options}
          value={keyword}
          showNoResults={false}
          open={!!keyword}
          onResultSelect={handleResultSelect}
          onSearchChange={handleSearchChange}
          fluid
          // only select the first result if there is more than 1 (means we are in a category)
          selectFirstResult={options.length > 1}
        />
      </label>
    </Form>
  );
}

SearchBox.propTypes = {
  onSearch: PropTypes.func.isRequired,
  category: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    isRoot: PropTypes.bool.isRequired,
  }),
  isAdmin: PropTypes.bool.isRequired,
};

SearchBox.defaultProps = {
  category: null,
};
