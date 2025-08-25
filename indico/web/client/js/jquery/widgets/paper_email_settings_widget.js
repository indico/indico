// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */

(function($) {
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

    _initCheckboxes(data) {
      const self = this;
      const elementID = self.element.prop('id');
      const multipleRecipientOptions = self.options.multipleRecipientOptions;
      const singleRecipientOptions = self.options.singleRecipientOptions;

      multipleRecipientOptions.forEach(condition => {
        data[condition].forEach(role => {
          $('#{0}-{1}-{2}'.format(elementID, condition, role)).prop('checked', true);
        });
      });
      singleRecipientOptions.forEach(condition => {
        $('#{0}-{1}'.format(elementID, condition)).prop('checked', data[condition]);
      });
    },

    _create() {
      const self = this;
      const element = self.element;
      const $container = self.options.containerElement;
      const hiddenData = element.val() ? JSON.parse(element.val()) : {};

      self._initCheckboxes(hiddenData);

      $container.find('.multiple-recipients input').on('change', function() {
        const setting = hiddenData[this.name];
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
