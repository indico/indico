// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global setupSearchBox:false, strnatcmp:false */

import 'selectize';
import 'selectize/dist/css/selectize.css';
import 'selectize/dist/css/selectize.default.css';

import 'indico/modules/events/util/list_generator';
import 'indico/modules/events/util/static_filters';

import './badges';

(function(global) {
  global.setupEventManagementActionMenu = function setupEventManagementActionMenu() {
    $('#event-action-move-to-category').on('click', function(evt) {
      evt.preventDefault();

      var $this = $(this);
      $('<div>').categorynavigator({
        openInDialog: true,
        actionOn: {
          categoriesWithSubcategories: {
            disabled: true,
          },
          categoriesWithoutEventCreationRights: {
            disabled: true,
          },
          categories: {
            disabled: true,
            ids: [$this.data('category-id')],
          },
        },
        onAction: function(category) {
          var msg = $T
            .gettext(
              'You are about to move the event to the category "{0}". Are you sure you want to proceed?'
            )
            .format(category.title);
          confirmPrompt(msg, $T.gettext('Move event')).then(function() {
            $.ajax({
              url: $this.data('href'),
              type: 'POST',
              data: {target_category_id: category.id},
              error: handleAjaxError,
              success: function(data) {
                if (data.success) {
                  location.reload();
                }
              },
            });
          });
        },
      });
    });

    $('#event-action-menu-clones-target').qbubble({
      content: {
        text: $('#event-action-menu-clones'),
      },
    });

    $('#event-action-menu-actions-target').qbubble({
      content: {
        text: $('#event-action-menu-actions'),
      },
      style: {
        classes: 'qtip-allow-overflow',
      },
    });

    var selectors = [
      '#event-action-menu-actions button:not(.js-dropdown)',
      '#event-action-menu-actions a:not(.disabled)',
    ];
    $(selectors.join(', ')).on('click', function() {
      $('#event-action-menu-actions-target').qbubble('hide');
    });
  };

  function refreshPersonFilters() {
    $('#person-filters ul > li').removeClass('enabled');
    var personRows = $('.js-event-person-list tr[data-person-roles]');
    var filters = $('.js-event-person-list [data-filter]:checked')
      .map(function() {
        var $this = $(this);
        $this.closest('li').addClass('enabled');
        return $this.data('filter');
      })
      .get();

    var visibleEntries = personRows.filter(function() {
      var $this = $(this);

      return _.any(filters, function(filterName) {
        return $this.data('person-roles')[filterName];
      });
    });

    personRows.addClass('hidden');
    visibleEntries.removeClass('hidden');
    $('.js-event-person-list').trigger('indico:syncEnableIfChecked');
  }

  function toggleResetBtn() {
    var isInitialState =
      $('#person-filters [data-filter]:checked').length ===
      $('#person-filters [data-filter]:not(#filter-no-account)').length;
    $('.js-reset-role-filter').toggleClass('disabled', isInitialState);
  }

  function initTooltip() {
    $('.js-show-regforms').qtip({
      content: {
        text: function() {
          return $(this).data('title');
        },
      },
      hide: {
        delay: 100,
        fixed: true,
      },
    });
  }

  global.setupEventPersonsList = function setupEventPersonsList(options) {
    options = $.extend(
      {
        hasNoAccountFilter: false,
      },
      options
    );

    var filterConfig = {
      itemHandle: 'tr',
      listItems: '#event-participants-list tbody tr:not(.hidden)',
      term: '#search-input',
      state: '#filtering-state',
      placeholder: '#filter-placeholder',
    };
    var applySearchFilters = setupSearchBox(filterConfig);

    enableIfChecked(
      '.js-event-person-list',
      '.select-row:visible',
      '.js-event-person-list .js-requires-selected-row'
    );
    if ($('.js-event-person-list').closest('.ui-dialog').length) {
      $('.js-event-person-list [data-toggle=dropdown]')
        .closest('.toolbar')
        .dropdown();
    }
    $('.js-event-person-list [data-filter]').on('click', refreshPersonFilters);

    $('.js-event-person-list td').on('mouseenter', function() {
      var $this = $(this);
      if (this.offsetWidth < this.scrollWidth && !$this.attr('title')) {
        $this.attr('title', $this.text());
      }
    });

    $('.js-event-person-list .tablesorter').tablesorter({
      cssAsc: 'header-sort-asc',
      cssDesc: 'header-sort-desc',
      headerTemplate: '',
      sortList: [[1, 0]],
    });

    var $roleLabels = $('.js-event-person-list .roles-column > span');
    $roleLabels.qbubble({
      show: {
        event: 'mouseover',
      },
      hide: {
        fixed: true,
        delay: 100,
        event: 'mouseleave',
      },
      position: {
        my: 'left center',
        at: 'right center',
      },
      content: {
        text: function() {
          var $this = $(this);
          var html = $('<div>');
          var role = $('<strong>', {text: $(this).data('role-name')});
          html.append(role);
          if ($this.is('.js-count-label')) {
            var list = $('<ul>', {class: 'qbubble-item-list'});
            var items = _.values($this.data('items')).sort(function(a, b) {
              return strnatcmp(a.title.toLowerCase(), b.title.toLowerCase());
            });

            $.each(items, function() {
              var item = $('<li>');
              if (this.url) {
                item.append($('<a>', {text: this.title, href: this.url}));
              } else {
                item.text(this.title);
              }
              list.append(item);
            });
            html.append(list);
          }

          return html;
        },
      },
    });

    // Sets background color of custom role labels based on their font color
    $roleLabels.filter('.custom').each(function() {
      var $this = $(this);
      $this.css('background-color', $.Color($this.css('color')).alpha(0.1));
    });

    if (options.hasNoAccountFilter) {
      $('.js-event-person-list [data-filter]:not(#filter-no-account)').on('change', function() {
        $('#filter-no-account').prop('checked', false);
        refreshPersonFilters();
        applySearchFilters();
      });
      $('#filter-no-account').on('change', function() {
        if (this.checked) {
          $('.js-event-person-list [data-filter]:checked:not(#filter-no-account)').prop(
            'checked',
            false
          );
        }
        refreshPersonFilters();
        applySearchFilters();
      });
    }

    initTooltip();

    var $personFilters = $('#person-filters');
    // Sets background color of role filter items based on their colored squared color
    $personFilters.find('li .colored-square').each(function() {
      var $this = $(this);
      $this.closest('li').css('background-color', $.Color($this.css('color')).alpha(0.1));
    });

    // Reset role filters
    $personFilters.find('.js-reset-role-filter').on('click', function() {
      $('.js-event-person-list [data-filter]').each(function() {
        var $this = $(this);
        $this.prop('checked', !$this.is('#filter-no-account'));
        $this.parent().toggleClass('enabled', !$this.is('#filter-no-account'));
      });
      refreshPersonFilters();
      applySearchFilters();
      toggleResetBtn();
    });

    // Allows to click in the whole list item area to enable/disable role filters
    $personFilters.find('li label').on('click', function(evt) {
      evt.preventDefault();
    });
    $personFilters.find('li').on('click', function() {
      var $checkbox = $(this).find('[data-filter]');
      $checkbox.prop('checked', !$checkbox.prop('checked')).trigger('change');
      toggleResetBtn();
    });

    $('#event-participants-list').on('indico:htmlUpdated', initTooltip);
  };

  global.showUndoWarning = function showUndoWarning(message, feedbackMessage, actionCallback) {
    cornerMessage({
      message: message,
      progressMessage: $T.gettext('Undoing previous operation...'),
      feedbackMessage: feedbackMessage,
      actionLabel: $T.gettext('Undo'),
      actionCallback: actionCallback,
      duration: 10000,
      feedbackDuration: 4000,
      class: 'warning',
    });
  };

  global.handleSelectedRowHighlight = function handleSelectedRowHighlight(trigger) {
    var $obj = $('table.i-table input.select-row').on('change', function() {
      $(this)
        .closest('tr')
        .toggleClass('selected', this.checked);
    });

    if (trigger) {
      $obj.trigger('change');
    }
  };

  global.showThemeSettingsForm = function showThemeSettingsForm(options) {
    options = $.extend(
      true,
      {
        formUrl: null,
        themeFieldId: null,
        lastFieldId: null,
      },
      options
    );
    $('#' + options.themeFieldId).on('change', function() {
      $.ajax({
        url: options.formUrl,
        data: {
          theme: $(this).val(),
        },
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success: function(data) {
          var lastField = $('#' + options.lastFieldId);
          lastField.nextAll(':not(.form-group-footer)').remove();
          if (data.html) {
            lastField.after(data.html);
          }
          if (data.js) {
            $('body').append(data.js);
          }
        },
      });
    });
  };
})(window);
