// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import apiCategoryChildrenURL from 'indico-url:categories.api_category_children';
import apiCategoryInfoURL from 'indico-url:categories.api_category_info';
import apiEventListWithMetaDataURL from 'indico-url:categories.api_event_list_with_meta_data';

import React from 'react';
import remarkRehype from 'remark-rehype';

import {useIndicoAxios} from 'indico/react/hooks/hooks';
import {Markdown} from 'indico/react/util';

import {CategoryCardList} from '../card/CategoryCardList';
import {EventList} from '../list/EventList';
import {CategoryEventListWithMetaData, CategoryMetaData, CategoryType} from '../types';

import './Category.module.scss';

interface CategoryProps {
  categoryId: number;
  isFlat?: boolean;
}

export function Category({categoryId, isFlat}: CategoryProps) {
  const {data: categoryInfo, loading: categoryLoading} = useIndicoAxios(
    {url: apiCategoryInfoURL({category_id: String(categoryId)})},
    {camelize: true}
  );

  const category = categoryInfo as CategoryType;

  const {data: categoryChildrenData, loading: childrenLoading} = useIndicoAxios(
    {url: apiCategoryChildrenURL({category_id: String(categoryId)})},
    {camelize: true}
  );

  const categoryChildren = categoryChildrenData as {categories: CategoryMetaData[]};

  const {data: categoryEventListWithMetaData, loading: categoryEventListWithMetaDataLoading} =
    useIndicoAxios(
      {
        url: apiEventListWithMetaDataURL({
          category_id: String(categoryId),
          flat: isFlat ? 1 : 0,
        }),
      },
      {
        camelize: true,
      }
    );

  const categoryEventListWithMeta = categoryEventListWithMetaData as CategoryEventListWithMetaData;

  if (!category || categoryLoading || !categoryChildren || childrenLoading) {
    return null;
  }

  return (
    <div>
      {category.title === 'Home' && category.isRoot ? (
        category.hasChildren ? (
          <h1 styleName="category-title">Main categories</h1>
        ) : (
          <h1 styleName="category-title">All events</h1>
        )
      ) : (
        <h1 styleName="category-title">{category.title}</h1>
      )}
      <div styleName="category-info">
        {category.logoURL && (
          <img styleName="category-logo" src={category.logoURL} alt={category.title} />
        )}
        <div styleName="category-description">
          {/* Markdown will be replaced by custom solution */}
          <Markdown rehypePlugins={[remarkRehype]}>{category.description}</Markdown>
        </div>
      </div>
      <CategoryCardList data={categoryChildren.categories} columns={2} />

      {!categoryEventListWithMetaDataLoading && categoryEventListWithMeta && (
        <EventList viewData={categoryEventListWithMeta} categoryId={categoryId} isFlat={isFlat} />
      )}
    </div>
  );
}
