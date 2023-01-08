// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global paginatedSelectAll:false, handleAjaxError:false, cornerMessage:false,
          enableIfChecked:false, build_url:false, ajaxDialog:false, updateHtml:false */

import _ from 'lodash';
import React from 'react';
import ReactDOM from 'react-dom';

import {SingleEventMove, BulkEventMove} from 'indico/modules/events/management/EventMove';
import {showUserSearch} from 'indico/react/components/principals/imperative';
import {$T} from 'indico/utils/i18n';
import {natSortCompare} from 'indico/utils/sort';

(function(global) {
  // Category cache
  const _categories = {};

  global.setupCategoryMoveButton = function setupCategoryMoveButton(parentCategoryId) {
    if (parentCategoryId) {
      _fetchSourceCategory(parentCategoryId);
    }
    $('.js-move-category').on('click', function() {
      const $this = $(this);
      _moveCategories(
        [$this.data('categoryId')],
        _categories[parentCategoryId],
        $this.data('href')
      );
    });
  };

  global.setupCategoryTable = function setupCategoryTable(categoryId) {
    _fetchSourceCategory(categoryId);
    const $table = $('table.category-management');
    const $tbody = $table.find('tbody');
    const $bulkDeleteButton = $('.js-bulk-delete-category');
    const $bulkMoveButton = $('.js-bulk-move-category');
    const categoryRowSelector = 'tr[data-category-id]';
    const checkboxSelector = 'input[name=category_id]';

    $('.js-sort-categories').on('click', function() {
      const sortOrder = $(this).data('sort-order');
      const currentOrder = getSortedCategories();
      function undo() {
        restoreCategoryOrder(currentOrder);
        return setOrderAjax(currentOrder);
      }
      sortCategories(sortOrder);
      setOrderAjax(getSortedCategories());
      cornerMessage({
        actionLabel: $T.gettext('Undo'),
        actionCallback: undo,
        feedbackMessage: $T.gettext('The category order has been restored.'),
        duration: 10000,
        message: $T.gettext('The category list has been sorted.'),
      });
    });

    $bulkMoveButton.on('click', function(evt) {
      const $this = $(this);
      evt.preventDefault();
      if ($this.hasClass('disabled')) {
        return;
      }
      _moveCategories(getSelectedCategories(), _categories[categoryId], $this.data('href'));
    });

    $table.find('.js-move-category').on('click', function() {
      const $this = $(this);
      _moveCategories([$this.data('categoryId')], _categories[categoryId], $this.data('href'));
    });

    $table.find('.js-delete-category').on('indico:confirmed', function(evt) {
      evt.preventDefault();
      const $this = $(this);
      $.ajax({
        url: $this.data('href'),
        method: 'POST',
        error: handleAjaxError,
        success(data) {
          $this.closest(categoryRowSelector).remove();
          updateCategoryDeleteButton(data.is_parent_empty);
        },
      });
    });

    enableIfChecked($tbody, checkboxSelector, $bulkDeleteButton, function($checkboxes) {
      return $checkboxes.filter(':not([data-is-empty=true])').length === 0;
    });
    $bulkDeleteButton.on('click', bulkDeleteCategories).qtip({
      suppress: false,
      content: {
        text: getBulkDeleteButtonTooltipContent,
      },
    });

    enableIfChecked($tbody, checkboxSelector, $bulkMoveButton);
    $bulkMoveButton.qtip({
      suppress: false,
      content: {
        text: getBulkMoveButtonTooltipContent,
      },
    });

    $tbody.sortable({
      axis: 'y',
      containment: 'parent',
      cursor: 'move',
      handle: '.js-handle',
      items: '> tr',
      tolerance: 'pointer',
      update() {
        setOrderAjax(getSortedCategories());
      },
    });

    function getSortedCategories() {
      return $tbody
        .find(categoryRowSelector)
        .map(function() {
          return $(this).data('category-id');
        })
        .toArray();
    }

    function restoreCategoryOrder(order) {
      $.each(order, function(index, id) {
        $tbody
          .find(`[data-category-id=${id}]`)
          .not('.js-move-category')
          .detach()
          .appendTo($tbody);
      });
    }

    function compareCategories(a, b) {
      const cmp = natSortCompare(a.title.toLowerCase(), b.title.toLowerCase());
      if (cmp === 0) {
        return a.id < b.id ? -1 : 1;
      }
      return cmp;
    }

    function sortCategories(sortOrder) {
      $tbody
        .find(categoryRowSelector)
        .sort(function(a, b) {
          [a, b] = [$(a), $(b)];
          return (
            sortOrder *
            compareCategories(
              {title: a.data('category-title'), id: a.data('category-id')},
              {title: b.data('category-title'), id: b.data('category-id')}
            )
          );
        })
        .detach()
        .appendTo($tbody);
    }

    function setOrderAjax(order) {
      return $.ajax({
        url: $table.data('sort-url'),
        method: 'POST',
        data: JSON.stringify({
          categories: order,
        }),
        dataType: 'json',
        contentType: 'application/json',
        error: handleAjaxError,
      });
    }

    function updateCategoryDeleteButton(enabled) {
      if (enabled) {
        $('.banner .js-delete-category')
          .removeClass('disabled')
          .attr('title', $T.gettext('Delete category'));
      } else {
        $('.banner .js-delete-category')
          .addClass('disabled')
          .attr('title', $T.gettext('This category cannot be deleted because it is not empty.'));
      }
    }

    function getBulkDeleteButtonTooltipContent() {
      const $checked = getSelectedRows();
      if ($checked.length) {
        if ($bulkDeleteButton.hasClass('disabled')) {
          return $T.gettext(
            'At least one selected category cannot be deleted because it is not empty.'
          );
        } else {
          return $T
            .ngettext(
              'Delete the selected category',
              'Delete {0} selected categories',
              $checked.length
            )
            .format($checked.length);
        }
      } else {
        return $T.gettext('Select the categories to delete first.');
      }
    }

    function bulkDeleteCategories() {
      const $selectedRows = getSelectedRows();
      ajaxDialog({
        url: $table.data('bulk-delete-url'),
        method: 'POST',
        title: $T.gettext('Delete categories'),
        data: {
          category_id: getSelectedCategories(),
        },
        onClose(data) {
          if (data && data.success) {
            // Prevent other categories from being selected when someone reloads
            // the page after deleting a selected category.
            $selectedRows.find('input[type=checkbox]').prop('checked', false);
            $selectedRows.remove();
            updateCategoryDeleteButton(data.is_empty);
          }
        },
      });
    }

    function getBulkMoveButtonTooltipContent() {
      const $checked = getSelectedRows();
      if ($checked.length) {
        return $T
          .ngettext(
            'Move the selected category',
            'Move the {0} selected categories',
            $checked.length
          )
          .format($checked.length);
      } else {
        return $T.gettext('Select the categories to move first.');
      }
    }

    function getSelectedCategories() {
      return $table
        .find(categoryRowSelector)
        .find(`${checkboxSelector}:checked`)
        .map(function() {
          return this.value;
        })
        .toArray();
    }

    function getSelectedRows() {
      return $table.find(categoryRowSelector).has(`${checkboxSelector}:checked`);
    }
  };

  global.setupCategoryEventList = function setupCategoryEventList(categoryId) {
    const isEverythingSelected = paginatedSelectAll({
      containerSelector: '#event-management',
      checkboxSelector: 'input:checkbox[name=event_id]',
      allSelectedSelector: 'input:checkbox[name=all_selected]',
      selectionMessageSelector: '#selection-message',
      totalRows: $('#event-management').data('total'),
      messages: {
        allSelected(total) {
          return $T
            .ngettext('*', 'All {0} events in this category are currently selected.')
            .format(total);
        },
        pageSelected(selected, total) {
          return $T
            .ngettext(
              'Only {0} out of {1} events is currently selected.',
              'Only {0} out of {1} events are currently selected.',
              selected
            )
            .format(selected, total);
        },
      },
    }).isEverythingSelected;

    _fetchSourceCategory(categoryId);

    [].forEach.call(
      document.querySelectorAll('.js-move-event-to-subcategory-container'),
      moveContainer => {
        ReactDOM.render(
          React.createElement(SingleEventMove, {
            eventId: +moveContainer.dataset.eventId,
            currentCategoryId: categoryId,
            hasPendingMoveRequest: moveContainer.dataset.pendingRequest !== undefined,
            inCategoryManagement: true,
          }),
          moveContainer
        );
      }
    );

    const bulkMoveContainer = document.querySelector('#js-move-events-to-subcategory-container');
    ReactDOM.render(
      React.createElement(BulkEventMove, {
        currentCategoryId: categoryId,
        getEventData: () => {
          const allSelected = isEverythingSelected();
          const eventIds = [].map.call(
            document.querySelectorAll(
              '#event-management input[name=event_id][type=checkbox]:checked'
            ),
            o => o.value
          );
          return {
            allSelected,
            eventIds: allSelected ? null : eventIds,
            eventCount: allSelected ? $('#event-management').data('total') : eventIds.length,
          };
        },
      }),
      bulkMoveContainer
    );

    enableIfChecked('#event-management', 'input[name=event_id]', '.js-enabled-if-checked');
  };

  function _fetchSourceCategory(categoryId) {
    if (_categories[categoryId] === undefined) {
      _categories[categoryId] = categoryId;
      $.ajax({
        url: build_url(Indico.Urls.Categories.info, {category_id: categoryId}),
        dataType: 'json',
        error(xhr) {
          // XXX: Re-enable error handling once we skip retrieving protected parents
          if (xhr.status && xhr.status !== 403) {
            handleAjaxError(xhr);
          }
        },
        success(data) {
          _categories[categoryId] = data;
        },
      });
    }
  }

  function _moveCategories(ids, source, endpoint) {
    const sourceId = _.isObject(source) ? source.category.id : source;
    const data = {category_id: ids};

    $('<div>').categorynavigator({
      category: source,
      confirmation: true,
      openInDialog: true,
      actionButtonText: $T.gettext('Move here'),
      dialogTitle: $T.ngettext('Move category', 'Move categories', ids.length),
      dialogSubtitle: $T
        .ngettext(
          'Select new category parent for the category',
          'Select new category parent for {0} selected categories',
          ids.length
        )
        .format(ids.length),
      actionOn: {
        categoriesDescendingFrom: {
          disabled: true,
          ids,
        },
        categories: {
          disabled: true,
          groups: [
            {
              ids: [sourceId],
              message: $T.ngettext(
                'The category is already here',
                'The selected categories are already here',
                ids.length
              ),
            },
            {
              ids,
              message: $T.ngettext(
                'This is the category you are trying to move',
                'This is one of the categories you are trying to move',
                ids.length
              ),
            },
          ],
        },
      },
      onAction(category) {
        $.ajax({
          url: endpoint,
          type: 'POST',
          data: $.extend({target_category_id: category.id}, data),
          error: handleAjaxError,
          success(data) {
            if (data.success) {
              location.reload();
            }
          },
        });
      },
    });
  }

  function setupRolesToggle() {
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

  function setupRolesButtons() {
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

  global.setupCategoryRolesList = function setupCategoryRolesList() {
    setupRolesToggle();
    setupRolesButtons();
  };
})(window);
