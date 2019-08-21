/* eslint-disable react/display-name */
// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Tab} from 'semantic-ui-react';
import ResultList from './ResultList';
import './SearchApp.module.scss';
import Category from './results/Category';
import Contribution from './results/Contribution';
import Event from './results/Event';
import File from './results/File';

const panes = [
  {
    menuItem: 'Category',
    render: () => (
      <Tab.Pane attached={false}>
        <ResultList component={Category} />
      </Tab.Pane>
    ),
  },
  {
    menuItem: 'Contribution',
    render: () => (
      <Tab.Pane attached={false}>
        <ResultList component={Contribution} />
      </Tab.Pane>
    ),
  },
  {
    menuItem: 'Event',
    render: () => (
      <Tab.Pane attached={false}>
        <ResultList component={Event} />
      </Tab.Pane>
    ),
  },
  {
    menuItem: 'File',
    render: () => (
      <Tab.Pane attached={false}>
        <ResultList component={File} />
      </Tab.Pane>
    ),
  },
];

export default function SearchApp() {
  return <Tab menu={{secondary: true, pointing: true}} panes={panes} />;
}
