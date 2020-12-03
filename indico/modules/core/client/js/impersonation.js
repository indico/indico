// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import impersonateURL from 'indico-url:auth.admin_impersonate';

import React from 'react';
import ReactDOM from 'react-dom';

import {PersonLinkSearch} from 'indico/react/components/principals/PersonLinkSearch';
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
      <PersonLinkSearch
        existing={[]}
        onAddItems={e => impersonateUser(e.userId)}
        disabled={false}
        withExternalUsers={false}
        triggerFactory={searchTrigger}
        alwaysConfirm
        single
      />,
      document.getElementById('login-as')
    );
  }
});
