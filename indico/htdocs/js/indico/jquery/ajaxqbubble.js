/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

/* global showFormErrors:false, initForms:false */

(function($) {
    'use strict';

    $.widget('indico.ajaxqbubble', {
        options: {
            qBubbleOptions: {
                position: {
                    effect: false
                },
                content: {
                    text: $('<span>', {text: $T.gettext('Loading...')})
                }
            },
            url: null,
            method: 'GET',
            cache: false,
            success: null,
            onClose: null, // callback to invoke after closing the qtip by submitting the inner form. the argument
                          // is null if closed manually, otherwise the JSON returned by the server.
            qtipConstructor: null
        },

        _create: function() {
            var self = this;
            var qBubbleOptions = _.pick(self.options, 'qBubbleOptions').qBubbleOptions;
            var ajaxOptions = _.omit(self.options, 'qBubbleOptions');
            var returnData = null;

            var options = $.extend(true, {}, qBubbleOptions, {
                events: {
                    show: function(evt, api) {
                        $.ajax($.extend(true, {}, ajaxOptions, {
                            complete: IndicoUI.Dialogs.Util.progress(),
                            error: handleAjaxError,
                            success: function(data, _, xhr) {
                                if ($.isFunction(ajaxOptions.success)) {
                                    ajaxOptions.success.call(self.element, data);
                                }

                                var loadedURL = xhr.getResponseHeader('X-Indico-URL');
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
                                        api.set('content.text', ajaxifyForm($(data.html).find('form').addBack('form')));
                                        if (data.js) {
                                            $('body').append(data.js);
                                        }
                                    }
                                }

                                function ajaxifyForm($form) {
                                    initForms($form);
                                    var killProgress;
                                    return $form.ajaxForm({
                                        url: $form.attr('action') || loadedURL,
                                        method: 'POST',
                                        error: handleAjaxError,
                                        beforeSubmit: function() {
                                            killProgress = IndicoUI.Dialogs.Util.progress();
                                        },
                                        complete: function() {
                                            killProgress();
                                        },
                                        success: function(data) {
                                            if (data.success) {
                                                self.element.next('.label').text(data.new_value);
                                                returnData = data;
                                                api.hide(true);
                                            } else {
                                                updateContent(data);
                                                showFormErrors($('#qtip-' + api.id + '-content'));
                                            }
                                        }
                                    });
                                }

                                updateContent(data);
                            }
                        }));
                        if (qBubbleOptions.events && qBubbleOptions.events.show) {
                            qBubbleOptions.events.show(evt, api);
                        }
                    },
                    hide: function(evt, api) {
                        var originalEvent = evt.originalEvent;

                        if (self.options.onClose) {
                            self.options.onClose(returnData);
                        }
                        returnData = null;

                        // in order not to hide the qBubble when selecting a date
                        if ((originalEvent && $(originalEvent.target).closest('#ui-datepicker-div').length)) {
                            return false;
                        }

                        if (qBubbleOptions.events && qBubbleOptions.events.hide) {
                            qBubbleOptions.events.hide(evt, api);
                        }
                        return true;
                    },
                    hidden: function(evt, api) {
                        api.get('content.text').remove();
                        if (qBubbleOptions.events && qBubbleOptions.events.hidden) {
                            qBubbleOptions.events.hidden(evt, api);
                        }
                    }
                }
            });
            if (self.options.qtipConstructor) {
                self.options.qtipConstructor(self.element, options);
            } else {
                self.element.qbubble(options);
            }
        }
    });
})(jQuery);
