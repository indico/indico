// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global setupListGenerator:false, getSelectedRows:false, handleSelectedRowHighlight:false, setupTableSorter:false */

(function(global) {
  global.setupRegistrationList = function setupRegistrationList() {
    setupListGenerator();

    function handleRegListRowSelection() {
      $('table.i-table input.select-row')
        .on('change', function() {
          $('.regform-download-attachments').toggleClass(
            'disabled',
            !$('.list input:checkbox:checked[data-has-files=true]').length
          );
        })
        .trigger('change');
    }

    $('body').on('click', '#preview-email', function() {
      var $this = $(this);
      ajaxDialog({
        url: $this.data('href'),
        title: $T.gettext('Email Preview'),
        method: 'POST',
        data: function() {
          return {
            registration_id: getSelectedRows()[0],
            subject: $('#subject').val(),
            body: $('#body').val(),
          };
        },
      });
    });

    $('.registrations').on('indico:confirmed', '.js-delete-registrations', function(evt) {
      evt.preventDefault();
      var $this = $(this);
      var selectedRows = getSelectedRows();
      var msg = $T
        .ngettext(
          'Do you really want to delete the selected registration?',
          'Do you really want to delete the {0} selected registrations?',
          selectedRows.length
        )
        .format(selectedRows.length);
      confirmPrompt(msg).then(function() {
        $.ajax({
          url: $this.data('href'),
          method: $this.data('method'),
          data: {registration_id: selectedRows},
          complete: IndicoUI.Dialogs.Util.progress(),
          error: handleAjaxError,
          success: function() {
            for (var i = 0; i < selectedRows.length; i++) {
              var row = $('#registration-' + selectedRows[i]);
              row.fadeOut('fast', function() {
                $(this).remove();
              });
            }
          },
        });
      });
    });

    $('.registrations').on('indico:confirmed', '.js-modify-status', function(evt) {
      evt.preventDefault();
      var $this = $(this);
      var selectedRows = getSelectedRows();
      $.ajax({
        url: $this.data('href'),
        method: $this.data('method'),
        data: {
          registration_id: selectedRows,
          flag: $this.data('flag'),
        },
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success: function(data) {
          if (data) {
            $('.list-content').html(data.html);
            handleSelectedRowHighlight(true);
            handleRegListRowSelection();
            setupTableSorter();
          }
        },
      });
    });

    var principal = $('#indico-user-to-add').principalfield({
      onAdd: function(users) {
        if (users.length) {
          var url = $('.js-add-user').data('href');
          location.href = build_url(url, {user: users[0].id});
        }
      },
    });

    $('.js-add-user').on('click', function() {
      principal.principalfield('choose');
    });

    $('.js-add-multiple-users').ajaxDialog({
      dialogClasses: 'add-multiple-users-dialog',
      onClose: function(data) {
        if (data) {
          $('.list-content').html(data.html);
          handleSelectedRowHighlight(true);
          handleRegListRowSelection();
          setupTableSorter();
        }
      },
    });
  };
})(window);
