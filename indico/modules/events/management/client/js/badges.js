// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  'use strict';

  global.setupBadgePrinting = function setupBadgePrinting(templates) {
    var $template = $('#template');
    var $pageLayout = $('#page_layout');
    var $dashedBorder = $('#dashed_border');
    var $pageSize = $('#page_size');
    var $pageOrientation = $('#page_orientation');
    var $marginEditor = $('.margin-editor');
    var $infoMessage = $('.info');

    function toggleFoldableOption(template, pageSize, pageOrientation) {
      var foldablePairs = {
        A0: 'A2',
        A1: 'A3',
        A2: 'A4',
        A3: 'A5',
        A4: 'A6',
        A5: 'A7',
        A6: 'A8',
      };
      if (foldablePairs[pageSize] === template.format && pageOrientation === template.orientation) {
        $("#page_layout option[value='foldable']").prop('disabled', false);
      } else {
        $("#page_layout option[value='foldable']").prop('disabled', true);
        if ($('#page_layout :selected').val() === 'foldable') {
          $('#page_layout :selected')
            .next()
            .prop('selected', true);
        }
      }
    }

    $template
      .on('change', function() {
        var $this = $(this);
        var template = templates[parseInt($this.val(), 10)];

        $pageLayout.closest('.form-group').toggle(!!template.backside_tpl_id);
        $pageLayout.val('front_only');
        toggleFoldableOption(template, $pageSize.val(), $pageOrientation.val());
      })
      .change();

    $pageLayout
      .on('change', function() {
        $marginEditor.add($infoMessage).toggle($(this).val() !== 'foldable');
        $dashedBorder.closest('.form-group').toggle($(this).val() !== 'foldable');
      })
      .change();
    $pageSize
      .add($pageOrientation)
      .on('change', function() {
        toggleFoldableOption(
          templates[parseInt($template.val(), 10)],
          $pageSize.val(),
          $pageOrientation.val()
        );
        $pageLayout.change();
      })
      .change();
  };
})(window);
