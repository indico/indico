// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useEffect, useRef, useState} from 'react';
import ReactDOM from 'react-dom';

import {getCategoryData, getCategorySearchResults} from './api';
import * as model from './model';

const loadingSpinnerDelay = 1500;

export function DialogViewModel({trigger, categoryId, view: View, actionView, dialogTitle}) {
  const [state, setState] = useState(model.init());
  const dialogRef = useRef();
  const searchFieldRef = useRef();

  useEffect(() => {
    trigger.addEventListener('click', openDialog);
    // eslint-disable-next-line
  }, []);

  function openDialog() {
    setState(model.resetCategoryList);
    loadCategoryData(categoryId);
    dialogRef.current.showModal();
  }

  function changeCategory(nextCategoryId) {
    if (state.searchResults) {
      // NB: Prevent stale category list from showing briefly before loading the target from the search results
      setState(model.resetCategoryList);
    }
    loadCategoryData(nextCategoryId);
  }

  function withLoading(prepare, request) {
    setState(prepare);

    // NB: Only show the loading state for slow responses
    const longLoadTimer = setTimeout(() => setState(model.startLoading), loadingSpinnerDelay);

    function end() {
      clearTimeout(longLoadTimer);
      setState(model.finishLoading);
    }

    return request.then(
      response => {
        end();
        if (response.data.success) {
          return response;
        } else {
          return Promise.reject(response);
        }
      },
      error => {
        end();
        return Promise.reject(error);
      }
    );
  }

  function clearSearch() {
    setState(model.clearSearch);
  }

  function loadCategoryData(nextCategoryId) {
    clearSearch();
    if (searchFieldRef.current) {
      searchFieldRef.current.value = '';
    }
    withLoading(model.prepareForLoading, getCategoryData(nextCategoryId)).then(
      response => {
        setState(
          model.updateModelFromResponse(response.data.category, response.data.subcategories)
        );
      },
      () => {
        setState(model.updateModelFromError);
      }
    );
  }

  function searchCategories(keyword) {
    keyword = keyword.trim().toLowerCase();

    if (!keyword) {
      clearSearch();
      return;
    }

    withLoading(
      model.prepareForSearch(keyword),
      getCategorySearchResults(categoryId, keyword.trim().toLowerCase())
    ).then(
      response => {
        setState(model.updateModelFromSearch(response.data.categories));
      },
      () => {
        setState(model.updateModelFromSearchError);
      }
    );
  }

  return ReactDOM.createPortal(
    <View
      {...state}
      dialogTitle={dialogTitle}
      dialogRef={dialogRef}
      searchFieldRef={searchFieldRef}
      onChangeCategory={changeCategory}
      onSearch={searchCategories}
      onCancelSearch={clearSearch}
      actionView={actionView}
    />,
    document.body
  );
}

DialogViewModel.propTypes = {
  trigger: PropTypes.object.isRequired,
  categoryId: PropTypes.string.isRequired,
  view: PropTypes.elementType.isRequired,
  actionView: PropTypes.elementType,
  dialogTitle: PropTypes.string,
};
