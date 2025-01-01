// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function($) {
  'use strict';

  $.widget('indico.paperemailsettingswidget', {
    options: {
      containerElement: null,
      multipleRecipientOptions: [
        'notify_on_added_to_event',
        'notify_on_assigned_contrib',
        'notify_on_paper_submission',
      ],
      singleRecipientOptions: ['notify_judge_on_review', 'notify_author_on_judgment'],
    },

    _initCheckboxes: function(data) {
      var self = this;
      var elementID = self.element.prop('id');
      var multipleRecipientOptions = self.options.multipleRecipientOptions;
      var singleRecipientOptions = self.options.singleRecipientOptions;

      multipleRecipientOptions.forEach(function(condition) {
        data[condition].forEach(function(role) {
          $('#{0}-{1}-{2}'.format(elementID, condition, role)).prop('checked', true);
        });
      });
      singleRecipientOptions.forEach(function(condition) {
        $('#{0}-{1}'.format(elementID, condition)).prop('checked', data[condition]);
      });
    },

    _create: function() {
      var self = this;
      var element = self.element;
      var $container = self.options.containerElement;
      var hiddenData = element.val() ? JSON.parse(element.val()) : {};

      self._initCheckboxes(hiddenData);

      $container.find('.multiple-recipients input').on('change', function() {
        var setting = hiddenData[this.name];
        if (this.checked) {
          setting.push(this.value);
        } else {
          setting.splice(setting.indexOf(this.value), 1);
        }
        element.val(JSON.stringify(hiddenData));
      });

      $container.find('.single-recipient input').on('change', function() {
        hiddenData[this.name] = this.checked;
        element.val(JSON.stringify(hiddenData));
      });
    },
  });
})(jQuery);
