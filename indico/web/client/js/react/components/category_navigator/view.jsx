// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import Dialog from 'indico/react/components/Dialog';
import {Translate, PluralTranslate, Param} from 'indico/react/i18n';
import 'indico/custom_elements/ind_with_tooltip';
import 'indico/custom_elements/ind_with_toggletip';

import './style.scss';

const debounceTimer = Symbol('debounceTimer');
const debounceTimeout = 500;

function LoadingView({loading, children}) {
  return (
    <div className="category-list-container">
      <p className="categories-loading" aria-live="polite">
        {loading ? <Translate as="span">Please wait.</Translate> : null}
      </p>
      {loading ? null : children}
    </div>
  );
}

LoadingView.propTypes = {
  loading: PropTypes.bool,
  children: PropTypes.oneOfType([PropTypes.element, PropTypes.arrayOf(PropTypes.element)]),
};

function ErrorView({error}) {
  return (
    <p className="category-load-error" role="alert">
      {error ? <Translate>Categories could not be loaded.</Translate> : null}
    </p>
  );
}

ErrorView.propTypes = {
  error: PropTypes.object,
};

function CategorySearchView({searchFieldRef, onSearch}) {
  // XXX: We're not using a controlled component for the input. Because a lot of the operations surrounding it are async,
  // we don't want to have to deal with races. Instead, we're going to reset the input manually when the time is right.

  function handleSearch(ev) {
    clearTimeout(ev.target[debounceTimer]);
    ev.target[debounceTimer] = setTimeout(() => {
      onSearch(ev.target.value);
    }, debounceTimeout);
  }

  return (
    <form onSubmit={e => e.preventDefault()}>
      <label className="category-search-field">
        <span>
          <Translate>Find a category by keyword:</Translate>
        </span>
        <input
          ref={searchFieldRef}
          type="search"
          placeholder={Translate.string('Search all categories...')}
          aria-describedby="category-search-info"
          onChange={handleSearch}
        />
      </label>
      <p className="category-search-info">
        <Translate>Search results will update as you type.</Translate>
      </p>
    </form>
  );
}

CategorySearchView.propTypes = {
  searchFieldRef: PropTypes.object,
  onSearch: PropTypes.func.isRequired,
};

function BreadcrumbView({path, onChangeCategory}) {
  if (!path?.length) {
    return null;
  }

  return (
    <div className="breadcrumbs">
      <span>{Translate.string('in')}</span>
      {path.map(category => (
        <button
          type="button"
          key={category.id}
          onClick={() => onChangeCategory(category.id)}
          aria-label={Translate.string('View the {title} category', {title: category.title})}
        >
          {category.title}
        </button>
      ))}
    </div>
  );
}

BreadcrumbView.propTypes = {
  path: PropTypes.array,
  onChangeCategory: PropTypes.func,
};

function CategoryItemLabelView({category, onChangeCategory}) {
  if (!category.hasChildren) {
    return <span className="category-nav-list-item-title">{category.title}</span>;
  }

  return (
    <button
      type="button"
      className="category-nav-drilldown"
      onClick={() => onChangeCategory(category.id)}
      disabled={!category.canAccess}
      aria-label={Translate.string('See subcategories under {category}', {
        category: category.title,
      })}
    >
      {category.title}
    </button>
  );
}

CategoryItemLabelView.propTypes = {
  category: PropTypes.object.isRequired,
  onChangeCategory: PropTypes.func.isRequired,
};

function CategoryStatsView({category}) {
  const {title, deepEventCount: events, deepCategoryCount: subcategories} = category;

  const categoryTipText = Translate.string(
    '{title} category contains {events} and {subcategories}',
    {
      title,
      events: PluralTranslate.string('{count} event', '{count} events', events, {
        count: events,
      }),
      subcategories: PluralTranslate.string(
        '{count} subcategory',
        '{count} subcategories',
        subcategories,
        {count: subcategories}
      ),
    }
  );

  return (
    <span className="category-nav-stats">
      <span className="category-nav-stats-events" aria-hidden="true">
        <span aria-hidden="true">{events}</span>
      </span>
      <span className="category-nav-stats-subcategories" aria-hidden="true">
        <span aria-hidden="true">{subcategories}</span>
      </span>
      <ind-with-toggletip>
        <button type="button">
          <span>
            <Translate>Show category stats</Translate>
          </span>
        </button>
        <span data-tip-content aria-live="polite">
          {categoryTipText}
        </span>
      </ind-with-toggletip>
    </span>
  );
}

CategoryStatsView.propTypes = {
  category: PropTypes.object.isRequired,
};

