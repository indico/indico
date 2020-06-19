// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global showUndoWarning:false, setupListGenerator:false, setupSearchBox:false */
/* global reloadManagementAttachmentInfoColumn:false, ajaxDialog:true, handleAjaxError:true */
/* global enableIfChecked:true */

import fileTypesURL from 'indico-url:event_editing.api_file_types';
import paperInfoURL from 'indico-url:papers.api_paper_details';

import _ from 'lodash';
import moment from 'moment';
import React from 'react';
import ReactDOM from 'react-dom';

import 'indico/modules/events/util/types_dialog';
import EditableSubmissionButton from 'indico/modules/events/editing/editing/EditableSubmissionButton';
import {$T} from 'indico/utils/i18n';
import {camelizeKeys} from 'indico/utils/case';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import PublicationSwitch from './PublicationSwitch';

(function(global) {
  global.setupEditableSubmissionButton = async function setupEditableSubmissionButton() {
    const editableSubmissionButton = document.querySelector('#editable-submission-button');
    if (!editableSubmissionButton) {
      return;
    }
    const availableTypes = JSON.parse(editableSubmissionButton.dataset.availableTypes);
    const {eventId, contributionId, contributionCode} = editableSubmissionButton.dataset;

    let fileTypeResponses, paperInfoResponse, lastRevFiles;
    try {
      [fileTypeResponses, paperInfoResponse] = await Promise.all([
        Promise.all(
          availableTypes.map(type => indicoAxios.get(fileTypesURL({confId: eventId, type})))
        ),
        indicoAxios.get(paperInfoURL({confId: eventId, contrib_id: contributionId}), {
          validateStatus: status => (status >= 200 && status < 300) || status === 404,
        }),
      ]);
    } catch (e) {
      handleAxiosError(e);
      return;
    }
    const fileTypes = _.fromPairs(
      fileTypeResponses.map((response, index) => [
        availableTypes[index],
        camelizeKeys(response.data),
      ])
    );

    if (paperInfoResponse) {
      const {isInFinalState, lastRevision} = camelizeKeys(paperInfoResponse.data);
      if (isInFinalState && lastRevision) {
        lastRevFiles = lastRevision.files;
      }
    }

    ReactDOM.render(
      <EditableSubmissionButton
        fileTypes={fileTypes}
        eventId={+eventId}
        contributionId={+contributionId}
        contributionCode={contributionCode}
        uploadableFiles={lastRevFiles}
      />,
      editableSubmissionButton
    );
  };

  function setupPublicationButton() {
    const element = document.querySelector('#pub-switch');
    ReactDOM.render(<PublicationSwitch eventId={element.dataset.eventId} />, element);
  }

  global.setupContributionConfig = function setupContributionConfig() {
    setupPublicationButton();
  };

  function setupTableSorter(selector) {
    $(selector).tablesorter({
      cssAsc: 'header-sort-asc',
      cssDesc: 'header-sort-desc',
      cssInfoBlock: 'avoid-sort',
      headerTemplate: '',
      sortList: [[1, 0]],
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

  function setupSessionPicker(createURL, timetableRESTURL) {
    const $contributionList = $('#contribution-list');
    $contributionList.on('click', '.session-item-picker', function() {
      $(this).itempicker({
        filterPlaceholder: $T.gettext('Filter sessions'),
        containerClasses: 'session-item-container',
        items: $contributionList.find('table').data('session-items'),
        footerElements: [
          {
            title: $T.gettext('Assign new session'),
            onClick(itemPicker) {
              ajaxDialog({
                title: $T.gettext('Add new session'),
                url: createURL,
                onClose(data) {
                  if (data) {
                    $('.session-item-picker').each(function() {
                      const $this = $(this);
                      if ($this.data('indicoItempicker')) {
                        $this.itempicker('updateItemList', data.sessions);
                      } else {
                        $contributionList.find('table').data('session-items', data.sessions);
                      }
                    });
                    itemPicker.itempicker('selectItem', data.new_session_id);
                  }
                },
              });
            },
          },
        ],
        onSelect(newSession, oldSession) {
          const $this = $(this);
          const styleObject = $this[0].style;
          const postData = {session_id: newSession ? newSession.id : null};

          return patchObject($this.data('href'), $this.data('method'), postData).then(function(
            data
          ) {
            const label = newSession ? newSession.title : $T.gettext('No session');
            $this.find('.label').text(label);

            if (!newSession) {
              styleObject.removeProperty('color');
              styleObject.removeProperty('background');
            } else {
              styleObject.setProperty('color', `#${newSession.colors.text}`, 'important');
              styleObject.setProperty(
                'background',
                `#${newSession.colors.background}`,
                'important'
              );
            }

            if (data.unscheduled) {
              const row = $this.closest('tr');
              const startDateCol = row.find('td.start-date > .vertical-aligner');
              const oldLabelHtml = startDateCol.children().detach();

              startDateCol.html($('<em>', {text: $T.gettext('Not scheduled')}));
              /* eslint-disable max-len */
              showUndoWarning(
                $T
                  .gettext("'{0}' has been unscheduled due to the session change.")
                  .format(row.data('title')),
                $T.gettext('Undo successful! Timetable entry and session have been restored.'),
                function() {
                  return patchObject(timetableRESTURL, 'POST', data.undo_unschedule).then(function(
                    data
                  ) {
                    oldLabelHtml
                      .filter('.label')
                      // eslint-disable-next-line prefer-template
                      .text(' ' + moment.utc(data.start_dt).format('DD/MM/YYYY HH:mm'));
                    startDateCol.html(oldLabelHtml);
                    $this.itempicker('selectItem', oldSession ? oldSession.id : null);
                  });
                }
              );
            }
          });
        },
      });
    });
  }

  function setupTrackPicker(createURL) {
    const $contributionList = $('#contribution-list');
    $contributionList.on('click', '.track-item-picker', function() {
      $(this).itempicker({
        filterPlaceholder: $T.gettext('Filter tracks'),
        containerClasses: 'track-item-container',
        uncheckedItemIcon: '',
        items: $contributionList.find('table').data('track-items'),
        footerElements: [
          {
            title: $T.gettext('Add new track'),
            onClick(trackItemPicker) {
              ajaxDialog({
                title: $T.gettext('Add new track'),
                url: createURL,
                onClose(data) {
                  if (data) {
                    $('.track-item-picker').each(function() {
                      const $this = $(this);
                      if ($this.data('indicoItempicker')) {
                        $this.itempicker('updateItemList', data.tracks);
                      } else {
                        $contributionList.find('table').data('track-items', data.tracks);
                      }
                    });
                    trackItemPicker.itempicker('selectItem', data.new_track_id);
                  }
                },
              });
            },
          },
        ],
        onSelect(newTrack) {
          const $this = $(this);
          const postData = {track_id: newTrack ? newTrack.id : null};

          return patchObject($this.data('href'), $this.data('method'), postData).then(function() {
            const label = newTrack ? newTrack.title : $T.gettext('No track');
            $this.find('.label').text(label);
          });
        },
      });
    });
  }

  function setupStartDateQBubbles() {
    $('.js-contrib-start-date').each(function() {
      const $this = $(this);

      $this.ajaxqbubble({
        url: $this.data('href'),
        qBubbleOptions: {
          style: {
            classes: 'qbubble-contrib-start-date qtip-allow-overflow',
          },
        },
      });
    });
  }

  function setupDurationQBubbles() {
    $('.js-contrib-duration').each(function() {
      const $this = $(this);

      $this.ajaxqbubble({
        url: $this.data('href'),
        qBubbleOptions: {
          style: {
            classes: 'qbubble-contrib-duration',
          },
        },
      });
    });
  }

  global.setupContributionList = function setupContributionList(options) {
    options = $.extend(
      {
        createSessionURL: null,
        createTrackURL: null,
        timetableRESTURL: null,
      },
      options
    );

    const filterConfig = {
      itemHandle: 'tr',
      listItems: '#contribution-list tbody tr',
      term: '#search-input',
      state: '#filtering-state',
      placeholder: '#filter-placeholder',
    };

    $('.list-section [data-toggle=dropdown]')
      .closest('.toolbar')
      .dropdown();
    setupTableSorter('#contribution-list .tablesorter');
    setupSessionPicker(options.createSessionURL, options.timetableRESTURL);
    setupTrackPicker(options.createTrackURL);
    setupStartDateQBubbles();
    setupDurationQBubbles();
    enableIfChecked('#contribution-list', 'input[name=contribution_id]', '.js-enable-if-checked');

    const applySearchFilters = setupListGenerator(filterConfig);

    $('#contribution-list')
      .on('indico:htmlUpdated', function() {
        setupTableSorter('#contribution-list .tablesorter');
        setupStartDateQBubbles();
        setupDurationQBubbles();
        _.defer(applySearchFilters);
      })
      .on('attachments:updated', function(evt) {
        const target = $(evt.target);
        reloadManagementAttachmentInfoColumn(target.data('locator'), target.closest('td'));
      });
    $('.js-submit-form').on('click', function(e) {
      e.preventDefault();
      const $this = $(this);
      if (!$this.hasClass('disabled')) {
        $('#contribution-list form')
          .attr('action', $this.data('href'))
          .submit();
      }
    });
  };

  global.setupSubContributionList = function setupSubContributionList() {
    $('#subcontribution-list [data-toggle=dropdown]')
      .closest('.toolbar')
      .dropdown();
    setupTableSorter('#subcontribution-list .tablesorter');
    enableIfChecked(
      '#subcontribution-list',
      'input[name=subcontribution_id]',
      '#subcontribution-list .js-enable-if-checked'
    );

    $('#subcontribution-list td.subcontribution-title').on('mouseenter', function() {
      const $this = $(this);
      if (this.offsetWidth < this.scrollWidth && !$this.attr('title')) {
        $this.attr('title', $this.text());
      }
    });
    $('#subcontribution-list').on('attachments:updated', function(evt) {
      const target = $(evt.target);
      reloadManagementAttachmentInfoColumn(target.data('locator'), target.closest('td'));
    });

    $('#subcontribution-list table').sortable({
      items: '.js-sortable-subcontribution-row',
      handle: '.js-sort-handle',
      placeholder: 'sortable-placeholder',
      tolerance: 'pointer',
      distance: 10,
      axis: 'y',
      containment: '#subcontribution-list table',
      start(e, ui) {
        ui.placeholder.height(ui.helper.outerHeight());
      },
      update(e, ui) {
        const self = $(this);

        $.ajax({
          url: ui.item.data('sort-url'),
          method: 'POST',
          data: {subcontrib_ids: self.sortable('toArray')},
          error: handleAjaxError,
        });
      },
    });
  };

  global.setupEventDisplayContributionList = function setupEventDisplayContributionList() {
    const filterConfig = {
      itemHandle: 'div.contribution-row',
      listItems: '#display-contribution-list div.contribution-row',
      term: '#search-input',
      state: '#filtering-state',
      placeholder: '#filter-placeholder',
    };

    const applySearchFilters = setupListGenerator(filterConfig);
    applySearchFilters();
  };

  global.setupEventDisplayAuthorList = function setupEventDisplayAuthorList() {
    const filterConfig = {
      itemHandle: '.author-list > li',
      listItems: '.author-list > li',
      term: '#search-input',
      state: '#filtering-state',
      placeholder: '#filter-placeholder',
    };

    const applySearchFilters = setupSearchBox(filterConfig);
    applySearchFilters();
  };
})(window);
