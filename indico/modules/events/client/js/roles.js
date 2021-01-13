// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global updateHtml:false, handleAjaxError:false */

import {showUserSearch} from 'indico/react/components/principals/imperative';

(function(global) {
  function setupToggle() {
    const $roles = $('#event-roles');
    $roles.on('click', '.toggle-members', function() {
      const $row = $(this)
        .closest('tr')
        .next('tr')
        .find('.slide');
      $row.css('max-height', `${$row[0].scrollHeight}px`);
      $row.toggleClass('open close');
    });

    $roles.on('indico:htmlUpdated', function() {
      $(this)
        .find('.slide')
        .each(function() {
          $(this).css('max-height', `${this.scrollHeight}px`);
        });
    });
  }

  function setupButtons() {
    $('#event-roles').on('click', '.js-add-members', async evt => {
      evt.stopPropagation();
      const $this = $(evt.target);
      const users = await showUserSearch({withExternalUsers: true});
      if (users.length) {
        $.ajax({
          url: $this.data('href'),
          method: $this.data('method'),
          data: JSON.stringify({users}),
          dataType: 'json',
          contentType: 'application/json',
          error: handleAjaxError,
          complete: IndicoUI.Dialogs.Util.progress(),
          success(data) {
            updateHtml($this.data('update'), data);
          },
        });
      }
    });
  }

  global.setupRolesList = function setupRolesList() {
    setupToggle();
    setupButtons();
  };
})(window);