function CategoryListView({category, subcategories, onChangeCategory, actionView: ActionView}) {
  if (!category) {
    return null;
  }

  return (
    <article className="category-list-section" aria-labelledby="category-nav-category-list">
      <header>
        <div className="category-nav-actions">
          <div>
            <h3 id="category-nav-category-list" className="category-nav-list-item-title">
              {category.title}
            </h3>
            <BreadcrumbView path={category.path} onChangeCategory={onChangeCategory} />
          </div>
          {ActionView && <ActionView category={category} />}
        </div>
        <CategoryStatsView category={category} />
      </header>
      <ul>
        {subcategories.map(subcategory => (
          <li key={subcategory.id} data-haschildren={subcategory.hasChildren}>
            <div className="category-nav-actions">
              <CategoryItemLabelView onChangeCategory={onChangeCategory} category={subcategory} />
              <div className="category-list-actions">
                {ActionView && <ActionView category={subcategory} />}
              </div>
            </div>
            <CategoryStatsView category={subcategory} />
          </li>
        ))}
      </ul>
    </article>
  );
}

CategoryListView.propTypes = {
  category: PropTypes.object,
  subcategories: PropTypes.array,
  onChangeCategory: PropTypes.func,
  actionView: PropTypes.elementType,
};

function SearchResultsView({
  searchResults,
  searchKeyword,
  onChangeCategory,
  onCancelSearch,
  actionView: ActionView,
}) {
  return (
    <article className="category-search-results">
      <h3>
        <Translate>Category search results</Translate>
      </h3>
      {searchResults.length ? (
        <ul>
          {searchResults.map(category => (
            <li key={category.id} data-haschildren={category.hasChildren}>
              <div className="category-nav-actions">
                <div>
                  <CategoryItemLabelView category={category} onChangeCategory={onChangeCategory} />
                  <BreadcrumbView path={category.path} onChangeCategory={onChangeCategory} />
                </div>
                {ActionView && <ActionView category={category} />}
              </div>
              <CategoryStatsView category={category} />
            </li>
          ))}
        </ul>
      ) : (
        <div className="category-search-no-results" aria-live="assertive" aria-atomic="true">
          <Translate as="p">
            No categories matched "<Param name="keyword" value={searchKeyword} />
            ".
          </Translate>
          <button type="button" onClick={onCancelSearch}>
            <Translate>Go back to the category list</Translate>
          </button>
        </div>
      )}
    </article>
  );
}

SearchResultsView.propTypes = {
  searchKeyword: PropTypes.string,
  searchResults: PropTypes.array,
  onChangeCategory: PropTypes.func,
  onCancelSearch: PropTypes.func,
  actionView: PropTypes.elementType,
};

export function DialogView(props) {
  const {
    dialogRef,
    searchFieldRef,
    dialogTitle = 'Navigate to a category',
    loading,
    error,
    onSearch,
    searchKeyword,
    searchResults,
    actionView,
    onChangeCategory,
    onCancelSearch,
    ...categoryListProps
  } = props;

  const commonListProps = {
    actionView,
    onChangeCategory,
  };

  function handleClose(ev) {
    ev.target.closest('dialog').close();
  }

  const closeButton = (
    <button type="button" value="close" onClick={handleClose}>
      <span>
        <Translate>Close</Translate>
      </span>
    </button>
  );

  return (
    <Dialog ref={dialogRef} id="category-nav-dialog" aria-labelledby="category-nav">
      <div className="titlebar">
        <h2 id="category-nav">{dialogTitle}</h2>
        {closeButton}
      </div>
      <div className="content">
        {error ? null : <CategorySearchView searchFieldRef={searchFieldRef} onSearch={onSearch} />}
        <LoadingView loading={loading}>
          <ErrorView error={error} />
          {searchResults ? (
            <SearchResultsView
              searchResults={searchResults}
              searchKeyword={searchKeyword}
              onCancelSearch={onCancelSearch}
              {...commonListProps}
            />
          ) : (
            <CategoryListView {...categoryListProps} {...commonListProps} />
          )}
        </LoadingView>
      </div>
      <div className="button-bar">{closeButton}</div>
    </Dialog>
  );
}

DialogView.propTypes = {
  dialogRef: PropTypes.object,
  searchFieldRef: PropTypes.object,
  dialogTitle: PropTypes.string,
  category: PropTypes.object,
  subcategories: PropTypes.array,
  searchKeyword: PropTypes.string,
  searchResults: PropTypes.array,
  error: PropTypes.object,
  loading: PropTypes.bool,
  onChangeCategory: PropTypes.func,
  onSearch: PropTypes.func,
  onCancelSearch: PropTypes.func,
  actionView: PropTypes.elementType,
};
