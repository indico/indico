// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global handleAjaxError:true */

import _ from 'lodash';

(function(global) {
  global.setupProtectionWidget = function setupProtectionWidget(options) {
    options = $.extend(
      true,
      {
        fieldId: null,
        fieldName: null,
        parentProtected: false,
        aclMessageUrl: null,
        hasInheritedAcl: false,
        permissionsFieldId: null,
        isUnlistedEvent: false,
      },
      options
    );

    const inputs = $(`input[name=${options.fieldName}][id^=${options.fieldId}]`);

    if (options.isUnlistedEvent) {
      inputs.prop('disabled', true);
      $(`#form-group-protected-${options.fieldId} .protection-message`).hide();
      $(`#form-group-protected-${options.fieldId} .unlisted-event-protection-message`).show();
    }

    inputs.on('change', function() {
      const $this = $(this);
      const isProtected =
        $this.val() === 'protected' || ($this.val() === 'inheriting' && options.parentProtected);

      if (this.checked) {
        $(`#form-group-protected-${options.fieldId} .protection-message`).hide();
        $(`#form-group-protected-${options.fieldId} .${$this.val()}-protection-message`).show();

        if (options.aclMessageUrl && options.hasInheritedAcl) {
          $.ajax({
            url: options.aclMessageUrl,
            data: {mode: $this.val()},
            error: handleAjaxError,
            success(data) {
              $this
                .closest('form')
                .find('.inheriting-acl-message')
                .html(data.html);
            },
          });
        }
        if (options.permissionsFieldId) {
          $(`#permissions-widget-${options.permissionsFieldId}`).trigger(
            'indico:protectionModeChanged',
            [isProtected]
          );
        }
      }
    });

    _.defer(function() {
      if (!options.isUnlistedEvent) {
        inputs.trigger('change');
      }
    });
  };
})(window);
