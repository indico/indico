// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import getCategoryChildrenURL from 'indico-url:categories.get_category_children';

import React from 'react';

import {useIndicoAxios} from 'indico/react/hooks/hooks';
import {Translate} from 'indico/react/i18n';

// eslint-disable-next-line import/no-unresolved
import ArrowIcon from '../icon/circle-arrow-right-solid-full.svg?react';

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

  const {data, loading} = useIndicoAxios(url, {
    camelize: true,
  });

  if (loading) {
    return (
      <div aria-busy="true">
        <Translate>Loading...</Translate>
      </div>
    );
  }

  const gridClass = `${columns > 1 ? `grid-${columns}-responsive` : ''}`;

  return (
    <div className={gridClass}>
      {data.categories.map(category => (
        <Card
          styleName="category-card-wrapper"
          key={category.id}
          href={category.displayURL}
          ariaLabel={category.description || category.title}
        >
          <Card.Icon 
            icon="fas:folder" 
            color="primary" 
            size="md" 
            variant="compact" 
            decorative />
          <Card.Icon
            icon= {ArrowIcon}
            color="success"
            size="sm"
            variant="compact"
          />
          <div styleName="card-main" className="indico-ui">
            <Card.Header>{category.title}</Card.Header>
            <Card.Meta>
              {category.deepCategoryCount > 0 ? (
                <>
                  {category.deepCategoryCount} Categories
                  <span styleName="dot-divider" className="indico-ui">
                    •
                  </span>
                </>
              ) : null}
              {category.deepEventCount > 0 ? `${category.deepEventCount} Events` : null}
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
              styleName="arrow-icon"
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
