// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState, useEffect, useRef} from 'react';

import {Translate} from 'indico/react/i18n';
import {$T} from 'indico/utils/i18n';

import {getCategoryActionState} from './categoryActionUtils';
import CategoryNavigatorContext from './context';
import DrillDownView from './DrillDownView';
import LoadErrorView from './LoadErrorView';
import SearchResultsView from './SearchResultsView';
import useNavigatorState from './useNavigatorState';

import './category_navigator.scss';

const DEFAULT_OPTIONS = {
  actionButtonText: $T.gettext('Select'),
  emptyCategoryText: $T.gettext("This category doesn't contain any subcategory"),
  onAction: () => {},
};

export default function CategoryNavigator() {
  const [options, setOptions] = useState(null);
  const dialogRef = useRef();

  const navigatorState = useNavigatorState(options?.category ?? 0);

  useEffect(() => {
    const handleShowNavigator = evt => {
      console.log('[CategoryNavigator] showcategorynavigator event received:', evt.detail);
      setOptions({...DEFAULT_OPTIONS, ...evt.detail});
    };

    console.log('[CategoryNavigator] Adding showcategorynavigator event listener');
    window.addEventListener('showcategorynavigator', handleShowNavigator);

    return () => {
      console.log('[CategoryNavigator] Removing showcategorynavigator event listener');
      window.removeEventListener('showcategorynavigator', handleShowNavigator);
    };
  }, []);

  useEffect(() => {
    if (!dialogRef.current) {
      console.log('[CategoryNavigator] Dialog ref not available yet');
      return;
    }

    if (options) {
      console.log('[CategoryNavigator] Showing dialog with options:', options);
      dialogRef.current.showModal();
    } else {
      console.log('[CategoryNavigator] Closing dialog');
      dialogRef.current.close();
    }
  }, [options]);

  const handleClose = () => {
    navigatorState.clearSearch();
    setOptions(null);
  };

  if (!options) {
    return null;
  }

  const handleCategoryAction = category => {
    // Check if action should be disabled before calling callback
    const actionState = getCategoryActionState(category, options.shouldDisableAction);
    if (actionState.disabled) {
      return;
    }
    options.onAction(category);
  };

  const handleClearSearch = evt => {
    navigatorState.clearSearch();
    evt.target.parentNode.querySelector('input').focus();
  };

  const contextValue = {
    options,
    navigatorState,

    onClose: handleClose,
    onCategoryAction: handleCategoryAction,
  };

  return (
    <CategoryNavigatorContext.Provider value={contextValue}>
      <dialog id="category-navigator" ref={dialogRef} aria-labelledby="categorynav-title">
        <div>
          <div className="titlebar">
            <h2 id="categorynav-title">
              <span>{options.dialogTitle}</span>
              {options.dialogSubtitle && <span className="subtitle">{options.dialogSubtitle}</span>}
            </h2>
            <button type="button" onClick={handleClose} value="close">
              <Translate as="span">Close</Translate>
            </button>
          </div>

          <div className="content">
            <div className="search">
              <label>
                <Translate as="span">Search categories</Translate>
                <input
                  type="text"
                  placeholder="Search"
                  value={navigatorState.searchQuery}
                  onChange={e => navigatorState.setSearchQuery(e.target.value)}
                />
              </label>
              <button
                type="button"
                onClick={handleClearSearch}
                hidden={!navigatorState.searchQuery}
                value="clear-search"
              >
                <Translate as="span">Clear search</Translate>
              </button>
            </div>

            <div className="main">
              {(() => {
                switch (navigatorState.viewState) {
                  case 'loading':
                    return (
                      <div className="loading">
                        <div className="i-spinner" />
                      </div>
                    );
                  case 'error':
                    return <LoadErrorView />;
                  case 'searching':
                    return <SearchResultsView />;
                  default:
                    return <DrillDownView />;
                }
              })()}
            </div>
          </div>

          <div className="button-bar">
            <button type="button" onClick={handleClose}>
              <Translate>Close</Translate>
            </button>
          </div>
        </div>
      </dialog>
    </CategoryNavigatorContext.Provider>
  );
}
