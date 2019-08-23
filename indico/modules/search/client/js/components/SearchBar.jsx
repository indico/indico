import React, {useState} from 'react';
import {Form} from 'semantic-ui-react';
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
    <Form onSubmit={handleSubmit} size="tiny">
      <Form.Group>
        <Form.Input
          styleName="field"
          icon="search"
          placeholder="Search..."
          value={value}
          onChange={handleChange}
        />
        <Form.Button content="Submit" size="tiny" />
      </Form.Group>
      {/* <Grid>
        <Grid.Column textAlign="center">
          <Form.Button content="Submit" size="tiny" />
        </Grid.Column>
      </Grid> */}
    </Form>
  );
}
