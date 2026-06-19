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
}

export function CategoryCardList({categoryId}: CategoryCardListProps) {
  const url = getCategoryChildrenURL({
    category_id: String(categoryId),
  });

  const {data, loading, error} = useIndicoAxios(url, {
    camelize: true,
  });

  if (loading || !data || error) {
    return null;
  }

  return (
    <div>
      {data.categories.map(category => (
        <Card key={category.id} href={category.displayURL}>
          <Card.Icon
            icon={{name: 'folder', prefix: 'fas'}}
            color="primary"
            size="md"
            variant="plain"
          />
          <div styleName="card-main">
            <Card.Header>{category.title}</Card.Header>
            <Card.Meta>
              {category.deepCategoryCount || 0} Categories <span>•</span>{' '}
              {category.deepEventCount || 0} Events
            </Card.Meta>
          </div>
          {category.isProtected ? (
            <Card.Icon
              icon={{name: 'shield-halved', prefix: 'fas'}}
              color="error"
              size="sm"
              variant="light"
              title="Protected"
              label="Protected Category"
            />
          ) : (
            <Card.Icon
              icon={{name: 'chevron-right', prefix: 'fas'}}
              color="gray"
              size="xs"
              variant="plain"
              title="View Category"
              label="View Category"
            />
          )}
        </Card>
      ))}
    </div>
  );
}
