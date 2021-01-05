// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global updateHtml:false */

(function(global) {
  'use strict';

  function setupToggle() {
    var $roles = $('#event-roles');
    $roles.on('click', '.toggle-members', function() {
      var $row = $(this)
        .closest('tr')
        .next('tr')
        .find('.slide');
      $row.css('max-height', $row[0].scrollHeight + 'px');
      $row.toggleClass('open close');
    });

    $roles.on('indico:htmlUpdated', function() {
      $(this)
        .find('.slide')
        .each(function() {
          $(this).css('max-height', this.scrollHeight + 'px');
        });
    });
  }

  function setupButtons() {
    $('#event-roles').on('click', '.js-add-members', function(evt) {
      evt.stopPropagation();
      var $this = $(this);
      $('<div>')
        .principalfield({
          multiChoice: true,
          onAdd: function(users) {
            $.ajax({
              url: $this.data('href'),
              method: $this.data('method'),
              data: JSON.stringify({users: users}),
              dataType: 'json',
              contentType: 'application/json',
              error: handleAjaxError,
              complete: IndicoUI.Dialogs.Util.progress(),
              success: function(data) {
                updateHtml($this.data('update'), data);
              },
            });
          },
        })
        .principalfield('choose');
    });
  }

  global.setupRolesList = function setupRolesList() {
    setupToggle();
    setupButtons();
  };
})(window);
