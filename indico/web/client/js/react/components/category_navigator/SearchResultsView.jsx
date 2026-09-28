// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';

import CategoryActionElement from './CategoryActionElement';
import {canActOnCategory} from './categoryActionUtils';
import CategoryStats from './CategoryStats';

function highlightMatch(text, query) {
  if (!query) {
    return text;
  }
  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase();
  const index = lowerText.indexOf(lowerQuery);
  if (index === -1) {
    return text;
  }
  const before = text.substring(0, index);
  const match = text.substring(index, index + query.length);
  const after = text.substring(index + query.length);
  return (
    <>
      {before}
      <strong>{match}</strong>
      {after}
    </>
  );
}

export default function SearchResultsView({
  navigatorState,
  actionButtonText,
  isNavigation,
  actionUrl,
  actionOn,
  onAction,
  focusSearch,
}) {
  const {searchResults, searchQuery, isSearchLoading, isSearchError, drillFromSearch, clearSearch} =
    navigatorState;

  const clearAndFocus = () => {
    clearSearch();
    focusSearch();
  };

  if (isSearchLoading && !searchResults) {
    return (
      <div className="spinner-wrapper">
        <div className="i-spinner" />
      </div>
    );
  }

  if (isSearchError) {
    return null;
  }

  const categories = searchResults?.categories || [];
  const totalCount = searchResults?.total_count || 0;
  const count = categories.length;

  if (count === 0 && !isSearchLoading) {
    return (
      <div className="placeholder">
        <div className="placeholder-text">
          <Translate>Your search doesn't match any category</Translate>
        </div>
        <div className="placeholder-actions">
          <Translate>
            You can{' '}
            <Param
              name="modify"
              wrapper={<button type="button" className="link-style" onClick={focusSearch} />}
            >
              modify
            </Param>{' '}
            or{' '}
            <Param
              name="clear"
              wrapper={<button type="button" className="link-style" onClick={clearAndFocus} />}
            >
              clear
            </Param>{' '}
            your search.
          </Translate>
        </div>
      </div>
    );
  }

  return (
    <div className="search-results-view">
      <div className="search-result-info">
        <span className="result-stats">
          <PluralTranslate count={count}>
            <Singular>
              Displaying 1 result out of <Param name="total" value={totalCount} />.
            </Singular>
            <Plural>
              Displaying <Param name="count" value={count} /> results out of{' '}
              <Param name="total" value={totalCount} />.
            </Plural>
          </PluralTranslate>
          {totalCount > count && (
            <span>
              {' '}
              <Translate>Make the search more specific for more accurate results</Translate>
            </span>
          )}
        </span>
        <button type="button" className="clear js-clear-search" onClick={clearAndFocus}>
          <Translate>Clear search</Translate>
        </button>
      </div>

      <ul className="group-list search-result-list search-results-list">
        {categories.map(category => {
          const actionState = canActOnCategory(category, actionOn);
          const parentPath = category.parent_path || [];

          return (
            <li key={category.id} className="item subcategory search-result">
              <div className="result-info-area">
                <div className="icon-wrapper">
                  {category.is_favorite ? (
                    <i className="icon-star favorite-icon">
                      <span className="visually-hidden">
                        <Translate>In favorite categories</Translate>
                      </span>
                    </i>
                  ) : (
                    <i className="icon-search search-icon" aria-hidden="true" />
                  )}
                </div>

                <div className="title-area title-wrapper">
                  <button
                    type="button"
                    className="category-drill-button js-go-to"
                    onClick={() => drillFromSearch(category.id)}
                    disabled={!category.can_access}
                  >
                    {category.is_protected && (
                      <span className="protection icon-shield">
                        <span className="visually-hidden">
                          <Translate>This category is protected</Translate>{' '}
                        </span>
                      </span>
                    )}
                    <span className="title">{highlightMatch(category.title, searchQuery)}</span>
                    <span className="icon-folder" aria-hidden="true" />
                  </button>

                  {parentPath.length > 0 && (
                    <div className="breadcrumbs">
                      <ul>
                        {parentPath.map((parent, idx) => (
                          <li key={parent.id}>
                            {idx === 0 && (
                              <span className="path-prefix">{Translate.string('in')}&nbsp;</span>
                            )}
                            <ind-with-tooltip>
                              <button
                                type="button"
                                className="breadcrumb-button"
                                onClick={() => drillFromSearch(parent.id)}
                              >
                                {parent.title}
                                <span data-tip-content>
                                  <Translate>Go to category</Translate>
                                </span>
                              </button>
                            </ind-with-tooltip>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              <div className="side-panel">
                <CategoryStats category={category} />
                <CategoryActionElement
                  category={category}
                  actionButtonText={actionButtonText}
                  isNavigation={isNavigation}
                  actionUrl={actionUrl}
                  disabled={!actionState.allowed}
                  disabledMessage={actionState.message}
                  onAction={onAction}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

SearchResultsView.propTypes = {
  navigatorState: PropTypes.object.isRequired,
  actionButtonText: PropTypes.string.isRequired,
  isNavigation: PropTypes.bool.isRequired,
  actionUrl: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  actionOn: PropTypes.object.isRequired,
  onAction: PropTypes.func.isRequired,
  focusSearch: PropTypes.func.isRequired,
};

SearchResultsView.defaultProps = {
  actionUrl: null,
};
