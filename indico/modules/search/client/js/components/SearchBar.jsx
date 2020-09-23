// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState, useEffect} from 'react';
import PropTypes from 'prop-types';
import {Form} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

export default function SearchBar({onSearch, searchTerm}) {
  const [keyword, setKeyword] = useState(searchTerm);

  const handleChange = event => {
    setKeyword(event.target.value);
  };

  const handleSubmit = event => {
    event.preventDefault();
    onSearch(keyword);
  };

  useEffect(() => {
    setKeyword(searchTerm);
  }, [searchTerm]);

  return (
    <Form onSubmit={handleSubmit}>
      <Form.Input
        action={Translate.string('Search')}
        placeholder={Translate.string('Enter your search term')}
        value={keyword}
        onChange={handleChange}
      />
    </Form>
  );
}

SearchBar.propTypes = {
  onSearch: PropTypes.func.isRequired,
  searchTerm: PropTypes.string.isRequired,
};
