// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global ajaxDialog */

import React from 'react';
import ReactDOM from 'react-dom';

import {ManageNotes} from 'indico/react/components';

import 'indico/custom_elements/ind_collapsible';
import 'indico/custom_elements/ind_with_tooltip';

import './util/list_generator';
import './util/static_filters';
import './util/social';
import './favorite';

(function() {
  function setupEventDisplay() {
    function openAjaxDialog($element) {
      ajaxDialog({
        title: $element.data('title'),
        subtitle: $element.data('subtitle'),
        url: $element.data('href'),
        confirmCloseUnsaved: true,
        onClose(data, customData) {
          if (data || customData) {
            location.reload();
          }
        },
      });
    }

    const containers = document.querySelectorAll('.manage-notes-container');
    containers.forEach(container => {
      ReactDOM.render(
        React.createElement(ManageNotes, {
          icon: container.dataset.icon !== undefined,
          title: container.dataset.title,
          compile: container.CDATA_SECTION_NODE.icon !== undefined,
          apiURL: container.dataset.apiUrl,
          imageUploadURL: container.dataset.imageUploadUrl,
          getNoteURL: container.dataset.getNoteUrl,
        }),
        container
      );
    });

    $('.js-go-to-day')
      .dropdown({
        always_listen: true,
      })
      .find('li a')
      .on('menu_select', function() {
        const anchor = $(this).attr('href');
        $('body, html').animate(
          {
            scrollTop: $(anchor).offset().top,
          },
          {
            duration: 700,
            complete() {
              location.href = anchor;
            },
          }
        );
        return false;
      });

    const selectors = [
      '.notes-compile',
      '.contribution-edit',
      '.subcontribution-edit',
      '.subcontributions-edit',
    ].join(', ');
    $('body').on('click', selectors, function(e) {
      e.preventDefault();
      openAjaxDialog($(this));
      return false;
    });

    $(document).ready(function() {
      $('h1, .item-description, .timetable-title').mathJax();
    });
  }

  function toggleNote(element, visible, immediate) {
    // Note for event
    let note = element.closest('.event-note-section');
    // Note for other elements
    if (note.length === 0) {
      note = element.closest('li').find('.note-area-wrapper');
    }
    const content = note.hasClass('togglable') ? note : note.find('.togglable');
    if (immediate) {
      content.toggle(visible);
    } else {
      content[visible === undefined ? 'slideToggle' : visible ? 'slideDown' : 'slideUp']();
    }
  }

  $(document).ready(function() {
    $('.event-service-row > .trigger').on('click', function() {
      const toggler = $(this);
      toggler.siblings('.event-service-details').slideToggle({
        start() {
          toggler.toggleClass('icon-expand icon-collapse');
        },
        duration: 'fast',
      });
    });

    $('.event-service-row-toggle').on('click', function(e) {
      e.preventDefault();
      const toggler = $(this);
      const togglerButton = $(this)
        .parent()
        .siblings('.trigger');
      toggler
        .parent()
        .siblings('.event-service-details')
        .slideToggle({
          start() {
            togglerButton.toggleClass('icon-expand icon-collapse');
          },
          duration: 'fast',
        });
    });

    $('a.js-show-note-toggle').on('click', function(e) {
      e.preventDefault();
      toggleNote($(this));
    });

    $('input.js-toggle-note-cb').on('change', function(e, immediate) {
      toggleNote($(this), this.checked, immediate);
    });

    $('input.js-toggle-note-cb').trigger('change', [true]);

    setupEventDisplay();
  });
})();
