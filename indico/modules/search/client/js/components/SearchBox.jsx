// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
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
  <div styleName="option">
    <span>
      <Icon name="search" />
      {keyword}
    </span>
    <Label content={label} size="small" />
  </div>
);

export default function SearchBox({onSearch, category, isAdmin}) {
  const [keyword, setKeyword] = useState('');
  const [allowAdmin, setAllowAdmin] = useState(false);
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
      value: 'global',
      title: 'allowAdmin',
      className: 'cursor-default',
      onClick: () => {},
      // eslint-disable-next-line
      renderer: () => (
        <div styleName="option">
          <Label content={Translate.string('ADMIN')} size="small" color="red" />
          <Checkbox
            styleName="checkbox-admin-search"
            label={Translate.string('Skip access checks')}
            checked={allowAdmin}
            onChange={e => {
              e.stopPropagation();
              setAllowAdmin(curAllowAdmin => !curAllowAdmin);
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
      onSearch(keyword.trim(), category ? category.isRoot : true, allowAdmin);
    }
  };

  const handleResultSelect = (e, data) => {
    if (data.result.title === 'allowAdmin') {
      setAllowAdmin(curAllowAdmin => !curAllowAdmin);
    } else if (keyword.trim()) {
      onSearch(keyword.trim(), data.result.value === 'global', allowAdmin);
    }
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Search
        input={{fluid: true}}
        placeholder={Translate.string('Enter your search term')}
        results={options}
        value={keyword}
        showNoResults={false}
        open={!!keyword.length}
        onResultSelect={handleResultSelect}
        onSearchChange={handleSearchChange}
        fluid
        // only select the first result if there is more than 1 (means we are in a category)
        selectFirstResult={options.length > 1}
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
  }),
  isAdmin: PropTypes.bool.isRequired,
};

SearchBox.defaultProps = {
  category: null,
};
