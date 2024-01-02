// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// eslint-disable-next-line import/unambiguous
(function() {
  function setupProtection() {
    $('#protection-details-link').qtip({
      style: {
        width: '280px',
        classes: 'qtip-rounded qtip-shadow qtip-popup',
        tip: {
          corner: true,
          width: 20,
          height: 15,
        },
      },
      position: {
        my: 'top center',
        at: 'bottom center',
      },
      content: $('#protection-details'),
      show: {
        event: 'click',
        effect() {
          $(this).fadeIn(300);
        },
      },
      hide: {
        event: 'unfocus click',
        fixed: true,
        effect() {
          $(this).fadeOut(300);
        },
      },
    });
  }

  function setupTimezone() {
    const widget = $('#tz-selector-widget');

    $('#tz-selector-link').qtip({
      style: {
        classes: 'qtip-rounded qtip-shadow qtip-popup qtip-timezone qtip-wide',
        tip: {
          corner: true,
          width: 20,
          height: 15,
        },
      },
      position: {
        my: 'top center',
        at: 'bottom center',
      },
      content: widget,
      show: {
        event: 'click',
        effect() {
          $(this).fadeIn(300);
        },
      },
      hide: {
        event: 'unfocus click',
        fixed: true,
        effect() {
          $(this).fadeOut(300);
        },
      },
      events: {
        show() {
          // eslint-disable-next-line no-undef
          _.defer(scrollToCurrentTZ);
        },
      },
    });

    function scrollToCurrentTZ() {
      const option = widget.find('select[name=tz] option:selected')[0];
      if (option) {
        option.scrollIntoView(false);
      }
    }
  }

  function setupUserSettings() {
    const link = $('#user-settings-link');

    $('#user-settings-widget a:not([data-toggle=dropdown])').on('click', function() {
      link.qtip('hide');
    });

    link.qtip({
      style: {
        minWidth: '200px',
        classes: 'qtip-rounded qtip-shadow qtip-popup qtip-allow-overflow',
        tip: {
          corner: true,
          width: 20,
          height: 15,
        },
      },
      position: {
        my: 'top center',
        at: 'bottom center',
      },
      content: $('#user-settings-widget'),
      show: {
        event: 'click',
        effect() {
          $(this).fadeIn(300);
        },
      },
      hide: {
        event: 'unfocus click',
        fixed: true,
        effect() {
          $(this).fadeOut(300);
        },
      },
    });
  }

  $(document).ready(function() {
    setupProtection();
    setupTimezone();
    setupUserSettings();
  });
})();
