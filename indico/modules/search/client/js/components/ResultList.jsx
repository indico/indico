// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {List} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import './ResultList.module.scss';
import data1 from '../../../data/category_data';
import data2 from '../../../data/contribution_data';
import data3 from '../../../data/event_data';
import data4 from '../../../data/file_data';
import SearchPagination from './SearchPagination';

const datasetSelector = filter => {
  if (filter === 'Category') {
    return data1;
  } else if (filter === 'Contribution') {
    return data2;
  } else if (filter === 'Event') {
    return data3;
  } else if (filter === 'File') {
    return data4;
  } else return [];
};

export default function ResultList({component: Component}) {
  const data = datasetSelector(Component.name);
  return (
    <SearchPagination data={data}>
      {items => (
        <List divided relaxed>
          {items.map(item => (
            <List.Item key={item.url}>
              <List.Content styleName="list">
                <Component {...item} />
              </List.Content>
            </List.Item>
          ))}
        </List>
      )}
    </SearchPagination>
  );
}

ResultList.propTypes = {
  component: PropTypes.elementType.isRequired,
};

// for some reason it doesn't render the items again and have the latest value still there
// also fix the descriptions in events and files to be more user friendly
