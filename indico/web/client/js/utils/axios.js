// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import axios from 'axios';
import isURLSameOrigin from 'axios/lib/helpers/isURLSameOrigin';
import qs from 'qs';

import showReactErrorDialog from 'indico/react/errors';
import {$T} from 'indico/utils/i18n';

export const indicoAxios = axios.create({
  paramsSerializer: params => qs.stringify(params, {arrayFormat: 'repeat'}),
  xsrfCookieName: null,
  xsrfHeaderName: null,
});

indicoAxios.isCancel = axios.isCancel;
indicoAxios.CancelToken = axios.CancelToken;

indicoAxios.interceptors.request.use(config => {
  if (isURLSameOrigin(config.url)) {
    config.headers.common['X-Requested-With'] = 'XMLHttpRequest'; // needed for `request.is_xhr`
    config.headers.common['X-CSRF-Token'] = document
      .getElementById('csrf-token')
      .getAttribute('content');
  }
  return config;
});

export function handleAxiosError(error, strict = false) {
  if (axios.isCancel(error)) {
    return;
  }
  if (error.response && error.response.data && error.response.data.error) {
    error = error.response.data.error;
  } else {
    if (strict) {
      throw error;
    }
    error = {
      title: $T.gettext('Something went wrong'),
      message: error.message,
    };
  }
  showReactErrorDialog(error);
  return error.message;
}

export default indicoAxios;
