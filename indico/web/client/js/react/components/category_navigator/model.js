// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export class CategoryDataError extends Error {}

export class CategorySearchError extends Error {}

// Data objects

function createCategoryFromResponse(category) {
  return {
    id: category.id,
    title: category.title,
    canAccess: category.can_access,
    canCreateEvents: category.can_create_events,
    canManage: category.can_manage,
    canProposeEvents: category.can_propose_events,
    isProtected: category.is_protected,
    hasChildren: category.has_children,
    deepCategoryCount: category.deep_category_count,
    deepEventCount: category.deep_event_count,
    path: category.parent_path,
  };
}

// Category list

export function prepareForLoading(model) {
  return {...model, error: null};
}

export function resetCategoryList(model) {
  return {...model, category: null, subcategories: []};
}

export function updateModelFromResponse(category, subcategories) {
  return function(model) {
    category = createCategoryFromResponse(category);
    subcategories = subcategories.map(createCategoryFromResponse);

    return {
      ...model,
      category,
      subcategories,
    };
  };
}

export function updateModelFromError(model) {
  return {
    ...model,
    error: new CategoryDataError(),
  };
}

// Search results

export function prepareForSearch(keyword) {
  return function(model) {
    return {...model, error: null, searchKeyword: keyword};
  };
}

export function clearSearch(model) {
  return {...model, searchResults: null, searchKeyword: ''};
}

export function updateModelFromSearch(categories) {
  return function(model) {
    return {
      ...model,
      searchResults: categories.map(createCategoryFromResponse),
    };
  };
}

export function updateModelFromSearchError(model) {
  return {
    ...model,
    error: new CategorySearchError(),
  };
}

// Loading flag

export function startLoading(model) {
  return {...model, loading: true};
}

export function finishLoading(model) {
  return {...model, loading: false};
}

// Model

export function init() {
  return {
    category: null,
    searchKeyword: '',
    subcategories: [],
    searchResults: null,
    error: null,
    loading: false,
  };
}
