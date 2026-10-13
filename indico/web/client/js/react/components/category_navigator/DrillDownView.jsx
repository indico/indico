// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {Translate, Param} from 'indico/react/i18n';

import CategoryActionElement from './CategoryActionElement';
import {canActOnCategory} from './categoryActionUtils';
import CategoryStats from './CategoryStats';

export default function DrillDownView({
  navigatorState,
  actionButtonText,
  isNavigation,
  actionUrl,
  actionOn,
  emptyCategoryText,
  onAction,
  focusSearch,
}) {
  const {
    currentCategory,
    subcategories,
    navigateTo,
    isBrowsingFromSearch,
    searchQuery,
    returnToSearchResults,
    isLoadingSubcategories,
    isError,
  } = navigatorState;

  if (!currentCategory) {
    return null;
  }

  const parentPath = currentCategory.parent_path || [];
  const parentCategory = parentPath.length > 0 ? parentPath[parentPath.length - 1] : null;

  const currentActionState = canActOnCategory(currentCategory, actionOn);

  return (
    <div className="drilldown-view">
      {isBrowsingFromSearch && (
        <div className="search-return-banner">
          <button type="button" className="return-button" onClick={returnToSearchResults}>
            <span className="icon-arrow-left" aria-hidden="true" />
            <span>
              <Translate>
                Back to search results for "<Param name="query" value={searchQuery} />"
              </Translate>
            </span>
          </button>
        </div>
      )}

      <div className="item current-category">
        {currentCategory.is_protected && (
          <span className="protection icon-shield">
            <span className="visually-hidden">
              <Translate>This category is protected</Translate>
            </span>
          </span>
        )}
        <div className="title-wrapper">
          <h3 className="title">{currentCategory.title}</h3>
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
                        onClick={() => navigateTo(parent.id)}
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

        <div className="side-panel">
          {parentCategory && (
            <ind-with-tooltip class="parent-category-control">
              <button
                type="button"
                className="icon-arrow-up navigate-up js-navigate-up"
                onClick={() => navigateTo(parentCategory.id)}
              >
                <span data-tip-content>
                  <Translate>
                    Go to parent: <Param name="title" value={parentCategory.title} />
                  </Translate>
                </span>
              </button>
            </ind-with-tooltip>
          )}
          <CategoryActionElement
            category={currentCategory}
            actionButtonText={actionButtonText}
            isNavigation={isNavigation}
            actionUrl={actionUrl}
            disabled={!currentActionState.allowed}
            disabledMessage={currentActionState.message}
            onAction={onAction}
          />
        </div>
      </div>

      {isLoadingSubcategories ? (
        <div className="spinner-wrapper">
          <div className="i-spinner" />
        </div>
      ) : isError ? (
        <div className="placeholder">
          <div className="placeholder-text">
            <Translate>Failed to load category</Translate>
          </div>
        </div>
      ) : subcategories.length > 0 ? (
        <ul className="group-list subcategory-list">
          {subcategories.map(subcat => {
            const subActionState = canActOnCategory(subcat, actionOn);
            return (
              <li key={subcat.id} className="item subcategory">
                <div className="drill-down-area title-wrapper">
                  <button
                    type="button"
                    className="category-drill-button js-go-to"
                    onClick={() => navigateTo(subcat.id)}
                    disabled={!subcat.can_access}
                  >
                    {subcat.is_protected && (
                      <span className="protection icon-shield">
                        <span className="visually-hidden">
                          <Translate>This category is protected</Translate>{' '}
                        </span>
                      </span>
                    )}
                    <span className="title">{subcat.title}</span>
                    <span className="icon-folder" aria-hidden="true" />
                  </button>
                </div>
                <div className="side-panel">
                  <CategoryStats category={subcat} />
                  <CategoryActionElement
                    category={subcat}
                    actionButtonText={actionButtonText}
                    isNavigation={isNavigation}
                    actionUrl={actionUrl}
                    disabled={!subActionState.allowed}
                    disabledMessage={subActionState.message}
                    onAction={onAction}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="placeholder">
          <div className="placeholder-text">{emptyCategoryText}</div>
          <div className="placeholder-actions">
            {!currentActionState.allowed ? (
              parentCategory && (
                <Translate>
                  You can{' '}
                  <Param
                    name="navigateUp"
                    wrapper={
                      <button
                        type="button"
                        className="link-style"
                        onClick={() => navigateTo(parentCategory.id)}
                      />
                    }
                  >
                    navigate up
                  </Param>{' '}
                  or{' '}
                  <Param
                    name="search"
                    wrapper={<button type="button" className="link-style" onClick={focusSearch} />}
                  >
                    search
                  </Param>
                  .
                </Translate>
              )
            ) : !parentCategory ? (
              <Translate>
                You can only{' '}
                <Param
                  name="action"
                  value={actionButtonText.toLowerCase()}
                  wrapper={
                    <button
                      type="button"
                      className="link-style"
                      onClick={() => onAction(currentCategory)}
                    />
                  }
                />{' '}
                this one.
              </Translate>
            ) : (
              <Translate>
                You can{' '}
                <Param
                  name="action"
                  value={actionButtonText.toLowerCase()}
                  wrapper={
                    <button
                      type="button"
                      className="link-style"
                      onClick={() => onAction(currentCategory)}
                    />
                  }
                />{' '}
                this one,{' '}
                <Param
                  name="navigateUp"
                  wrapper={
                    <button
                      type="button"
                      className="link-style"
                      onClick={() => navigateTo(parentCategory.id)}
                    />
                  }
                >
                  navigate up
                </Param>{' '}
                or{' '}
                <Param
                  name="search"
                  wrapper={<button type="button" className="link-style" onClick={focusSearch} />}
                >
                  search
                </Param>
                .
              </Translate>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

DrillDownView.propTypes = {
  navigatorState: PropTypes.object.isRequired,
  actionButtonText: PropTypes.string.isRequired,
  isNavigation: PropTypes.bool.isRequired,
  actionUrl: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  actionOn: PropTypes.object.isRequired,
  emptyCategoryText: PropTypes.string.isRequired,
  onAction: PropTypes.func.isRequired,
  focusSearch: PropTypes.func.isRequired,
};

DrillDownView.defaultProps = {
  actionUrl: null,
};
