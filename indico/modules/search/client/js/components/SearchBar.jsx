import React, {useState} from 'react';
import {Form, Input} from 'semantic-ui-react';
import './SearchBar.module.scss';

export default function SearchBar() {
  const [value, setValue] = useState('');
  const handleChange = event => {
    setValue(event.target.value);
  };

  const handleSubmit = event => {
    alert(`${value} was submitted`);
    event.preventDefault();
  };

  return (
    <div>
      <Form onSubmit={handleSubmit}>
        <Form.Group>
          <Input
            action="Search"
            placeholder="Search..."
            value={value}
            onChange={handleChange}
            styleName="field"
          />
        </Form.Group>
      </Form>
    </div>
  );
}
