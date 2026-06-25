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

// import ArrowIcon from '../../../web/static/images/circle-arrow-right-solid-full.svg';
// import { ReactComponent as ArrowIcon } from '../../../web/static/images/circle-arrow-right-solid-full.svg';

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
          <Card.Icon icon="fas:folder" color="primary" size="md" variant="compact" decorative />
          {/* <Card.Icon
            icon= {ArrowIcon}
            color="primary"
            size="md"
            variant="plain"
          /> */}
          {/* <Card.Icon icon={{svg: <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path fill="rgb(71, 147, 206)" d="M320 576C461.4 576 576 461.4 576 320C576 178.6 461.4 64 320 64C178.6 64 64 178.6 64 320C64 461.4 178.6 576 320 576zM361 417C351.6 426.4 336.4 426.4 327.1 417C317.8 407.6 317.7 392.4 327.1 383.1L366.1 344.1L216 344.1C202.7 344.1 192 333.4 192 320.1C192 306.8 202.7 296.1 216 296.1L366.1 296.1L327.1 257.1C317.7 247.7 317.7 232.5 327.1 223.2C336.5 213.9 351.7 213.8 361 223.2L441 303.2C450.4 312.6 450.4 327.8 441 337.1L361 417.1z"/></svg>}}
          
          <Card.Icon
            icon={{svg: <img src={ArrowIcon} />}}
            color="primary"
            size="md"
            variant="plain"
          /> */}
          <div styleName="card-main">
            <Card.Header>{category.title}</Card.Header>
            <Card.Meta>
              {category.deepCategoryCount > 0 ? (
                <>
                  {category.deepCategoryCount} Categories
                  <span styleName="dot-divider">•</span>
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
