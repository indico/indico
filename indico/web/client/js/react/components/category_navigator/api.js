// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

/* global build_url */

export async function fetchCategoryInfo(id) {
  try {
    const {data} = await indicoAxios.get(build_url(Indico.Urls.Categories.info, {category_id: id}));
    return data;
  } catch (error) {
    if (error.response?.status === 403) {
      return null;
    }
    handleAxiosError(error);
    throw error;
  }
}

export async function fetchReachableCategories(id, exclude = []) {
  try {
    const {data} = await indicoAxios.post(
      build_url(Indico.Urls.Categories.infoFrom, {category_id: id}),
      {exclude}
    );
    return data;
  } catch (error) {
    handleAxiosError(error);
    throw error;
  }
}

export async function searchCategories(query) {
  try {
    const {data} = await indicoAxios.get(build_url(Indico.Urls.Categories.search), {
      params: {q: query},
    });
    return data;
  } catch (error) {
    handleAxiosError(error);
    throw error;
  }
}
