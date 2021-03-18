// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
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
      },
      options
    );

    const inputs = $(`input[name=${options.fieldName}][id^=${options.fieldId}]`);

    inputs.on('change', function() {
      const $this = $(this);
      const isProtected =
        $this.val() === 'protected' || ($this.val() === 'inheriting' && options.parentProtected);

      if (this.checked) {
        $('#form-group-protected-{0} .protection-message'.format(options.fieldId)).hide();
        $(
          '#form-group-protected-{0} .{1}-protection-message'.format(options.fieldId, $this.val())
        ).show();

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
          $('#permissions-widget-{0}'.format(options.permissionsFieldId)).trigger(
            'indico:protectionModeChanged',
            [isProtected]
          );
        }
      }
    });

    _.defer(function() {
      inputs.trigger('change');
    });
  };
})(window);
