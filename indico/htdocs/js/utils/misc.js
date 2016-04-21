/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

    global.confirmPrompt = function confirmPrompt(message, title) {
        var dfd = $.Deferred();
        message = $('<div>', {width: 400, html: message});
        new ConfirmPopup(title || $T('Please confirm'), message, function(confirmed) {
            if (confirmed) {
                dfd.resolve();
            } else {
                dfd.reject();
            }
        }).open();
        return dfd.promise();
    };

    global.alertPopup = function alertPopup(message, title) {
        var dfd = $.Deferred();
        new AlertPopup(title, message, function(){
            dfd.resolve();
        }).open();
        return dfd;
    };

    global.handleFlashes = function handleFlashes(data, clear, element) {
        var container;
        if (!element || !element.length) {
            container = $('#flashed-messages');
        } else if (element.hasClass('flashed-messages')) {
            container = element;
        } else {
            container = element.closest('.ui-dialog-content').find('.flashed-messages');
            if (!container.length) {
                container = element.closest('.page-content').find('.flashed-messages');
            }
        }
        if (!container.length) {
            container = $('#flashed-messages');
        }
        if (clear === undefined || clear) {
            container.empty();
        }
        if (data.flashed_messages) {
            var flashed = $(data.flashed_messages.trim()).children();
            container.append(flashed);
        }
    };

    global.cornerMessage = function cornerMessage(options) {
        // Create nice message in bottom right corner

        options = $.extend({
            actionLabel: null, // the text of the action label
            actionCallback: null, // the callback that will be invoked
            message: '', // the message that will be displayed
            progressMessage: $T.gettext('Executing operation...'), // the message that will be displayed while executing
                                                                   // the action
            feedbackMessage: $T.gettext('Operation done!'), // the message that will be displayed once the action has
                                                            // been successfully executed
            duration: 0, // the lifetime of the message (without being clicked, 0 = forever)
            feedbackDuration: 4000, // the lifetime of the feedback message (0 = forever)
            class: '' // a class that will be added to the message box (warning, error, success or highlight)
        }, options);

        function _disappear(when) {
            return setTimeout(function() {
                box.fadeOut(function() {
                    box.remove();
                });
            }, when);
        }

        var container = $('#corner-message-container'),
            disappearHandler = options.duration ? _disappear(options.duration) : null;

        if (!container.length) {
            container = $('<div id="corner-message-container">').appendTo('body');
        }

        var box = $('<div class="corner-message">').text(options.message).prependTo(container);

        if (options.class) {
            box.addClass(options.class);
        }

        if (options.actionLabel) {
            var text = $('<a class="corner-message-text" href="#">').text(options.actionLabel).appendTo(box);

            text.on('click', function(evt) {
                evt.preventDefault();

                if (disappearHandler) {
                    clearTimeout(disappearHandler);
                }
                if (options.actionCallback) {
                    var promise = options.actionCallback();

                    box.addClass('progress').text(options.progressMessage);
                    text.remove();

                    promise.then(function() {
                        box.text(options.feedbackMessage);
                        box.removeClass(options.class).addClass('success').removeClass('progress');
                    }, function() {
                        box.text($T.gettext('Operation failed!'));
                        box.removeClass('progress success warning highlight').addClass('error');
                    }).always(function() {
                        if (options.feedbackDuration) {
                            _disappear(options.feedbackDuration);
                        }
                    });
                } else {
                    _disappear(0);
                }
            });
        }
    };

    global.uniqueId = function uniqueId() {
        return '' + Math.round(new Date().getTime() + (Math.random() * 100));
    };
})(window);
