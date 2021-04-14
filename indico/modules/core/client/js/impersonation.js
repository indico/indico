// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import impersonateURL from 'indico-url:auth.admin_impersonate';

import React from 'react';
import ReactDOM from 'react-dom';

import {LazyUserSearch} from 'indico/react/components/principals/Search';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

async function sendRequest(data) {
  try {
    await indicoAxios.post(impersonateURL(), data);
  } catch (error) {
    handleAxiosError(error);
    return;
  }
  window.location.reload();
}

export function impersonateUser(id) {
  sendRequest({user_id: id});
}

const searchTrigger = triggerProps => (
  <a {...triggerProps}>
    <Translate>Login as...</Translate>
  </a>
);

document.addEventListener('DOMContentLoaded', () => {
  const undoLoginAs = document.querySelectorAll('.undo-login-as');
  const loginAs = document.querySelector('#login-as');

  if (undoLoginAs.length) {
    undoLoginAs.forEach(elem => {
      elem.addEventListener('click', e => {
        e.preventDefault();
        sendRequest({undo: true});
      });
    });
  }
  if (loginAs) {
    ReactDOM.render(
      <LazyUserSearch
        existing={[]}
        onAddItems={e => impersonateUser(e.userId)}
        triggerFactory={searchTrigger}
        alwaysConfirm
        single
      />,
      document.getElementById('login-as')
    );
  }
});
