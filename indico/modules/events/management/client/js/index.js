// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global setupSearchBox:false, cornerMessage:false, handleAjaxError:false,
          enableIfChecked:false */

import _ from 'lodash';
import React from 'react';
import ReactDOM from 'react-dom';

import 'indico/modules/events/util/list_generator';
import 'indico/modules/events/util/static_filters';

import './badges';

import {AuthorsListButton} from 'indico/modules/events/persons/AuthorsListButton';
import {EmailContribAbstractRolesButton} from 'indico/modules/events/persons/EmailContribAbstractRolesButton';
import {EmailParticipantRolesButton} from 'indico/modules/events/persons/EmailParticipantRolesButton';
import {$T} from 'indico/utils/i18n';
import {natSortCompare} from 'indico/utils/sort';

import {SingleEventMove, EventPublish} from './EventMove';
import {SeriesManagement} from './SeriesManagement';

(function(global) {
  global.setupEmailButton = function setupEmailButton(field, trigger) {
    const element = document.querySelector(field);
    const {eventId, roleId, personSelector} = element.dataset;
    const extraParams = {};
    if (element.dataset.noAccount !== undefined) {
      extraParams.noAccount = true;
    }
    if (element.dataset.notInvitedOnly !== undefined) {
      extraParams.notInvitedOnly = true;
    }
    ReactDOM.render(
      <EmailParticipantRolesButton
        eventId={+eventId}
        roleId={roleId && +roleId}
        personSelector={personSelector}
        triggerSelector={trigger}
        {...extraParams}
      />,
      element
    );
  };

  global.setupEmailContribAbstractRoles = function setupEmailContribAbstractRoles(
    containerSelector
  ) {
    const element = document.querySelector(containerSelector);
    const {objectContext, idSelector, metadataUrl, previewUrl, sendUrl} = element.dataset;
    ReactDOM.render(
      <EmailContribAbstractRolesButton
        objectContext={objectContext}
        idSelector={idSelector}
        metadataURL={metadataUrl}
        previewURL={previewUrl}
        sendURL={sendUrl}
      />,
      element
    );
  };

  global.setupAuthorsListButton = function setupAuthorsListButton(containerSelector) {
    const element = document.querySelector(containerSelector);
    const {eventId, objectContext, paramsSelector} = element.dataset;
    ReactDOM.render(
      <AuthorsListButton
        eventId={+eventId}
        objectContext={objectContext}
        paramsSelector={paramsSelector}
      />,
      element
    );
  };

  global.setupEventManagementActionMenu = function setupEventManagementActionMenu() {
    const moveContainer = document.querySelector('#event-action-move-container');
    if (moveContainer) {
      ReactDOM.render(
        React.createElement(SingleEventMove, {
          eventId: +moveContainer.dataset.eventId,
          currentCategoryId: +moveContainer.dataset.categoryId,
          hasPendingMoveRequest: moveContainer.dataset.pendingRequest !== undefined,
        }),
        moveContainer
      );
    }

    const manageSeriesContainer = document.querySelector('#event-action-manage-series-container');
    if (manageSeriesContainer) {
      const seriesId =
        manageSeriesContainer.dataset.seriesId !== undefined
          ? +manageSeriesContainer.dataset.seriesId
          : null;
      ReactDOM.render(
        React.createElement(SeriesManagement, {
          eventId: +manageSeriesContainer.dataset.eventId,
          categoryId: +manageSeriesContainer.dataset.categoryId,
          timezone: manageSeriesContainer.dataset.timezone,
          seriesId,
        }),
        manageSeriesContainer
      );
    }

    const publishContainer = document.querySelector('#event-action-publish-container');
    if (publishContainer) {
      ReactDOM.render(
        React.createElement(EventPublish, {
          eventId: +publishContainer.dataset.eventId,
          hasPendingPublishRequest: publishContainer.dataset.pendingRequest !== undefined,
        }),
        publishContainer
      );
    }

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

    const selectors = [
      '#event-action-menu-actions button:not(.js-dropdown)',
      '#event-action-menu-actions a:not(.disabled)',
    ];
    $(selectors.join(', ')).on('click', function() {
      $('#event-action-menu-actions-target').qbubble('hide');
    });
  };

  function refreshPersonFilters() {
    $('#person-filters ul > li').removeClass('enabled');
    const personRows = $('.js-event-person-list tr[data-person-roles]');
    const filters = $('.js-event-person-list [data-filter]:checked')
      .map(function() {
        const $this = $(this);
        $this.closest('li').addClass('enabled');
        return $this.data('filter');
      })
      .get();

    const visibleEntries = personRows.filter(
      (idx, entry) =>
        !filters.length || filters.find(filterName => $(entry).data('person-roles')[filterName])
    );

    personRows.addClass('hidden');
    visibleEntries.removeClass('hidden');
    $('.js-event-person-list').trigger('indico:syncEnableIfChecked');
  }

  function toggleResetBtn() {
    $('.js-reset-role-filter').toggleClass(
      'disabled',
      $('#person-filters [data-filter]:checked').length === 0
    );
  }

  function initTooltip() {
    $('.js-show-regforms').qtip({
      content: {
        text() {
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
        hasNoRegistrationFilter: false,
        hasNoBuiltinRolesFilter: false,
      },
      options
    );

    const filterConfig = {
      itemHandle: 'tr',
      listItems: '#event-participants-list tbody tr:not(.hidden)',
      term: '#search-input',
      state: '#filtering-state',
      placeholder: '#filter-placeholder',
    };
    const applySearchFilters = setupSearchBox(filterConfig);

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
      const $this = $(this);
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

    const $roleLabels = $('.js-event-person-list .roles-column > span');
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
        text() {
          const $this = $(this);
          const html = $('<div>');
          const role = $('<strong>', {text: $(this).data('role-name')});
          html.append(role);
          if ($this.is('.js-count-label')) {
            const list = $('<ul>', {class: 'qbubble-item-list'});
            const items = _.values($this.data('items')).sort(function(a, b) {
              return natSortCompare(a.title.toLowerCase(), b.title.toLowerCase());
            });

            $.each(items, function() {
              const item = $('<li>');
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
      const $this = $(this);
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

    if (options.hasNoRegistrationFilter) {
      $('.js-event-person-list [data-filter]:not(#filter-no-registration)').on(
        'change',
        function() {
          $('#filter-no-registration').prop('checked', false);
          refreshPersonFilters();
          applySearchFilters();
        }
      );
      $('#filter-no-registration').on('change', function() {
        if (this.checked) {
          $('.js-event-person-list [data-filter]:checked:not(#filter-no-registration)').prop(
            'checked',
            false
          );
        }
        refreshPersonFilters();
        applySearchFilters();
      });
    }

    if (options.hasNoBuiltinRolesFilter) {
      $('.js-event-person-list [data-filter]:not(#filter-no-builtin-roles)').on(
        'change',
        function() {
          $('#filter-no-builtin-roles').prop('checked', false);
          refreshPersonFilters();
          applySearchFilters();
        }
      );
      $('#filter-no-builtin-roles').on('change', function() {
        if (this.checked) {
          $('.js-event-person-list [data-filter]:checked:not(#filter-no-builtin-roles)').prop(
            'checked',
            false
          );
        }
        refreshPersonFilters();
        applySearchFilters();
      });
    }

    initTooltip();

    const $personFilters = $('#person-filters');
    // Sets background color of role filter items based on their colored squared color
    $personFilters.find('li .colored-square').each(function() {
      const $this = $(this);
      $this.closest('li').css('background-color', $.Color($this.css('color')).alpha(0.1));
    });

    // Reset role filters
    $personFilters.find('.js-reset-role-filter').on('click', function() {
      $('.js-event-person-list [data-filter]').each(function() {
        const $this = $(this);
        $this.prop('checked', false);
        $this.parent().toggleClass('enabled', false);
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
      const $checkbox = $(this).find('[data-filter]');
      $checkbox.prop('checked', !$checkbox.prop('checked')).trigger('change');
      toggleResetBtn();
    });

    $('#event-participants-list').on('indico:htmlUpdated', initTooltip);
  };

  global.showUndoWarning = function showUndoWarning(message, feedbackMessage, actionCallback) {
    cornerMessage({
      message,
      progressMessage: $T.gettext('Undoing previous operation...'),
      feedbackMessage,
      actionLabel: $T.gettext('Undo'),
      actionCallback,
      duration: 10000,
      feedbackDuration: 4000,
      class: 'warning',
    });
  };

  global.handleSelectedRowHighlight = function handleSelectedRowHighlight(trigger) {
    const $obj = $('table.i-table input.select-row').on('change', function() {
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
    $(`#${options.themeFieldId}`).on('change', function() {
      $.ajax({
        url: options.formUrl,
        data: {
          theme: $(this).val(),
        },
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success(data) {
          const lastField = $(`#${options.lastFieldId}`);
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
