// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useImperativeHandle, useLayoutEffect, useRef, useState} from 'react';

import {Translate} from 'indico/react/i18n';

import DrillDownView from './DrillDownView';
import SearchResultsView from './SearchResultsView';
import useNavigatorState from './useNavigatorState';

import './category_navigator.scss';

/* global confirmPrompt */

export default function CategoryNavigator({
  category,
  dialogTitle,
  dialogSubtitle,
  actionButtonText,
  emptyCategoryText,
  actionOn,
  isNavigation,
  actionUrl,
  confirmation,
  onAction,
  onClose,
  inline,
  apiRef,
}) {
  const navigatorState = useNavigatorState(category);
  const {clearSearch, navigateTo, handleSearchChange} = navigatorState;
  const dialogRef = useRef(null);
  const searchInputRef = useRef(null);
  const [isConfirming, setIsConfirming] = useState(false);

  useImperativeHandle(
    apiRef,
    () => ({
      goToCategory: id => {
        clearSearch();
        navigateTo(id);
      },
      searchCategories: query => handleSearchChange(query),
    }),
    [clearSearch, navigateTo, handleSearchChange]
  );

  useLayoutEffect(() => {
    if (inline || isConfirming) {
      return undefined;
    }
    const dialog = dialogRef.current;
    const scrollLocked = [document.documentElement, document.body].filter(
      el => !el.classList.contains('prevent-scrolling')
    );
    scrollLocked.forEach(el => el.classList.add('prevent-scrolling'));
    dialog.showModal();
    dialog.focus();
    return () => {
      dialog.close();
      scrollLocked.forEach(el => el.classList.remove('prevent-scrolling'));
    };
  }, [inline, isConfirming]);

  // A control that removes itself (drilling, breadcrumbs, "navigate up") drops focus to the body
  useLayoutEffect(() => {
    const dialog = dialogRef.current;
    if (dialog?.open && document.activeElement === document.body) {
      dialog.focus();
    }
  });

  const handleAction = selectedCategory => {
    if (confirmation) {
      const text = Translate.string(
        'You selected category "{title}". Are you sure you want to proceed?',
        {title: selectedCategory.title}
      );
      dialogRef.current?.close();
      setIsConfirming(true);
      confirmPrompt(text, Translate.string('Confirm action')).then(
        async () => {
          try {
            await onAction(selectedCategory);
          } catch {
            setIsConfirming(false);
          }
        },
        () => setIsConfirming(false)
      );
    } else {
      Promise.resolve(onAction(selectedCategory)).catch(() => {});
    }
  };

  // Native modal dialogs let Tab move on to the browser UI; keep it cycling inside the navigator
  const handleKeyDown = evt => {
    if (evt.key !== 'Tab') {
      return;
    }
    const dialog = dialogRef.current;
    const focusable = [
      ...dialog.querySelectorAll('button, [href], input, summary, [tabindex]:not([tabindex="-1"])'),
    ].filter(el => !el.disabled && el.getClientRects().length);
    if (!focusable.length) {
      return;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (evt.shiftKey && (document.activeElement === first || document.activeElement === dialog)) {
      evt.preventDefault();
      last.focus();
    } else if (!evt.shiftKey && document.activeElement === last) {
      evt.preventDefault();
      first.focus();
    }
  };

  const handleKeyDownCapture = evt => {
    if (evt.key === 'Escape' && dialogRef.current?.querySelector('ind-with-tooltip[shown]')) {
      evt.preventDefault();
      evt.stopPropagation();
      onClose();
    }
  };

  const focusSearch = () => {
    searchInputRef.current?.focus();
  };

  const {
    currentCategory,
    isLoading,
    isLoadingSubcategories,
    isError,
    isSearchActive,
    isSearchLoading,
    searchResults,
  } = navigatorState;
  const isListLoading =
    isLoading ||
    (isSearchActive
      ? isSearchLoading && !searchResults
      : isLoadingSubcategories && !!currentCategory);

  const content = (
    <>
      <div className="search">
        <label>
          <span className="visually-hidden">
            <Translate>Search categories</Translate>
          </span>
          <input
            ref={searchInputRef}
            type="text"
            placeholder={Translate.string('Search')}
            value={navigatorState.searchQuery}
            onChange={e => handleSearchChange(e.target.value)}
          />
        </label>
        {navigatorState.searchQuery && (
          <ind-with-tooltip>
            <button
              type="button"
              value="clear-search"
              onClick={() => {
                clearSearch();
                focusSearch();
              }}
            >
              <span data-tip-content>
                <Translate>Clear search</Translate>
              </span>
            </button>
          </ind-with-tooltip>
        )}
      </div>

      <div className="main">
        <div className={isListLoading ? 'category-list loading' : 'category-list'}>
          {isLoading ? (
            <div className="spinner-wrapper">
              <div className="i-spinner" />
            </div>
          ) : isError && !currentCategory ? (
            <div className="placeholder">
              <div className="placeholder-text">
                <Translate>Failed to load category</Translate>
              </div>
            </div>
          ) : isSearchActive ? (
            <SearchResultsView
              navigatorState={navigatorState}
              actionButtonText={actionButtonText}
              isNavigation={isNavigation}
              actionUrl={actionUrl}
              actionOn={actionOn}
              onAction={handleAction}
              focusSearch={focusSearch}
            />
          ) : (
            <DrillDownView
              navigatorState={navigatorState}
              actionButtonText={actionButtonText}
              isNavigation={isNavigation}
              actionUrl={actionUrl}
              actionOn={actionOn}
              emptyCategoryText={emptyCategoryText}
              onAction={handleAction}
              focusSearch={focusSearch}
            />
          )}
        </div>
      </div>
    </>
  );

  if (inline) {
    return <div className="categorynav-inline categorynav">{content}</div>;
  }

  return (
    <dialog
      ref={dialogRef}
      id="category-navigator"
      className="categorynav-modal"
      aria-label={dialogTitle}
      onKeyDown={handleKeyDown}
      onKeyDownCapture={handleKeyDownCapture}
      onCancel={e => {
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }}
      onClick={e => {
        if (e.target === e.currentTarget) {
          const {left, right, top, bottom} = e.currentTarget.getBoundingClientRect();
          if (e.clientX < left || e.clientX > right || e.clientY < top || e.clientY > bottom) {
            onClose();
          }
        }
      }}
    >
      <div>
        <div className="titlebar">
          <div className="titlebar-heading">
            <h2>{dialogTitle}</h2>
            {dialogSubtitle && <div className="subtitle">{dialogSubtitle}</div>}
          </div>
          <ind-with-tooltip>
            <button type="button" className="close-button" onClick={onClose} value="close">
              <span data-tip-content>
                <Translate>Close category navigator</Translate>
              </span>
            </button>
          </ind-with-tooltip>
        </div>

        <div className="content categorynav">{content}</div>

        <div className="button-bar">
          <button type="button" className="close-bar-button" onClick={onClose}>
            <Translate>Close</Translate>
          </button>
        </div>
      </div>
    </dialog>
  );
}

CategoryNavigator.propTypes = {
  category: PropTypes.oneOfType([PropTypes.number, PropTypes.object]),
  dialogTitle: PropTypes.string,
  dialogSubtitle: PropTypes.string,
  actionButtonText: PropTypes.string,
  emptyCategoryText: PropTypes.string,
  actionOn: PropTypes.object,
  isNavigation: PropTypes.bool,
  actionUrl: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  confirmation: PropTypes.bool,
  onAction: PropTypes.func,
  onClose: PropTypes.func,
  inline: PropTypes.bool,
  apiRef: PropTypes.object,
};

CategoryNavigator.defaultProps = {
  category: 0,
  dialogTitle: 'Select a category',
  dialogSubtitle: null,
  actionButtonText: 'Select',
  emptyCategoryText: "This category doesn't contain any subcategory",
  actionOn: {},
  isNavigation: false,
  actionUrl: null,
  confirmation: false,
  onAction: () => {},
  onClose: () => {},
  inline: false,
  apiRef: null,
};
