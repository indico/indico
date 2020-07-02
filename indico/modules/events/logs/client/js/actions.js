// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import qs from 'qs';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

export const SET_KEYWORD = 'SET_KEYWORD';
export const SET_FILTER = 'SET_FILTER';
export const SET_PAGE = 'SET_PAGE';
export const UPDATE_ENTRIES = 'UPDATE_ENTRIES';
export const FETCH_STARTED = 'FETCH_STARTED';
export const FETCH_FAILED = 'FETCH_FAILED';
export const SET_DETAILED_VIEW = 'SET_DETAILED_VIEW';
export const VIEW_PREV_ENTRY = 'VIEW_PREV_ENTRY';
export const VIEW_NEXT_ENTRY = 'VIEW_NEXT_ENTRY';
export const SET_METADATA_QUERY = 'SET_METADATA_QUERY';

export function setKeyword(keyword) {
  return {type: SET_KEYWORD, keyword};
}

export function setFilter(filter) {
  return {type: SET_FILTER, filter};
}

export function setPage(currentPage) {
  return {type: SET_PAGE, currentPage};
}

export function setDetailedView(entryIndex) {
  return {type: SET_DETAILED_VIEW, currentViewIndex: entryIndex};
}

export function setMetadataQuery(metadataQuery) {
  return {type: SET_METADATA_QUERY, metadataQuery};
}

export function clearMetadataQuery() {
  return dispatch => {
    dispatch(setMetadataQuery({}));
    dispatch(setPage(1));
    dispatch(setDetailedView(null));
    dispatch(fetchLogEntries());
    history.replaceState({}, null, location.pathname);
  };
}

export function showRelatedEntries() {
  return (dispatch, getStore) => {
    const {
      logs: {entries, currentViewIndex},
    } = getStore();

    const entry = entries[currentViewIndex];
    const queryString = qs.stringify({meta: entry.meta}, {allowDots: true});
    dispatch(setMetadataQuery(entry.meta));
    dispatch(setPage(1));
    dispatch(setDetailedView(null));
    dispatch(fetchLogEntries());
    history.replaceState({}, null, `${location.pathname}?${queryString}`);
  };
}

export function viewPrevEntry() {
  return async (dispatch, getStore) => {
    const {
      staticData: {pageSize},
      logs: {currentViewIndex, currentPage},
    } = getStore();

    if (currentViewIndex === 0) {
      if (currentPage === 0) {
        // ERROR!
      } else {
        await dispatch(setPage(currentPage - 1));
        await dispatch(fetchLogEntries());
        await dispatch(setDetailedView(pageSize - 1));
      }
    } else {
      dispatch({type: SET_DETAILED_VIEW, currentViewIndex: currentViewIndex - 1});
    }
  };
}

export function viewNextEntry() {
  return async (dispatch, getStore) => {
    const {
      staticData: {pageSize},
      logs: {currentViewIndex, currentPage, pages},
    } = getStore();

    if (currentViewIndex === pageSize - 1) {
      if (currentPage === pages[pages.length - 1]) {
        // ERROR!
      } else {
        await dispatch(setPage(currentPage + 1));
        await dispatch(setDetailedView(0));
        await dispatch(fetchLogEntries());
      }
    } else {
      dispatch({type: SET_DETAILED_VIEW, currentViewIndex: currentViewIndex + 1});
    }
  };
}

export function updateEntries(entries, pages, totalPageCount) {
  return {type: UPDATE_ENTRIES, entries, pages, totalPageCount};
}

export function fetchStarted() {
  return {type: FETCH_STARTED};
}

export function fetchFailed() {
  return {type: FETCH_FAILED};
}

export function fetchLogEntries() {
  return async (dispatch, getStore) => {
    dispatch(fetchStarted());
    const {
      logs: {filters, keyword, currentPage, metadataQuery},
      staticData: {fetchLogsUrl},
    } = getStore();

    const params = {
      page: currentPage,
      filters: [],
      data: JSON.stringify(metadataQuery),
    };
    if (keyword) {
      params.q = keyword;
    }

    Object.entries(filters).forEach(([item, active]) => {
      if (active) {
        params.filters.push(item);
      }
    });

    let response;
    try {
      response = await indicoAxios.get(fetchLogsUrl, {params});
    } catch (error) {
      handleAxiosError(error);
      dispatch(fetchFailed());
      return;
    }
    const {entries, pages, total_page_count: totalPageCount} = response.data;
    dispatch(updateEntries(entries, pages, totalPageCount));
  };
}
