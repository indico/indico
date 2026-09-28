// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {useState, useEffect, useRef, useCallback} from 'react';

import {fetchCategoryInfo, fetchReachableCategories, searchCategories} from './api';

export default function useNavigatorState(initialCategory = 0) {
  const initialId =
    initialCategory && typeof initialCategory === 'object'
      ? initialCategory.category.id
      : initialCategory || 0;

  const [currentCategoryId, setCurrentCategoryId] = useState(initialId);
  const [categoryCache, setCategoryCache] = useState(() => {
    if (initialCategory && typeof initialCategory === 'object') {
      const cache = {[initialCategory.category.id]: initialCategory.category};
      (initialCategory.subcategories || []).forEach(sc => {
        cache[sc.id] = sc;
      });
      (initialCategory.supercategories || []).forEach(sc => {
        cache[sc.id] = sc;
      });
      return cache;
    }
    return {};
  });
  const [subcategoriesCache, setSubcategoriesCache] = useState(() => {
    if (initialCategory && typeof initialCategory === 'object') {
      return {
        [initialCategory.category.id]: (initialCategory.subcategories || []).map(sc => sc.id),
      };
    }
    return {};
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchLoading, setIsSearchLoading] = useState(false);
  const [isSearchError, setIsSearchError] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [isBrowsingFromSearch, setIsBrowsingFromSearch] = useState(false);

  const searchTimerRef = useRef(null);
  const latestQueryRef = useRef('');

  const fillCache = useCallback(data => {
    if (!data?.category) {
      return;
    }
    setCategoryCache(prev => {
      const next = {...prev, [data.category.id]: data.category};
      (data.subcategories || []).forEach(sc => {
        next[sc.id] = {...(next[sc.id] || {}), ...sc};
      });
      (data.supercategories || []).forEach(sc => {
        next[sc.id] = {...(next[sc.id] || {}), ...sc};
      });
      return next;
    });
    setSubcategoriesCache(prev => ({
      ...prev,
      [data.category.id]: (data.subcategories || []).map(sc => sc.id),
    }));
  }, []);

  const loadCategory = useCallback(
    async id => {
      setIsLoading(true);
      setIsError(false);
      try {
        const data = await fetchCategoryInfo(id);
        if (!data) {
          setIsError(true);
        } else {
          fillCache(data);
          fetchReachableCategories(id)
            .then(reachableData => {
              if (reachableData?.categories) {
                reachableData.categories.forEach(fillCache);
              }
            })
            .catch(() => {});
        }
      } catch {
        setIsError(true);
      } finally {
        setIsLoading(false);
      }
    },
    [fillCache]
  );

  useEffect(() => {
    if (subcategoriesCache[currentCategoryId] === undefined) {
      loadCategory(currentCategoryId);
    }
  }, [currentCategoryId, subcategoriesCache, loadCategory]);

  const navigateTo = useCallback(id => {
    setIsError(false);
    setCurrentCategoryId(id);
  }, []);

  const drillFromSearch = useCallback(id => {
    setIsError(false);
    setIsBrowsingFromSearch(true);
    setCurrentCategoryId(id);
  }, []);

  const returnToSearchResults = useCallback(() => {
    setIsBrowsingFromSearch(false);
  }, []);

  const clearSearch = useCallback(() => {
    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current);
    }
    latestQueryRef.current = '';
    setSearchQuery('');
    setSearchResults(null);
    setIsSearchLoading(false);
    setIsSearchError(false);
    setIsBrowsingFromSearch(false);
  }, []);

  const handleSearchChange = useCallback(query => {
    latestQueryRef.current = query;
    setSearchQuery(query);
    setIsBrowsingFromSearch(false);
    setIsSearchError(false);

    if (searchTimerRef.current) {
      clearTimeout(searchTimerRef.current);
    }

    if (query.trim().length < 3) {
      setSearchResults(null);
      setIsSearchLoading(false);
      return;
    }

    setIsSearchLoading(true);
    searchTimerRef.current = setTimeout(async () => {
      const isStale = () => latestQueryRef.current !== query;
      try {
        const data = await searchCategories(query.trim());
        if (isStale()) {
          return;
        }
        setSearchResults(data);
        if (data?.categories) {
          setCategoryCache(prev => {
            const next = {...prev};
            data.categories.forEach(cat => {
              next[cat.id] = {...(next[cat.id] || {}), ...cat};
            });
            return next;
          });
        }
      } catch {
        if (!isStale()) {
          setSearchResults(null);
          setIsSearchError(true);
        }
      } finally {
        if (!isStale()) {
          setIsSearchLoading(false);
        }
      }
    }, 400);
  }, []);

  const currentCategory = categoryCache[currentCategoryId] || null;
  const subcategoryIds = subcategoriesCache[currentCategoryId] || [];
  const subcategories = subcategoryIds.map(id => categoryCache[id]).filter(Boolean);

  const isSearchActive = searchQuery.trim().length >= 3 && !isBrowsingFromSearch;
  const isLoadingSubcategories = subcategoriesCache[currentCategoryId] === undefined && !isError;

  return {
    currentCategoryId,
    currentCategory,
    subcategories,
    isLoading: isLoading && !currentCategory,
    isLoadingSubcategories,
    isError,
    searchQuery,
    isSearchLoading,
    isSearchError,
    searchResults,
    isSearchActive,
    isBrowsingFromSearch,
    navigateTo,
    drillFromSearch,
    returnToSearchResults,
    clearSearch,
    handleSearchChange,
    reloadCurrent: () => loadCategory(currentCategoryId),
  };
}
