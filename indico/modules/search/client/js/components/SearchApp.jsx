/* eslint-disable react/display-name */
// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {Menu} from 'semantic-ui-react';

import ResultList from './ResultList';
import SearchBar from './SearchBar';
import Category from './results/Category';
import Contribution from './results/Contribution';
import Event from './results/Event';
import File from './results/File';

import './SearchApp.module.scss';

import data1 from '../../../data/category_data';
import data2 from '../../../data/contribution_data';
import data3 from '../../../data/event_data';
import data4 from '../../../data/file_data';

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

export default function SearchApp() {
  const [activeMenuItem, setActiveMenuItem] = useState('Category');
  const [allData, setAllData] = useState(datasetSelector(activeMenuItem));
  const handleClick = (e, {name}) => {
    setActiveMenuItem(name);
    setAllData(datasetSelector(name));
  };

  return (
    <div>
      <SearchBar />
      <Menu pointing secondary>
        <Menu.Item name="Category" active={activeMenuItem === 'Category'} onClick={handleClick} />
        <Menu.Item
          name="Contribution"
          active={activeMenuItem === 'Contribution'}
          onClick={handleClick}
        />
        <Menu.Item name="Event" active={activeMenuItem === 'Event'} onClick={handleClick} />
        <Menu.Item name="File" active={activeMenuItem === 'File'} onClick={handleClick} />
      </Menu>

      {activeMenuItem === 'Category' && <ResultList component={Category} allData={allData} />}
      {activeMenuItem === 'Contribution' && (
        <ResultList component={Contribution} allData={allData} />
      )}
      {activeMenuItem === 'Event' && <ResultList component={Event} allData={allData} />}
      {activeMenuItem === 'File' && <ResultList component={File} allData={allData} />}
    </div>
  );
}
