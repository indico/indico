// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global showFormErrors, initForms, handleAjaxError */

import _ from 'lodash';

import {$T} from '../../utils/i18n';

(function($) {
  $.widget('indico.ajaxqbubble', {
    options: {
      qBubbleOptions: {
        position: {
          effect: false,
        },
        content: {
          text: $('<span>', {text: $T.gettext('Loading...')}),
        },
      },
      url: null,
      method: 'GET',
      cache: false,
      success: null,
      onClose: null, // callback to invoke after closing the qtip by submitting the inner form. the argument
      // is null if closed manually, otherwise the JSON returned by the server.
      qtipConstructor: null,
    },

    _create() {
      const self = this;
      const qBubbleOptions = _.pick(self.options, 'qBubbleOptions').qBubbleOptions;
      const ajaxOptions = _.omit(self.options, 'qBubbleOptions');
      let returnData = null;

      const options = $.extend(true, {}, qBubbleOptions, {
        events: {
          show(evt, api) {
            $.ajax(
              $.extend(true, {}, ajaxOptions, {
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success(data, __, xhr) {
                  if ($.isFunction(ajaxOptions.success)) {
                    ajaxOptions.success.call(self.element, data);
                  }

                  let loadedURL = xhr.getResponseHeader('X-Indico-URL');
                  if (loadedURL) {
                    // in case of a redirect we need to update the url used to submit the ajaxified
                    // form. otherwise url normalization might fail during the POST requests.
                    // we also remove the _=\d+ cache buster since it's only relevant for the GET
                    // request and added there automatically
                    loadedURL = loadedURL
                      .replace(/&_=\d+/, '')
                      .replace(/\?_=\d+$/, '')
                      .replace(/\?_=\d+&/, '?');
                  }

                  function updateContent(data) {
                    if (data) {
                      api.set(
                        'content.text',
                        ajaxifyForm($(data.html).find('form').addBack('form'))
                      );
                      if (data.js) {
                        $('body').append(data.js);
                      }
                    }
                  }

                  function ajaxifyForm($form) {
                    initForms($form);
                    let killProgress;
                    return $form.ajaxForm({
                      url: $form.attr('action') || loadedURL,
                      method: 'POST',
                      error: handleAjaxError,
                      beforeSubmit() {
                        killProgress = IndicoUI.Dialogs.Util.progress();
                      },
                      complete() {
                        killProgress();
                      },
                      success(data) {
                        if (data.success) {
                          self.element.next('.label').text(data.new_value);
                          returnData = data;
                          api.hide(true);
                        } else {
                          updateContent(data);
                          showFormErrors($(`#qtip-${api.id}-content`));
                        }
                      },
                    });
                  }

                  updateContent(data);
                },
              })
            );
            if (qBubbleOptions.events && qBubbleOptions.events.show) {
              qBubbleOptions.events.show(evt, api);
            }
          },
          hide(evt, api) {
            const originalEvent = evt.originalEvent;

            if (self.options.onClose) {
              self.options.onClose(returnData);
            }
            returnData = null;

            // in order not to hide the qBubble when selecting a date
            if (originalEvent && $(originalEvent.target).closest('#ui-datepicker-div').length) {
              return false;
            }

            if (qBubbleOptions.events && qBubbleOptions.events.hide) {
              qBubbleOptions.events.hide(evt, api);
            }
            return true;
          },
          hidden(evt, api) {
            api.get('content.text').remove();
            if (qBubbleOptions.events && qBubbleOptions.events.hidden) {
              qBubbleOptions.events.hidden(evt, api);
            }
          },
        },
      });
      if (self.options.qtipConstructor) {
        self.options.qtipConstructor(self.element, options);
      } else {
        self.element.qbubble(options);
      }
    },
  });
})(jQuery);
