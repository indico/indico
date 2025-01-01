// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// -----------------------------------------------------------------------------
// Indico-specific settings
// -----------------------------------------------------------------------------

import {$T} from '../../utils/i18n';

$.datepicker.setDefaults({
  autoSize: true,
  buttonText: '',
  dateFormat: 'dd/mm/yy',
  firstDay: 1,
  nextText: $T('Next'),
  prevText: $T('Previous'),
  showOn: 'both',
});

$.fn.qtip.defaults = $.extend(true, {}, $.fn.qtip.defaults, {
  position: {
    my: 'top left',
    at: 'bottom right',
    viewport: $(window),
  },
  style: {
    tip: {corner: true},
  },
});

$.extend($.colorbox.settings, {
  opacity: 0.6,
});

$.tablesorter.defaults.sortReset = true;

$.ajaxSetup({
  traditional: true,
  beforeSend: function(xhr, settings) {
    'use strict';
    if (!/^https?:.*/.test(settings.url)) {
      // Add CSRF token to local requests
      xhr.setRequestHeader('X-CSRF-Token', $('#csrf-token').attr('content'));
    }
  },
});

// Disabling autoDiscover, otherwise Dropzone will try to attach twice.
if (window.Dropzone) {
  window.Dropzone.autoDiscover = false;
}
