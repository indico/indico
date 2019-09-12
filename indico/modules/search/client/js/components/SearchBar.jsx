import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Form} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

export default function SearchBar({onSearch, query}) {
  const [value, setValue] = useState(query);
  const handleChange = event => {
    setValue(event.target.value);
  };

  const handleSubmit = event => {
    event.preventDefault();
    onSearch(value, 'pushIn');
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
  query: PropTypes.string.isRequired,
};
