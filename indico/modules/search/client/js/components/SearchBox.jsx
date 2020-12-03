// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Form} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

export default function SearchBox({onSearch}) {
  const [keyword, setKeyword] = useState('');
  const handleChange = event => {
    setKeyword(event.target.value);
  };
  const handleSubmit = () => {
    onSearch(keyword);
  };
  return (
    <Form onSubmit={handleSubmit}>
      <Form.Input
        action={{icon: 'search', size: 'tiny', disabled: !keyword}}
        placeholder={Translate.string('Enter your search term')}
        onChange={handleChange}
        value={keyword}
      />
    </Form>
  );
}

SearchBox.propTypes = {
  onSearch: PropTypes.func.isRequired,
};
