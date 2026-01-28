// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global build_url */

export function fetchCategoryInfo(id) {
  const url = build_url(Indico.Urls.Categories.info, {category_id: id});
  return fetch(url, {redirect: 'error'}).then(response => {
    // XXX: Re-enable error handling once we skip retrieving protected parents
    if (!response.ok && response.status !== 403) {
      throw new Error(`Failed to fetch category info: ${response.statusText}`);
    }

    if (!response.ok) {
      return null;
    }

    return response.json();
  });
}

export function fetchReachableCategories(id, exclude = []) {
  const url = build_url(Indico.Urls.Categories.infoFrom, {category_id: id});
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      exclude,
    }),
  }).then(response => {
    if (!response.ok) {
      throw new Error(`Failed to fetch reachable categories: ${response.statusText}`);
    }

    return response.json();
  });
}

export function searchCategories(query) {
  const url = build_url(Indico.Urls.Categories.search);
  const searchParams = new URLSearchParams({q: query});
  return fetch(`${url}?${searchParams}`).then(response => {
    if (!response.ok) {
      throw new Error(`Failed to search categories: ${response.statusText}`);
    }

    return response.json();
  });
}
