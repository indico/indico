// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {useState, useRef, useEffect, useCallback} from 'react';

import {fetchCategoryInfo, searchCategories} from './api';

export default function useNavigatorState(initialCategoryId) {
  const [searchQuery, setSearchQueryState] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [currentCategory, setCurrentCategory] = useState(null);
  const [subcategories, setSubcategories] = useState([]);
  const [isLoadingCategory, setIsLoadingCategory] = useState(false);
  const [isLoadingFailed, setIsLoadingFailed] = useState(false);
  const searchTimerRef = useRef(null);

  const loadCategory = useCallback(categoryId => {
    if (categoryId === null || categoryId === undefined) {
      return;
    }

    setIsLoadingCategory(true);
    setIsLoadingFailed(false);
    fetchCategoryInfo(categoryId)
      .then(data => {
        if (data) {
          setCurrentCategory(data.category);
          setSubcategories(data.subcategories || []);
        }
      })
      .catch(error => {
        setIsLoadingFailed(true);
        setCurrentCategory(null);
        setSubcategories([]);
        console.error('Failed to fetch category:', error);
      })
      .finally(() => {
        setIsLoadingCategory(false);
      });
  }, []);

  useEffect(() => {
    loadCategory(initialCategoryId);
  }, [initialCategoryId, loadCategory]);

  const setSearchQuery = query => {
    setSearchQueryState(query);

    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current);
    }

    if (query.length >= 3) {
      setIsSearching(true);
      setIsLoadingFailed(false);
      searchTimerRef.current = setTimeout(() => {
        searchCategories(query)
          .then(data => {
            setSearchResults(data);
          })
          .catch(error => {
            console.error('Search failed:', error);
            setSearchResults(null);
          })
          .finally(() => {
            setIsSearching(false);
          });
      }, 500);
    } else {
      setSearchResults(null);
      setIsSearching(false);
    }
  };

  const clearSearch = () => {
    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current);
    }
    setSearchQueryState('');
    setSearchResults(null);
    setIsSearching(false);
  };

  const hasSearchResults = searchQuery.length >= 3;

  // Compute view state from current state
  let viewState = 'loaded';
  if (isLoadingCategory || isSearching) {
    viewState = 'loading';
  } else if (isLoadingFailed) {
    viewState = 'error';
  } else if (hasSearchResults) {
    viewState = 'searching';
  }

  const navigateTo = categoryId => {
    clearSearch();
    loadCategory(categoryId);
  };

  return {
    // Data
    currentCategory,
    currentCategoryId: currentCategory?.id,
    searchQuery,
    searchResults,
    subcategories,
    viewState,

    // Flags
    hasSearchResults,
    isLoadingCategory,
    isLoadingFailed,
    isSearching,

    // Actions
    clearSearch,
    navigateTo,
    setSearchQuery,
  };
}
