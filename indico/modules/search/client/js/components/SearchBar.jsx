import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Form} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

export default function SearchBar({onSearch, searchTerm}) {
  const [value, setValue] = useState(searchTerm);

  const handleChange = event => {
    setValue(event.target.value);
  };

  const handleSubmit = event => {
    event.preventDefault();
    onSearch(value);
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Form.Input
        action={Translate.string('Search')}
        placeholder={Translate.string('Enter your search term')}
        value={value}
        onChange={handleChange}
      />
    </Form>
  );
}

SearchBar.propTypes = {
  onSearch: PropTypes.func.isRequired,
  searchTerm: PropTypes.string.isRequired,
};
