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

(function(global, $) {
    'use strict';

    // Ajaxifies a link to open the target page (which needs to be using jsonify_template or
    // WPJinjaMixin.render_template) in a  modal dialog. Any forms on the page are ajaxified and should be using
    // redirect_or_jsonify() (when used with WPJinjaMixin) or jsonify_data (when used with jsonify_template)
    // in case of success (or just return a JSON response containing success=true and possibly flashed messages).
    // The link target MUST point to a page which is also valid when loaded directly in the browser since the
    // link could still be opened in a new tab manually. If you don't have a non-AJAX version, place the url in
    // data-href.
    $.fn.ajaxDialog = function jqAjaxDialog(options) {
        return this.on('click', function(e) {
            e.preventDefault();
            if ($(this).hasClass('disabled')) {
                return;
            }
            var href = $(this).attr('href');
            if (href === undefined || href == '#') {
                var data_href = $(this).data('href');
                href = data_href ? data_href : href;
            }
            ajaxDialog($.extend({}, options, {
                url: href,
                trigger: this
            }));
        });
    };

    // See the documentation of $.fn.ajaxDialog - use this function if you want to open an ajax-based dialog
    // manually instead of triggering it from a link using its href.
    global.ajaxDialog = function ajaxDialog(options) {
        options = $.extend({
            trigger: null, // element that opened the dialog
            title: null, // title of the dialog
            url: null, // url to get the form/dialog from
            method: 'GET', // http method to get the form/dialog
            data: null, // object or callable to add data when loading the form/dialog
            backSelector: '[data-button-back]', // elements in the form which will close the form
            clearFlashes: true, // clear existing flashed messages before showing new ones
            onClose: null, // callback to invoke after closing the dialog. first argument is null if closed manually,
                           // otherwise the JSON returned by the server. if it returns false, the dialog will remain
                           // open; if it returns a Deferred object, the dialog remain open until the object is resolved
            getExtraData: function() {},  // callback to add data to the form. receives the <form> element as `this`
            confirmCloseUnsaved: false,  // ask the user to confirm closing the dialog with unsaved changes
            dialogClasses: '',  // extra classes to add to the dialog canvas
            hidePageHeader: false  // if the default page header (title/subtitle/description) should be hidden
        }, options);

        var popup = null;
        var customData = null;

        $.ajax({
            type: options.method,
            url: options.url,
            data: $.isFunction(options.data) ? options.data() : options.data,
            cache: false, // IE caches GET AJAX requests. WTF.
            complete: IndicoUI.Dialogs.Util.progress(),
            error: handleAjaxError,
            success: function(data) {
                if (handleAjaxError(data)) {
                    return;
                }
                showDialog(data);
            }
        });

        function confirmClose() {
            var forms = popup.contentContainer.find('form');
            var hasChanges = forms.length && forms.filter(function() {
                return $(this).data('fieldsChanged');
            }).length;
            var message = $T('You have unsaved changes. Do you really want to close the dialog without saving?');
            return hasChanges ? confirmPrompt(message, $T('Unsaved changes')) : $.Deferred().resolve();
        }

        function showDialog(dialogData) {
            popup = new ExclusivePopup($.isFunction(options.title) ? options.title() : options.title, function() {
                closeDialog(null);
                return false;
            }, false, false);

            popup.draw = function() {
                this.ExclusivePopup.prototype.draw.call(this, dialogData.html);
            };

            popup.postDraw = function() {
                ajaxifyForms();
                popup.canvas.on('ajaxDialog:setData', function(e, data) {
                    customData = data;
                });
                injectJS(dialogData.js);
                _.defer(function() {
                    popup.canvas.data('ui-dialog')._focusTabbable();
                });
            };

            var dialogClasses = _.union(['dialog-window', options.dialogClasses]);
            if (options.hidePageHeader) {
                dialogClasses.push('no-page-header');
            }
            popup.canvas.addClass(dialogClasses.join(' '));
            popup.open();
        }

        function closeDialog(callbackData, submitted) {
            var confirmDeferred = (submitted || !options.confirmCloseUnsaved) ? $.Deferred().resolve() : confirmClose();
            confirmDeferred.then(function() {
                var onCloseResult = !options.onClose ? $.Deferred().resolve() : options.onClose(callbackData, customData);
                if (onCloseResult === false) {
                    return;
                }
                else if (!onCloseResult || onCloseResult === true) {
                    onCloseResult = $.Deferred().resolve();
                }
                onCloseResult.then(function() {
                    popup.close();
                });
            });
        }

        function ajaxifyForms() {
            var killProgress = null;
            var forms = popup.contentContainer.find('form');
            showFormErrors(popup.resultContainer);
            initForms(forms);
            forms.on('click', options.backSelector, function(e) {
                e.preventDefault();
                closeDialog();
            }).each(function() {
                var $this = $(this);
                $this.on('ajaxDialog:beforeSubmit', function() {
                    killProgress = IndicoUI.Dialogs.Util.progress();
                }).on('ajaxDialog:error', function(e, xhr) {
                    if (killProgress) {
                        killProgress();
                    }
                    closeDialog();
                    handleAjaxError(xhr);
                }).on('ajaxDialog:success', function(e, data) {
                    if (killProgress) {
                        killProgress();
                    }
                    if (handleAjaxError(data)) {
                        closeDialog();
                        return;
                    }

                    handleFlashes(data, options.clearFlashes, options.trigger ? $(options.trigger) : null);

                    if (data.close_dialog || data.success) {
                        closeDialog(data, true);
                    } else if (data.html) {
                        popup.contentContainer.html(data.html);
                        ajaxifyForms();
                        injectJS(data.js);
                    }
                });
                // We often use forms with an empty action; those need to go to
                // their page and not the page that loaded the dialog!
                var action = $this.attr('action') || options.url;
                $this.ajaxForm({
                    url: action,
                    dataType: 'json',
                    data: options.getExtraData.call(this, options.trigger),
                    traditional: true,
                    beforeSubmit: function() {
                        $this.trigger('ajaxDialog:beforeSubmit');
                    },
                    error: function(xhr) {
                        $this.trigger('ajaxDialog:error', [xhr]);
                    },
                    success: function(data) {
                        $this.trigger('ajaxDialog:success', [data]);
                    }
                });
            });
        }

        function injectJS(js) {
            if (js) {
                $('body').append(js)
            }
        }
    };
})(window, jQuery);
