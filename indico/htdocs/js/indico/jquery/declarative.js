/* This file is part of Indico.
 * Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

(function(global) {
    'use strict';

    $(document).ready(function() {
        setupActionLinks();
        setupConfirmPopup();
        setupSelectAllNone();
    });

    function setupSelectAllNone() {
        $('body').on('click', '[data-select-all]', function() {
            var selector = $(this).data('select-all');
            $(selector).filter(':not(:checked)').prop('checked', true).trigger('change');
        });

        $('body').on('click', '[data-select-none]', function() {
            var selector = $(this).data('select-none');
            $(selector).filter(':checked').prop('checked', false).trigger('change');
        });
    }

    function setupConfirmPopup() {
        $('body').on('click', '[data-confirm]:not(button[data-href]):not(input:button[data-href]):not(a[data-method][data-href])', function() {
            var $this = $(this);
            confirmPrompt($(this).data('confirm'), $(this).data('title')).then(function() {
                if ($this.is('form')) {
                    $this.submit();
                } else {
                    window.location = $this.attr('href');
                }
            });
            return false;
        });
    }

    function setupActionLinks() {
        $('body').on('click', 'button[data-method][data-href], input:button[data-method][data-href], a[data-method][data-href]', function(e) {
            e.preventDefault();
            var $this = $(this);
            var url = $this.data('href');
            var method = $this.data('method').toUpperCase();
            var params = $this.data('params') || {};
            var paramsSelector = $this.data('params-selector');
            var update = $this.data('update');
            var dialog = $this.data('ajax-dialog') !== undefined;
            if (!$.isPlainObject(params)) {
                throw new Error('Invalid params. Must be valid JSON if set.');
            }

            if (paramsSelector) {
                var fieldParams = {};
                $(paramsSelector).each(function() {
                    if (!(this.name in fieldParams)) {
                        fieldParams[this.name] = [];
                    }
                    fieldParams[this.name].push($(this).val());
                });
                params = $.extend({}, fieldParams, params);
            }

            function execute() {
                var evt = $.Event('indico:confirmed');
                $this.trigger(evt);

                // Handle custom code
                if (evt.isDefaultPrevented()) {
                    return;
                }

                // Handle AJAX dialog
                if (dialog) {
                    ajaxDialog({
                        trigger: $this,
                        url: url,
                        title: $this.data('title'),
                        onClose: function(data) {
                            if (data && update) {
                                $(update).html(data.html);
                            }
                        }
                    });
                    return;
                }

                // Handle html update
                if (update) {
                    $.ajax({
                        method: method,
                        url: url,
                        data: params,
                        error: handleAjaxError,
                        complete: IndicoUI.Dialogs.Util.progress(),
                        success: function(data) {
                            $(update).html(data.html);
                        }
                    });
                    return;
                }

                // Handle normal GET/POST
                if (method === 'GET') {
                    location.href = build_url(url, params);
                } else if (method === 'POST') {
                    var form = $('<form>', {
                        action: url,
                        method: method
                    });
                    form.append($('<input>', {type: 'hidden', name: 'csrf_token', value: $('#csrf-token').attr('content')}));
                    $.each(params, function(key, value) {
                        form.append($('<input>', {type: 'hidden', name: key, value: value}));
                    });
                    form.appendTo('body').submit();
                }
            }

            var promptMsg = $this.data('confirm');
            var confirmed;
            if (!promptMsg) {
                confirmed = $.Deferred().resolve();
            } else {
                confirmed = confirmPrompt(promptMsg, $(this).data('title') || $T('Confirm action'));
            }
            confirmed.then(execute);
        });
    }
})(window);
