// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global setupListGenerator:false, setupSearchBox:false */

import 'selectize';
import 'selectize/dist/css/selectize.css';
import 'selectize/dist/css/selectize.default.css';

import 'indico/modules/events/reviews';
import 'indico/modules/events/util/types_dialog';

import './boa';

(function(global) {
  global.setupAbstractList = function setupAbstractList() {
    var abstractListContainer = $('#abstract-list');

    var filterConfig = {
      itemHandle: 'tr',
      listItems: '#abstract-list tbody tr',
      term: '#search-input',
      state: '#filtering-state',
      placeholder: '#filter-placeholder',
    };
    var applySearchFilters = setupListGenerator(filterConfig);
    abstractListContainer.on('indico:htmlUpdated', function() {
      abstractListContainer.find('.js-mathjax').mathJax();
      _.defer(applySearchFilters);
    });
  };

  global.setupAbstractEmailTemplatesPage = function setupAbstractEmailTemplatesPage() {
    $('.js-edit-tpl-dropdown')
      .parent()
      .dropdown();
    $('.email-templates > ul').sortable({
      axis: 'y',
      containment: 'parent',
      cursor: 'move',
      distance: 2,
      handle: '.ui-i-box-sortable-handle',
      items: '> li',
      tolerance: 'pointer',
      forcePlaceholderSize: true,
      placeholder: 'regform-section-sortable-placeholder',
      update: function() {
        var $elem = $('.email-templates > ul');
        var sortedList = $elem
          .find('li.email-template')
          .map(function(i, elem) {
            return $(elem).data('id');
          })
          .get();

        $.ajax({
          url: $elem.data('url'),
          method: 'POST',
          contentType: 'application/json',
          data: JSON.stringify({sort_order: sortedList}),
          complete: IndicoUI.Dialogs.Util.progress(),
          error: handleAjaxError,
        });
      },
    });

    $('.email-preview-btn').on('click', function(evt) {
      evt.preventDefault();
      var id = $(this).data('id');
      var $previewBtn = $('#email-preview-btn-' + id);
      if ($previewBtn.data('visible')) {
        $previewBtn.text($T.gettext('Show preview'));
        $('#email-preview-' + id).slideToggle();
        $previewBtn.data('visible', false);
      } else {
        $previewBtn.text($T.gettext('Hide preview'));
        $('#email-preview-' + id).slideToggle();
        $previewBtn.data('visible', true);
      }
    });

    $('#email-template-manager .ui-i-box-sortable-handle').on('mousedown', function() {
      $('.email-preview').hide();
      $('.email-preview-btn')
        .text($T.gettext('Show preview'))
        .data('visible', false);
    });

    $('.js-toggle-stop-on-match').on('click', function(evt) {
      evt.preventDefault();
      var $this = $(this);
      var stopOnMatch = !$this.data('stop-on-match');

      if ($this.hasClass('disabled')) {
        return;
      }

      $.ajax({
        url: $this.data('href'),
        method: $this.data('method'),
        data: JSON.stringify({stop_on_match: stopOnMatch}),
        dataType: 'json',
        contentType: 'application/json',
        error: handleAjaxError,
        success: function() {
          $this.data('stop-on-match', stopOnMatch);
          $this.toggleClass('stop-processing-enabled', stopOnMatch);
        },
      });
    });
  };

  global.setupCallForAbstractsPage = function setupCallForAbstractsPage(options) {
    options = $.extend(
      {
        hasAbstracts: false,
      },
      options
    );

    // show the form after login when using the submit button as a guest
    if (location.hash === '#submit-abstract') {
      $(document).ready(function() {
        $('.js-show-abstract-form').trigger('click');
      });
    }

    if (options.hasAbstracts) {
      var filterConfig = {
        itemHandle: 'div.contribution-row',
        listItems: '#display-contribution-list div.contribution-row',
        term: '#search-input',
        state: '#filtering-state',
        placeholder: '#filter-placeholder',
      };

      var applySearchFilters = setupSearchBox(filterConfig);
      applySearchFilters();
    }
  };

  global.setupAbstractJudgment = function setupAbstractJudgment(options) {
    options = $.extend(
      {
        trackSessionMap: {},
      },
      options
    );

    $('body').on('change', '#accepted_track', function() {
      var sessionId = options.trackSessionMap[$(this).val()];
      $('#session').val(sessionId || '__None');
    });
    $('#accepted_track').trigger('change');
  };
})(window);
