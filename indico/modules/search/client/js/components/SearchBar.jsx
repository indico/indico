import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Form, Input} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import './SearchBar.module.scss';

export default function SearchBar({onSearch}) {
  const [value, setValue] = useState('');
  const handleChange = event => {
    setValue(event.target.value);
  };

  const handleSubmit = event => {
    event.preventDefault();
    onSearch(value);
  };

  return (
    <div>
      <Form onSubmit={handleSubmit}>
        <Form.Group>
          <Input
            action={Translate.string('Search')}
            placeholder={Translate.string('Enter your search term')}
            value={value}
            onChange={handleChange}
            styleName="field"
          />
        </Form.Group>
      </Form>
    </div>
  );
}

SearchBar.propTypes = {
  onSearch: PropTypes.func.isRequired,
};
