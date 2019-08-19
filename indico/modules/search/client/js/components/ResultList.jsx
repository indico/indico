// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {List} from 'semantic-ui-react';
import data from '../../../data/data';
// import myData from '../../../data/data'
export default function ResultList() {
  const list = data.map(item => (
    <List.Item key={item._id}>
      <List.Content>
        <List.Header as="a">{item.name.first}</List.Header>
        <List.Description as="a">{item.age}</List.Description>
      </List.Content>
    </List.Item>
  ));
  return (
    <List divided relaxed>
      {list}
    </List>
  );
}
