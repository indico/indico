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
        action={{icon: 'search', size: 'tiny'}}
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
