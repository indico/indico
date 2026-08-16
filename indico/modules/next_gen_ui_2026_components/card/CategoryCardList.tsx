// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';

import {CategoryMetaData} from '../types';

import {Card} from './Card';

import './CategoryCardList.module.scss';

interface CategoryCardListProps {
  data: CategoryMetaData[];
  columns?: 1 | 2 | 3;
}

export function CategoryCardList({data, columns = 2}: CategoryCardListProps) {
  const categories = data ?? [];

  const gridClass = `${columns > 1 ? `grid-${columns}-responsive` : ''}`;

  return (
    <div className={gridClass} role="group" styleName="category-card-list">
      {categories.map(category => (
        <Card styleName="category-card" key={category.id} href={category.displayURL}>
          <Card.Icon
            icon="fas:folder"
            compact
            size="xxxxl"
            decorative
            styleName="category-card-folder-icon"
          />
          <div styleName="category-card-main">
            <Card.Header styleName="category-card-header">{category.title}</Card.Header>
            <Card.Meta styleName="category-card-meta">
              {category.deepCategoryCount === 0 && category.deepEventCount === 0 ? (
                <Translate>Empty</Translate>
              ) : (
                <>
                  {category.deepCategoryCount > 0 && (
                    <>
                      <PluralTranslate count={category.deepCategoryCount}>
                        <Singular>
                          <Param name="count" value={category.deepCategoryCount} /> Category
                        </Singular>
                        <Plural>
                          <Param name="count" value={category.deepCategoryCount} /> Categories
                        </Plural>
                      </PluralTranslate>
                      {category.deepEventCount > 0 && (
                        <span styleName="category-card-dot-divider" aria-hidden="true">
                          •
                        </span>
                      )}
                    </>
                  )}
                  {category.deepEventCount > 0 && (
                    <PluralTranslate count={category.deepEventCount}>
                      <Singular>
                        <Param name="count" value={category.deepEventCount} /> Event
                      </Singular>
                      <Plural>
                        <Param name="count" value={category.deepEventCount} /> Events
                      </Plural>
                    </PluralTranslate>
                  )}
                </>
              )}
            </Card.Meta>
          </div>
          {category.isProtected ? (
            <Card.Icon
              icon="fas:shield-halved"
              color="error"
              size="sm"
              variant="transparent"
              ariaLabel="Protected Category"
            />
          ) : (
            <Card.Icon
              icon="fas:chevron-right"
              styleName="category-card-arrow-icon"
              color="gray"
              size="xs"
              variant="transparent"
              ariaLabel="View Category"
            />
          )}
        </Card>
      ))}
    </div>
  );
}
