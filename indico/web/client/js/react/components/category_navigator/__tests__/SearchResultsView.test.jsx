// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {mount} from 'enzyme';
import React from 'react';

import SearchResultsView from '../SearchResultsView';

it('shows no-match guidance only when a search succeeded with zero results', () => {
  const navigatorState = {
    searchQuery: 'Navigator',
    isSearchLoading: false,
    isSearchError: false,
    searchResults: {categories: [], total_count: 0},
    clearSearch: jest.fn(),
  };
  const props = {
    navigatorState,
    actionButtonText: 'Select',
    isNavigation: false,
    actionOn: {},
    onAction: jest.fn(),
    focusSearch: jest.fn(),
  };

  const emptyResults = mount(<SearchResultsView {...props} />);
  expect(emptyResults.text()).toContain("Your search doesn't match any category");

  const failedSearch = mount(
    <SearchResultsView
      {...props}
      navigatorState={{...navigatorState, isSearchError: true, searchResults: null}}
    />
  );
  expect(failedSearch.text()).not.toContain("Your search doesn't match any category");
});
