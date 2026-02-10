// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';

import Breadcrumbs from './Breadcrumbs';
import {getCategoryActionState} from './categoryActionUtils';
import CategoryStats from './CategoryStats';
import {useCategoryNavigator} from './context';
import ProtectionStatus from './ProtectionStatus';

function highlightMatch(text, query) {
  const index = text.toLowerCase().indexOf(query.toLowerCase());
  if (index === -1) {
    return <span>{text}</span>;
  }

  const before = text.substring(0, index);
  const match = text.substring(index, index + query.length);
  const after = text.substring(index + query.length);

  return (
    <>
      <span>{before}</span>
      <mark>{match}</mark>
      <span>{after}</span>
    </>
  );
}

function SearchResultItem({category}) {
  const {options, onCategoryAction, navigatorState} = useCategoryNavigator();

  const resultType = category.is_favorite ? 'favorite' : 'regular';
  const actionState = getCategoryActionState(category, options.shouldDisableAction);

  const actionButton = (
    <button
      type="button"
      onClick={() => onCategoryAction(category)}
      disabled={actionState.disabled}
      className="category-action"
    >
      {options.actionButtonText}
    </button>
  );

  return (
    <li className="search-result">
      <div className="result-type-indicator" data-result-type={resultType}>
        {resultType === 'favorite' ? (
          <Translate as="span">In favorite categories</Translate>
        ) : (
          <Translate as="span">Search result</Translate>
        )}
      </div>

      <ProtectionStatus category={category} />

      <div className="title-wrapper">
        <span className="title">{highlightMatch(category.title, navigatorState.searchQuery)}</span>
        <Breadcrumbs path={category.parent_path} />
      </div>

      <div>
        {actionState.disabled && actionState.message ? (
          <ind-with-tooltip>
            {actionButton}
            <span data-tip-content>{actionState.message}</span>
          </ind-with-tooltip>
        ) : (
          actionButton
        )}
      </div>
      <CategoryStats category={category} />
    </li>
  );
}

SearchResultItem.propTypes = {
  category: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    is_favorite: PropTypes.bool,
    is_protected: PropTypes.bool,
    parent_path: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.number.isRequired,
        title: PropTypes.string.isRequired,
      })
    ),
    deep_category_count: PropTypes.number,
    deep_event_count: PropTypes.number,
  }).isRequired,
};

export default function SearchResultsView() {
  const {navigatorState} = useCategoryNavigator();
  const {searchResults: results, searchQuery: query, hasSearchResults: hasResults} = navigatorState;

  return (
    <>
      {hasResults && (
        <div className="search-result-info">
          <span className="result-stats">
            <PluralTranslate count={results.categories.length}>
              <Singular>
                Displaying 1 result out of <Param name="total" value={results.total_count} />.
              </Singular>
              <Plural>
                Displaying <Param name="count" value={results.categories.length} /> results out of{' '}
                <Param name="total" value={results.total_count} />.
              </Plural>
            </PluralTranslate>
          </span>
          <button
            type="button"
            className="clear"
            value="clear-search"
            onClick={() => navigatorState.clearSearch()}
          >
            <Translate>Clear search</Translate>
          </button>
        </div>
      )}

      {hasResults && (
        <ul className="search-result-list">
          {results.categories.map(category => (
            <SearchResultItem key={category.id} category={category} query={query} />
          ))}
        </ul>
      )}

      {!hasResults && (
        <div className="placeholder">
          <div className="placeholder-text">
            <Translate>Your search doesn't match any category</Translate>
          </div>
          <div>
            <Translate>
              <button type="button">modify</button> or <button type="button">clear</button> your
              search.
            </Translate>
          </div>
        </div>
      )}
    </>
  );
}
