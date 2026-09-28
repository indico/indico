// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {act, renderHook} from '@testing-library/react-hooks';

import {fetchCategoryInfo, fetchReachableCategories, searchCategories} from '../api';
import useNavigatorState from '../useNavigatorState';

jest.mock('../api');

it('opens the root when an unlisted event supplies no starting category', async () => {
  const root = {id: 0, title: 'Root', parent_path: []};
  fetchCategoryInfo.mockResolvedValue({category: root, subcategories: []});
  fetchReachableCategories.mockResolvedValue({categories: []});

  const {result, waitFor} = renderHook(() => useNavigatorState(null));

  await waitFor(() => expect(result.current.currentCategory).toEqual(root));
  expect(fetchCategoryInfo).toHaveBeenCalledWith(0);
});

it('reports the children of the current category as loading until they arrive', async () => {
  let resolveChild;
  const root = {id: 0, title: 'Root', parent_path: []};
  const child = {id: 1, title: 'Child', parent_path: [{id: 0, title: 'Root'}]};
  fetchCategoryInfo.mockImplementation(id =>
    id === 0
      ? Promise.resolve({category: root, subcategories: [child]})
      : new Promise(resolve => {
          resolveChild = resolve;
        })
  );
  fetchReachableCategories.mockResolvedValue({categories: []});

  const {result, waitFor} = renderHook(() => useNavigatorState(0));
  await waitFor(() => expect(result.current.isLoadingSubcategories).toBe(false));

  act(() => result.current.navigateTo(1));
  expect(result.current.currentCategory).toEqual(child);
  expect(result.current.isLoadingSubcategories).toBe(true);

  await act(async () => resolveChild({category: child, subcategories: []}));
  expect(result.current.isLoadingSubcategories).toBe(false);
});

it('reports an error instead of an empty category when access is denied', async () => {
  const root = {id: 0, title: 'Root', parent_path: []};
  fetchCategoryInfo.mockImplementation(id =>
    Promise.resolve(id === 0 ? {category: root, subcategories: []} : null)
  );
  fetchReachableCategories.mockResolvedValue({categories: []});

  const {result, waitFor} = renderHook(() => useNavigatorState(0));
  await waitFor(() => expect(result.current.currentCategory).toEqual(root));

  act(() => result.current.navigateTo(5));
  await waitFor(() => expect(result.current.isError).toBe(true));
  expect(result.current.isLoadingSubcategories).toBe(false);

  act(() => result.current.navigateTo(0));
  expect(result.current.isError).toBe(false);
});

it('ignores search results that arrive after a newer query', async () => {
  jest.useFakeTimers();
  const resolvers = new Map();
  fetchCategoryInfo.mockResolvedValue({category: {id: 0, title: 'Root'}, subcategories: []});
  fetchReachableCategories.mockResolvedValue({categories: []});
  searchCategories.mockImplementation(
    query =>
      new Promise(resolve => {
        resolvers.set(query, resolve);
      })
  );

  const {result} = renderHook(() => useNavigatorState(0));
  act(() => result.current.handleSearchChange('Navi'));
  act(() => jest.advanceTimersByTime(400));
  act(() => result.current.handleSearchChange('Navigator dest'));
  act(() => jest.advanceTimersByTime(400));

  await act(async () => resolvers.get('Navigator dest')({categories: [{id: 6}], total_count: 1}));
  await act(async () => resolvers.get('Navi')({categories: [{id: 1}, {id: 2}], total_count: 2}));

  expect(result.current.searchResults.categories).toEqual([{id: 6}]);
  expect(result.current.isSearchLoading).toBe(false);
  jest.useRealTimers();
});

it('distinguishes a failed search from a search with no matches', async () => {
  jest.useFakeTimers();
  fetchCategoryInfo.mockResolvedValue({category: {id: 0, title: 'Root'}, subcategories: []});
  fetchReachableCategories.mockResolvedValue({categories: []});
  searchCategories.mockRejectedValue(new Error('Search failed'));

  const {result} = renderHook(() => useNavigatorState(0));
  act(() => result.current.handleSearchChange('Navigator'));
  await act(async () => {
    jest.advanceTimersByTime(400);
  });

  expect(result.current.isSearchError).toBe(true);
  expect(result.current.searchResults).toBeNull();
  expect(result.current.isSearchLoading).toBe(false);

  act(() => result.current.handleSearchChange('Another query'));
  expect(result.current.isSearchError).toBe(false);
  jest.useRealTimers();
});
