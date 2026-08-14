// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// import apiEventListURL from 'indico-url:categories.api_event_list';

import apiViewDataURL from 'indico-url:categories.api_view_data';
import getCategoryChildrenURL from 'indico-url:categories.get_category_children';

import React from 'react';

import {useIndicoAxios} from 'indico/react/hooks/hooks';

import {CategoryCardList} from '../card/CategoryCardList';
import {EventList} from '../list/EventList';
// import { EventList } from '../list/EventList';

interface CategoryProps {
  categoryId: number;
}

export function Category({categoryId}: CategoryProps) {
  const {data: categoryChildrenData, loading: categoryChildrenLoading} = useIndicoAxios(
    {url: getCategoryChildrenURL({category_id: String(categoryId)})},
    {camelize: true}
  );

  const viewDataURL = apiViewDataURL({
    category_id: String(categoryId),
  });
  const {data: categoryViewData} = useIndicoAxios(viewDataURL, {
    camelize: true,
  });

  if (!categoryChildrenData || categoryChildrenLoading) {
    return null;
  }
  // const category = data.category;
  // console.log('Category data:', category);

  return (
    <div>
      <CategoryCardList data={categoryChildrenData} columns={2} />
      <EventList viewData={categoryViewData} categoryId={categoryId} />
    </div>
  );
}
