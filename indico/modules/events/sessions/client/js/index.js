// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'indico/modules/events/util/types_dialog';

import './session_display';

(function(global) {
  function setupTableSorter() {
    $('#sessions .tablesorter').tablesorter({
      cssAsc: 'header-sort-asc',
      cssDesc: 'header-sort-desc',
      cssInfoBlock: 'avoid-sort',
      cssChildRow: 'session-blocks-row',
      headerTemplate: '',
      sortList: [[1, 0]],
    });
  }

  function setupPalettePickers() {
    $('.palette-picker-trigger').each(function() {
      const $this = $(this);
      $this.palettepicker({
        availableColors: $this.data('colors'),
        selectedColor: $this.data('color'),
        onSelect(background, text) {
          $.ajax({
            url: $(this).data('href'),
            method: $(this).data('method'),
            data: JSON.stringify({colors: {text, background}}),
            dataType: 'json',
            contentType: 'application/json',
            error: handleAjaxError,
            complete: IndicoUI.Dialogs.Util.progress(),
          });
        },
      });
    });
  }

  function patchObject(url, method, data) {
    return $.ajax({
      url,
      method,
      data: JSON.stringify(data),
      dataType: 'json',
      contentType: 'application/json',
      error: handleAjaxError,
      complete: IndicoUI.Dialogs.Util.progress(),
    });
  }

  const filterConfig = {
    itemHandle: 'tr',
    listItems: '#sessions-wrapper tr.session-row',
    term: '#search-input',
    state: '#filtering-state',
    placeholder: '#filter-placeholder',
  };

  global.setupSessionsList = function setupSessionsList(options) {
    options = $.extend(
      {
        createTypeURL: null,
      },
      options
    );
    setupTypePicker(options.createTypeURL);
    enableIfChecked('#sessions-wrapper', '.select-row', '#sessions .js-requires-selected-row');
    setupTableSorter();
    setupPalettePickers();
    handleRowSelection(false);
    const applySearchFilters = setupSearchBox(filterConfig);

    $('#sessions .toolbar').on('click', '.disabled', function(evt) {
      evt.preventDefault();
      evt.stopPropagation();
    });

    $('#sessions-wrapper')
      .on('indico:htmlUpdated', function() {
        setupTableSorter();
        setupPalettePickers();
        handleRowSelection(true);
        _.defer(applySearchFilters);
      })
      .on('click', '.show-session-blocks', function() {
        const $this = $(this);
        ajaxDialog({
          title: $this.data('title'),
          url: $this.data('href'),
        });
      })
      .on('attachments:updated', function(evt) {
        const target = $(evt.target);
        reloadManagementAttachmentInfoColumn(target.data('locator'), target.closest('td'));
      });

    $('.js-submit-session-form').on('click', function(evt) {
      evt.preventDefault();
      const $this = $(this);

      if (!$this.hasClass('disabled')) {
        $('#sessions-wrapper form')
          .attr('action', $this.data('href'))
          .submit();
      }
    });
  };

  function setupTypePicker(createURL) {
    $('#sessions').on('click', '.session-type-picker', function() {
      $(this).itempicker({
        filterPlaceholder: $T.gettext('Filter types'),
        containerClasses: 'session-type-container',
        uncheckedItemIcon: '',
        footerElements: [
          {
            title: $T.gettext('Add new type'),
            onClick(sessionTypePicker) {
              ajaxDialog({
                title: $T.gettext('Add new type'),
                url: createURL,
                onClose(data) {
                  if (data) {
                    $('.session-type-picker').each(function() {
                      const $this = $(this);
                      if ($this.data('indicoItempicker')) {
                        $this.itempicker('updateItemList', data.types);
                      } else {
                        $this.data('items', data.types);
                      }
                    });
                    sessionTypePicker.itempicker('selectItem', data.new_type_id);
                  }
                },
              });
            },
          },
        ],
        onSelect(newType) {
          const $this = $(this);
          const postData = {type_id: newType ? newType.id : null};

          return patchObject($this.data('href'), $this.data('method'), postData).then(function() {
            const label = newType ? newType.title : $T.gettext('No type');
            $this.find('.label').text(label);
          });
        },
      });
    });
  }
})(window);
