// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// Global scripts that should be executed on all pages
/* global showFormErrors:false */
/* eslint-disable max-len */
/* eslint-disable import/unambiguous */

$(document).ready(function() {
  $('.main-breadcrumb a[href="#"]')
    .css({cursor: 'default', outline: 'none'})
    .on('click', function(e) {
      e.preventDefault();
    });

  // Use qtip for context help

  $.fn.qtip.defaults = $.extend(true, {}, $.fn.qtip.defaults, {
    position: {
      my: 'top center',
      at: 'bottom center',
    },
    hide: {
      event: 'click mouseout',
    },
  });

  $('.contextHelp[title]').qtip();

  /* Add qTips to elements with a title attribute. The position of the qTip
   * can be specified in the data-qtip-position attribute and is one of
   * "top", "left", "bottom" or "right". It defaults to "bottom".
   *
   * It is also possible to have HTML inside the qTip by using the
   * data-qtip-html attribute instead of the title attribute. */
  $(document).on(
    'mouseenter',
    '[title]:not([data-no-qtip]):not([title=""]):not(iframe), [data-qtip-html], [data-qtip-oldtitle]:not(iframe)',
    function(evt) {
      var $target = $(this);
      var title = ($target.attr('title') || $target.data('qtip-oldtitle') || '').trim();
      var extraOpts = $(this).data('qtip-opts') || {};
      var qtipClass = $(this).data('qtip-style');
      var qtipHTMLContainer = $(this).data('qtip-html');
      var qtipHTML =
        qtipHTMLContainer && qtipHTMLContainer.length ? $(this).next(qtipHTMLContainer) : null;

      // qtip not applied if it's empty, the element is disabled or it's inside a SemanticUI widget
      if (
        (!qtipHTML && !title) ||
        this.disabled ||
        $target.data('no-qtip') ||
        ($target.closest('.ui:not(.ui-qtip)').length && !$target.hasClass('ui-qtip')) ||
        $target.closest('.tox-tinymce').length ||
        $target.closest('.tox').length ||
        $target.closest('.fc-toolbar-chunk').length
      ) {
        return;
      }

      $target.attr('data-qtip-oldtitle', title);
      $target.removeAttr('title');

      var position = $(this).data('qtip-position');
      var positionOptions;
      if (position === 'left') {
        positionOptions = {
          my: 'right center',
          at: 'left center',
        };
      } else if (position === 'right') {
        positionOptions = {
          my: 'left center',
          at: 'right center',
        };
      } else if (position === 'top') {
        positionOptions = {
          my: 'bottom center',
          at: 'top center',
        };
      } else if (position === 'bottom') {
        positionOptions = {
          my: 'top center',
          at: 'bottom center',
        };
      }

      /* Attach the qTip to a new element to avoid side-effects on all elements with "title" attributes. */
      var qtip = $('<span>').qtip(
        $.extend(
          true,
          {},
          {
            overwrite: false,
            position: $.extend(
              {
                target: $target,
              },
              positionOptions
            ),

            show: {
              event: evt.type,
              ready: true,
            },

            content: {
              text: function() {
                if (qtipHTML) {
                  return qtipHTML.html();
                } else {
                  return title
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;');
                }
              },
            },

            events: {
              show: function(event) {
                if ($(event.originalEvent.target).hasClass('open')) {
                  event.preventDefault();
                }
              },

              hide: function() {
                $(this).qtip('destroy');
              },

              render: function(event, api) {
                $target.on('DOMNodeRemovedFromDocument remove', function() {
                  api.destroy();
                });
              },
            },

            hide: {
              event: 'mouseleave',
              target: $target,
            },

            style: {
              classes: qtipClass ? 'qtip-' + qtipClass : null,
            },
          },
          extraOpts
        ),
        evt
      );

      $target.on('indico:closeAutoTooltip', function() {
        qtip.qtip('hide');
      });
    }
  );

  // Enable colorbox for links with .js-lightbox
  $('body').on('click', 'a.js-lightbox', function() {
    $(this).colorbox({
      maxHeight: '90%',
      maxWidth: '90%',
      loop: false,
      photo: true,
      returnFocus: false,
    });
  });

  // Prevent # in the URL when clicking disabled links
  $('body').on('click', 'a.disabled', function(evt) {
    evt.preventDefault();
  });

  $('.contextHelp[data-src]').qtip({
    content: {
      text: function() {
        return $($(this).data('src')).removeClass('tip');
      },
    },
  });

  function initDropdowns($container) {
    $container.find('.js-dropdown').each(function() {
      $(this)
        .parent()
        .dropdown({
          selector: '.js-dropdown',
        });
    });
  }

  $('body').on('indico:htmlUpdated', function(evt) {
    initDropdowns($(evt.target));
  });
  initDropdowns($('body'));

  if (navigator.userAgent.match(/Trident\/7\./)) {
    // Silly IE11 will clear the second password field if
    // password autocompletion is enabled!
    // https://social.msdn.microsoft.com/Forums/en-US/7d02173f-8f45-4a74-90bf-5dfbd8f9c1de/ie-11-issue-with-two-password-input-fields
    $('input:password').each(function() {
      if (!this.value && this.getAttribute('value')) {
        this.value = this.getAttribute('value');
      }
    });
  }

  // jQuery UI prevents anything outside modal dialogs from gaining focus.
  // This breaks e.g. the session color date selector. To fix this we prevent
  // the focus trap (focusin event bound on document) from ever receiving the
  // event in case the z-index of the focused event is higher than the dialog's.
  function getMaxZ(elem) {
    var maxZ = 0;
    elem
      .parents()
      .addBack()
      .each(function() {
        var z = +$(this).css('zIndex');
        if (!isNaN(z)) {
          maxZ = Math.max(z, maxZ);
        }
      });
    return maxZ;
  }

  $('body').on('focusin', function(e) {
    if (!$.ui.dialog.overlayInstances) {
      return;
    }

    if (getMaxZ($(e.target)) > getMaxZ($('.ui-dialog:visible:last'))) {
      e.stopPropagation();
    }
  });

  // Prevent BACK in browser with backspace when focused on a readonly field
  $('input, textarea').on('keydown', function(e) {
    if (this.readOnly && e.key === 'Backspace') {
      e.preventDefault();
    }
  });

  $('input.permalink').on('focus', function() {
    this.select();
  });

  showFormErrors();

  // Show form creation dialog if hash is present in the URL
  const match = location.hash.match(
    /^#create-event:(lecture|meeting|conference)(?::(\d*)(?::([a-f0-9-]{36}))?)?$/
  );
  if (match) {
    const [, eventType, categoryId, eventUUID] = match;
    const title = {
      lecture: $T.gettext('Create new lecture'),
      meeting: $T.gettext('Create new meeting'),
      conference: $T.gettext('Create new conference'),
    }[eventType];
    let url;
    if (categoryId && eventUUID) {
      url = build_url(Indico.Urls.EventCreation, {
        event_type: eventType,
        category_id: categoryId,
        event_uuid: eventUUID,
      });
    } else if (categoryId) {
      url = build_url(Indico.Urls.EventCreation, {event_type: eventType, category_id: categoryId});
    } else if (eventUUID) {
      url = build_url(Indico.Urls.EventCreation, {event_type: eventType, event_uuid: eventUUID});
    } else {
      url = build_url(Indico.Urls.EventCreation, {event_type: eventType});
    }
    ajaxDialog({url, title});
  }
});
