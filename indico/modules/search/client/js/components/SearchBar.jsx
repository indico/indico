import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Form} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

export default function SearchBar({onSearch}) {
  const [value, setValue] = useState(
    window.location.search === '' ? '' : window.location.search.slice(3)
  );
  const handleChange = event => {
    setValue(event.target.value);
  };

  const handleSubmit = event => {
    event.preventDefault();
    window.history.pushState('', '', `?q=${value}`);
    onSearch(value);
  };

  return (
    <Form onSubmit={handleSubmit}>
      <Form.Input
        action={Translate.string('Search')}
        placeholder={Translate.string('Enter your search term')}
        value={value}
        onChange={handleChange}
        // styleName="field"
      />
    </Form>
  );
}

SearchBar.propTypes = {
  onSearch: PropTypes.func.isRequired,
};
