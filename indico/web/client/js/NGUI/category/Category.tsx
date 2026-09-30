// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import apiCategoryChildrenURL from 'indico-url:categories.api_category_children';
import apiCategoryInfoURL from 'indico-url:categories.api_category_info';
import apiEventListWithMetadataURL from 'indico-url:categories.api_event_list_with_metadata';

import React from 'react';
import remarkRehype from 'remark-rehype';

import {Card} from 'indico/NGUI/card/Card';
import {CategoryCardList} from 'indico/NGUI/category/CategoryCardList';
import {EventList} from 'indico/NGUI/category/EventList';
import {
  CategoryEventListWithMetaData,
  CategoryChildMetadata,
  Category as CategoryType,
} from 'indico/NGUI/types';
import {useIndicoAxios} from 'indico/react/hooks/hooks';
import {Translate} from 'indico/react/i18n';
import {Markdown} from 'indico/react/util';

import './Category.module.scss';
import {CategorySidebar} from '../category_sidebar/CategorySidebar';

interface CategoryProps {
  categoryId: number;
  isFlat?: boolean;
}

export function Category({categoryId, isFlat}: CategoryProps) {
  const {data: categoryInfo, loading: categoryLoading} = useIndicoAxios(
    {url: apiCategoryInfoURL({category_id: categoryId})},
    {camelize: true}
  );

  const category = categoryInfo as CategoryType;

  const {data: categoryChildrenData, loading: childrenLoading} = useIndicoAxios(
    {url: apiCategoryChildrenURL({category_id: categoryId})},
    {camelize: true}
  );

  const categoryChildren = categoryChildrenData as CategoryChildMetadata[];

  const {data: categoryEventListWithMetaData, loading: categoryEventListWithMetaDataLoading} =
    useIndicoAxios(
      {
        url: apiEventListWithMetadataURL({
          category_id: categoryId,
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

  const isUntitledRoot = category.title === 'Home' && category.isRoot;

  // (Ajob) Honestly, I think the whole idea of checking the string for 'Home' is very hacky
  let title = <h1>{category.title}</h1>;
  if (isUntitledRoot) {
    title = (
      // @ts-expect-error A string for 'as' is possible, just not typed properly
      <Translate as="h1">{category.hasChildren ? 'Main categories' : 'All events'}</Translate>
    );
  }

  return (
    <div styleName="category-wrapper">
      <section styleName="category">
        <section styleName="category-main">
          {title}
          <Card styleName="category-info">
            {category.logoURL && (
              <img styleName="category-logo" src={category.logoURL} alt={category.title} />
            )}
            <div styleName="category-description">
              {/* Markdown will be replaced by custom solution */}
              <Markdown rehypePlugins={[remarkRehype]}>{category.description}</Markdown>
            </div>
          </Card>
          {!isFlat && <CategoryCardList data={categoryChildren} />}
        </section>
        <CategorySidebar categoryId={categoryId} isFlat={isFlat} />
      </section>
      {!categoryEventListWithMetaDataLoading && categoryEventListWithMeta && (
        <EventList viewData={categoryEventListWithMeta} categoryId={categoryId} isFlat={isFlat} />
      )}
    </div>
  );
}
