// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {Translate, Param} from 'indico/react/i18n';

import Breadcrumbs from './Breadcrumbs';
import {getCategoryActionState} from './categoryActionUtils';
import CategoryStats from './CategoryStats';
import {useCategoryNavigator} from './context';
import ProtectionStatus from './ProtectionStatus';

function CurrentCategory({category}) {
  const {options, onCategoryAction, navigatorState} = useCategoryNavigator();

  const parentCategory = category.parent_path?.at(-1);
  const actionState = getCategoryActionState(category, options.shouldDisableAction);

  const actionButton = (
    <button
      className="category-action"
      type="button"
      data-category-id={category.id}
      onClick={() => onCategoryAction(category)}
      disabled={actionState.disabled}
      value="action"
    >
      {options.actionButtonText}
    </button>
  );

  return (
    <div className="current-category" data-id={`category-${category.id}`}>
      <ProtectionStatus category={category} />
      <div className="title-wrapper">
        <span className="title">{category.title}</span>
        <Breadcrumbs path={category.parent_path} />
      </div>
      {actionState.disabled && actionState.message ? (
        <ind-with-tooltip>
          {actionButton}
          <span data-tip-content>{actionState.message}</span>
        </ind-with-tooltip>
      ) : (
        actionButton
      )}
      {parentCategory && (
        <button
          className="go-to-parent"
          type="button"
          onClick={() => navigatorState.navigateTo(parentCategory.id)}
          value="drill-up"
        >
          <Translate as="span">
            Go up to <Param name="category" value={parentCategory.title} />
          </Translate>
        </button>
      )}
    </div>
  );
}

CurrentCategory.propTypes = {
  category: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    is_protected: PropTypes.bool,
    parent_path: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.number.isRequired,
        title: PropTypes.string.isRequired,
      })
    ),
  }).isRequired,
};

function SubcategoryItem({category}) {
  const {options, navigatorState, onCategoryAction} = useCategoryNavigator();

  const actionState = getCategoryActionState(category, options.shouldDisableAction);

  const actionButton = (
    <button
      className="category-action"
      type="button"
      data-category-id={category.id}
      onClick={() => onCategoryAction(category)}
      disabled={actionState.disabled}
      value="action"
    >
      {options.actionButtonText}
    </button>
  );

  return (
    <li
      className="subcategory"
      data-category-id={category.id}
      data-accessible={category.can_access}
    >
      <ProtectionStatus category={category} />
      <button
        className="drill-down-target"
        type="button"
        onClick={() => navigatorState.navigateTo(category.id)}
        disabled={!category.can_access}
        value="drill-down"
      >
        <span>{category.title}</span>
      </button>
      {actionState.disabled && actionState.message ? (
        <ind-with-tooltip>
          {actionButton}
          <span data-tip-content>{actionState.message}</span>
        </ind-with-tooltip>
      ) : (
        actionButton
      )}
      <CategoryStats category={category} />
    </li>
  );
}

SubcategoryItem.propTypes = {
  category: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    is_protected: PropTypes.bool,
    can_access: PropTypes.bool,
    deep_category_count: PropTypes.number,
    deep_event_count: PropTypes.number,
  }).isRequired,
};

function EmptyPlaceholder() {
  const {navigatorState, options, onCategoryAction} = useCategoryNavigator();
  const {currentCategory} = navigatorState;

  const parentCategory = currentCategory.parent_path?.at(-1);
  const actionButtonText = options.actionButtonText.toLowerCase();
  const actionState = getCategoryActionState(currentCategory, options.actionOn);

  const handleNavigateUp = () => {
    if (parentCategory) {
      navigatorState.navigateTo(parentCategory.id);
    }
  };

  const handleSearch = () => {
    const searchInput = document.querySelector('#category-navigator .search input');
    if (searchInput) {
      searchInput.focus();
    }
  };

  const handleAction = () => {
    if (!actionState.disabled) {
      onCategoryAction(currentCategory);
    }
  };

  let helpMessage;
  if (!currentCategory.parent_path || currentCategory.parent_path.length === 0) {
    helpMessage = (
      <Translate>
        You can only{' '}
        <Param
          name="action"
          wrapper={<button type="button" className="link-action" onClick={handleAction} />}
        >
          {actionButtonText}
        </Param>{' '}
        this one.
      </Translate>
    );
  } else {
    helpMessage = (
      <Translate>
        You can{' '}
        <Param
          name="action"
          wrapper={<button type="button" className="link-action" onClick={handleAction} />}
        >
          {actionButtonText}
        </Param>{' '}
        this one,{' '}
        <Param
          name="navigateUp"
          wrapper={<button type="button" className="link-action" onClick={handleNavigateUp} />}
        >
          navigate up
        </Param>{' '}
        or{' '}
        <Param
          name="search"
          wrapper={<button type="button" className="link-action" onClick={handleSearch} />}
        >
          search
        </Param>
        .
      </Translate>
    );
  }

  return (
    <div className="placeholder">
      <div className="placeholder-text">{options.emptyCategoryText}</div>
      <div className="placeholder-help">{helpMessage}</div>
    </div>
  );
}

export default function DrillDownView() {
  const {navigatorState} = useCategoryNavigator();
  const {currentCategory, subcategories} = navigatorState;

  if (!currentCategory) {
    return null;
  }

  const hasSubcategories = subcategories.length > 0;
  const hasProtected = subcategories.some(cat => cat.is_protected);

  return (
    <div className="category-list">
      <CurrentCategory category={currentCategory} />

      <ul className="subcategory-list" data-has-protected={hasProtected}>
        {subcategories.map(subcategory => (
          <SubcategoryItem key={subcategory.id} category={subcategory} />
        ))}
      </ul>

      {!hasSubcategories && <EmptyPlaceholder />}
    </div>
  );
}
