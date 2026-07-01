// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import getCategoryChildrenURL from 'indico-url:categories.get_category_children';

import React from 'react';

import {useIndicoAxios} from 'indico/react/hooks/hooks';

import {Card} from './Card';

import './CategoryCardList.module.scss';

interface CategoryCardListProps {
  categoryId: number;
  columns?: 1 | 2 | 3;
}

export function CategoryCardList({categoryId, columns = 2}: CategoryCardListProps) {
  const url = getCategoryChildrenURL({
    category_id: String(categoryId),
  });

  const {data} = useIndicoAxios(url, {
    camelize: true,
  });

  const categories = data?.categories ?? [];

  const gridClass = `${columns > 1 ? `grid-${columns}-responsive` : ''}`;

  return (
    <div className={gridClass} role="group">
      {categories.map(category => (
        <Card styleName="category-card" key={category.id} href={category.displayURL}>
          <Card.Icon icon="fas:folder" color="primary" size="md" variant="compact" decorative />
          <div styleName="category-card-main">
            <Card.Header styleName="category-card-header">{category.title}</Card.Header>
            <Card.Meta styleName="category-card-meta">
              {category.deepCategoryCount === 0 && category.deepEventCount === 0 ? (
                'Empty'
              ) : (
                <>
                  {category.deepCategoryCount > 0 && (
                    <>
                      {category.deepCategoryCount} Categories
                      {category.deepEventCount > 0 && (
                        <span styleName="category-card-dot-divider" aria-hidden="true">
                          •
                        </span>
                      )}
                    </>
                  )}
                  {category.deepEventCount > 0 ? `${category.deepEventCount} Events` : null}
                </>
              )}
            </Card.Meta>
          </div>
          {category.isProtected ? (
            <Card.Icon
              icon="fas:shield-halved"
              color="error"
              size="sm"
              variant="light"
              ariaLabel="Protected Category"
            />
          ) : (
            <Card.Icon
              icon="fas:chevron-right"
              styleName="category-card-arrow-icon"
              color="gray"
              size="xs"
              variant="plain"
              ariaLabel="View Category"
            />
          )}
        </Card>
      ))}
    </div>
  );
}
