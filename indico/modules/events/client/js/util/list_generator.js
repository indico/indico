// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global setupSearchBox:false, handleRowSelection:false, setupTableSorter:false */

(function(global) {
  function colorizeFilter(filter) {
    var dropdown = filter.find('.i-dropdown');
    filter.toggleClass('active highlight', dropdown.find(':checked').length > 0);
  }

  function colorizeActiveFilters() {
    $('.list-filter .filter').each(function() {
      colorizeFilter($(this));
    });
  }

  function setupStaticURLGeneration() {
    $('.js-static-url').on('click', function() {
      var $this = $(this);
      $.ajax({
        method: 'POST',
        url: $this.data('href'),
        error: handleAjaxError,
        complete: IndicoUI.Dialogs.Util.progress(),
        success: function(data) {
          $this.copyURLTooltip(data.url);
        },
      });
    });
  }

  global.handleRowSelection = function(trigger) {
    var $obj = $('table.i-table input.select-row').on('change', function() {
      $(this)
        .closest('tr')
        .toggleClass('selected', this.checked);
      $('.js-requires-selected-row').toggleClass(
        'disabled',
        !$('.list input:checkbox:checked').length
      );
    });

    if (trigger) {
      $obj.trigger('change');
    }
  };

  global.setupTableSorter = function() {
    $('.list .tablesorter').tablesorter({
      cssAsc: 'header-sort-asc',
      cssDesc: 'header-sort-desc',
      headerTemplate: '',
      headers: {
        0: {sorter: false},
      },
    });
  };

  global.setupListFilter = function() {
    var visibleItems = $('#visible-items');
    var hasColumnSelector = !!$('#visible-items').length;

    $('.list-filter .filter').each(function() {
      var $filter = $(this).parent();
      var isOnlyFilter = !!$filter.find('[data-only-filter]').length;
      $filter.dropdown({selector: "a[data-toggle='dropdown']", relative_to: $filter});
      if (!hasColumnSelector || isOnlyFilter) {
        $filter.find('.title-wrapper').on('click', function(evt) {
          $filter.find("a[data-toggle='dropdown']").trigger('click');
          evt.stopPropagation();
        });
      }
    });

    colorizeActiveFilters();
    $('.list-filter-dialog .toolbar').dropdown();

    $('.title-wrapper').on('click', function(evt) {
      if ($(evt.target).hasClass('filter')) {
        return;
      }
      var $this = $(this);
      var field = $this.closest('.title-wrapper');
      var fieldId = field.data('id');
      var visibilityIcon = field.find('.visibility');
      var enabled = visibilityIcon.hasClass('enabled');
      var isOnlyFilter = !!$this.parent().find('[data-only-filter]').length;

      if (hasColumnSelector && !isOnlyFilter) {
        var itemsData = JSON.parse(visibleItems.val());
        if (enabled) {
          itemsData.splice(itemsData.indexOf(fieldId), 1);
        } else {
          itemsData.push(fieldId);
        }

        visibilityIcon.toggleClass('enabled', !enabled);
        field.toggleClass('striped', enabled);
        visibleItems.val(JSON.stringify(itemsData)).trigger('change');
      }
    });

    if (hasColumnSelector) {
      $('.title-wrapper').each(function() {
        var field = $(this);
        var fieldId = field.data('id');
        var itemsData = JSON.parse(visibleItems.val());
        var isOnlyFilter = !!field.parent().find('[data-only-filter]').length;

        if (!isOnlyFilter) {
          if (itemsData.indexOf(fieldId) !== -1) {
            field.find('.visibility').addClass('enabled');
          } else {
            field.addClass('striped');
          }
        }
      });
    }

    $('.js-reset-btn').on('click', function() {
      $('.list-filter input:checkbox:checked')
        .prop('checked', false)
        .trigger('change');
      $('.js-clear-filters-message').show({
        done: function() {
          var $this = $(this);
          setTimeout(function() {
            $this.slideUp();
          }, 4000);
        },
      });
    });

    $('.list-filter input:checkbox').on('change', function() {
      colorizeFilter($(this).closest('.filter'));
    });

    $('.list-filter .title').on('mouseover', function() {
      var title = $(this);
      // Show a qtip if the text is ellipsized
      if (this.offsetWidth < this.scrollWidth) {
        title.qtip({hide: 'mouseout', content: title.text(), overwrite: false}).qtip('show');
      }
    });

    $('#list-filter-select-all').on('click', function() {
      $('.list-filter-dialog .visibility:not(.enabled)').trigger('click');
    });

    $('#list-filter-select-none').on('click', function() {
      $('.list-filter-dialog .visibility.enabled').trigger('click');
    });
  };

  global.setupListGenerator = function(filterConfig) {
    var applySearchFilters;
    if (filterConfig) {
      applySearchFilters = setupSearchBox(filterConfig);
    }
    setupStaticURLGeneration();
    handleRowSelection(false);
    setupTableSorter();

    $('.list').on('indico:htmlUpdated', function() {
      handleRowSelection(true);
      setupTableSorter();
    });

    $('.list .toolbar').dropdown();

    $('#select-all').on('click', function() {
      $('table.i-table input.select-row')
        .prop('checked', true)
        .trigger('change');
    });

    $('#select-none').on('click', function() {
      $('table.i-table input.select-row')
        .prop('checked', false)
        .trigger('change');
    });

    $('.change-columns-width').on('click', function() {
      $('.js-list-table-wrapper').toggleClass('scrollable');
      $('.change-columns-width').toggleClass('active');
    });

    $('.js-submit-list-form').on('click', function(e) {
      e.preventDefault();
      var $this = $(this);
      if (!$this.hasClass('disabled')) {
        $('.list form')
          .attr('action', $this.data('href'))
          .submit();
      }
    });

    $('.list .toolbar').on('click', '.disabled', function(e) {
      e.preventDefault();
      e.stopPropagation();
    });

    $('.state-badge').qbubble({
      show: {
        event: 'mouseover',
      },
      hide: {
        fixed: true,
        delay: 100,
        event: 'mouseleave',
      },
      position: {
        my: 'bottom center',
        at: 'top center',
      },
      content: {
        attr: 'data-qbubble',
      },
    });

    return applySearchFilters;
  };

  global.getSelectedRows = function() {
    return $('.list input:checkbox:checked')
      .map(function() {
        return $(this).val();
      })
      .get();
  };
})(window);
