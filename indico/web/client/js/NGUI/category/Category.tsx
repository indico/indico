// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import apiCategoryChildrenURL from 'indico-url:categories.api_category_children';
import apiCategoryInfoURL from 'indico-url:categories.api_category_info';
import apiEventListWithMetadataURL from 'indico-url:categories.api_event_list_with_metadata';
import manageModerationURL from 'indico-url:categories.manage_moderation';

import React, {useState} from 'react';
import remarkRehype from 'remark-rehype';

import {CategoryCardList} from 'indico/NGUI/category/CategoryCardList';
import {EventList} from 'indico/NGUI/category/EventList';
import MessageBox from 'indico/NGUI/message_box/MessageBox';
import {
  CategoryEventListWithMetaData,
  CategoryChildMetadata,
  Category as CategoryType,
} from 'indico/NGUI/types';
import {useIndicoAxios} from 'indico/react/hooks/hooks';
import {Translate, Param, Plural, PluralTranslate, Singular} from 'indico/react/i18n';
import {Markdown} from 'indico/react/util';
import './Category.module.scss';

interface CategoryProps {
  categoryId: number;
  isFlatInit?: boolean;
}

export function Category({categoryId, isFlatInit = false}: CategoryProps) {
  const [isFlat, setIsFlat] = useState(isFlatInit);

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

  const totalEventCount =
    categoryEventListWithMeta?.eventListData.eventCount +
    categoryEventListWithMeta?.eventListData.pastEventCount +
    categoryEventListWithMeta?.eventListData.futureEventCount;

  return (
    <div styleName="category-wrapper">
      {categoryEventListWithMeta && categoryEventListWithMeta.pendingEventMoves > 0 && (
        <MessageBox type="warning" icon={false}>
          <span>
            <PluralTranslate count={categoryEventListWithMeta.pendingEventMoves}>
              <Singular>
                There is <Param name="count" value={categoryEventListWithMeta.pendingEventMoves} />{' '}
                event move request{' '}
                <Param
                  name="url"
                  wrapper={<a href={manageModerationURL({category_id: categoryId})} />}
                >
                  {' '}
                  pending moderation
                </Param>
                .
              </Singular>
              <Plural>
                There are <Param name="count" value={categoryEventListWithMeta.pendingEventMoves} />{' '}
                events move requests{' '}
                <Param
                  name="url"
                  wrapper={<a href={manageModerationURL({category_id: categoryId})} />}
                >
                  {' '}
                  pending moderation
                </Param>
                .
              </Plural>
            </PluralTranslate>
          </span>
        </MessageBox>
      )}
      {category.title === 'Home' && category.isRoot ? (
        category.hasChildren ? (
          <h1>
            <Translate>Main categories</Translate>
          </h1>
        ) : (
          <h1>
            <Translate>All events</Translate>
          </h1>
        )
      ) : (
        <h1>{category.title}</h1>
      )}
      <div styleName="category-info">
        {category.logoURL && (
          <img styleName="category-logo" src={category.logoURL} alt={category.title} />
        )}
        <div styleName="category-description">
          {/* TODO: Markdown is planned to be replaced by custom solution */}
          <Markdown rehypePlugins={[remarkRehype]}>{category.description}</Markdown>
        </div>
      </div>
      {!category.hasChildren && totalEventCount === 0 && (
        <MessageBox
          type="info"
          message={Translate.string('This category is empty.')}
          icon={false}
          noBorder
        />
      )}

      {!isFlat && <CategoryCardList data={categoryChildren} columns={2} />}
      {isFlat && (
        <MessageBox type="highlight" icon={false}>
          <span>
            Displaying all the events from subcategories.{' '}
            <a onClick={() => setIsFlat(prevIsFlat => !prevIsFlat)}>
              Go back to single category view.{' '}
            </a>
          </span>
        </MessageBox>
      )}
      {categoryEventListWithMeta && categoryEventListWithMeta.hasHiddenEvents && (
        <MessageBox
          type="highlight"
          message={Translate.string('Some events in this category have been hidden.')}
          customIcon="fas:eye-slash"
          noBorder
        />
      )}
      {!categoryEventListWithMetaDataLoading && categoryEventListWithMeta && (
        <EventList viewData={categoryEventListWithMeta} categoryId={categoryId} isFlat={isFlat} />
      )}
    </div>
  );
}
