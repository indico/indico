// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import data from '../../../data/data';

export default function ResultList({component: Component}) {
  return (
    <List divided relaxed>
      {data.map(item => (
        <List.Item key={item._id}>
          <List.Content>
            <Component {...item} />
          </List.Content>
        </List.Item>
      ))}
    </List>
  );
}

ResultList.propTypes = {
  component: PropTypes.elementType.isRequired,
};
