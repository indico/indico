// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import categoriesInfoFromURL from 'indico-url:categories.info';
import categorySearchResults from 'indico-url:categories.search';

import {indicoAxios} from 'indico/utils/axios';

export function getCategoryData(categoryId) {
  return indicoAxios.get(categoriesInfoFromURL({category_id: categoryId}));
}

export function getCategorySearchResults(scopeCategoryId, keyword) {
  return indicoAxios.get(categorySearchResults({q: keyword, category: scopeCategoryId}));
}
