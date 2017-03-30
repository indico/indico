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

(function() {
    'use strict';

    function setupEventDisplay() {
        function openAjaxDialog($element) {
            ajaxDialog({
                title: $element.data('title'),
                url: $element.data('href'),
                confirmCloseUnsaved: true,
                onClose: function(data, customData) {
                    if (data || customData) {
                        location.reload();
                    }
                }
            });
        }

        $(document).on('click', '[data-note-editor]', function(evt) {
            evt.preventDefault();
            openAjaxDialog($(this));
        });

        $('.js-go-to-day').dropdown({
            always_listen: true
        }).find('li a').on('menu_select', function() {
            var anchor = $(this).attr('href');
            $('body, html').animate({
                scrollTop: $(anchor).offset().top
            }, {
                duration: 700,
                complete: function() {
                    location.href = anchor;
                }
            });
            return false;
        });

        var selectors = ['.notes-compile', '.contribution-edit', '.subcontribution-edit'].join(', ');
        $('body').on('click', selectors, function(e) {
            e.preventDefault();
            openAjaxDialog($(this));
            return false;
        });

        $(document).ready(function() {
            $('h1, .item-description, .timetable-title').mathJax();
        });
    }

    function toggleNote(element, visible, immediate) {
        // Note for event
        var note = element.closest('.event-note-section');
        // Note for other elements
        if (note.length === 0) {
            note = element.closest('li').find('.note-area-wrapper');
        }
        var content = note.hasClass('togglable') ? note : note.find('.togglable');
        if (immediate) {
            content.toggle(visible);
        } else {
            content[visible === undefined ? 'slideToggle' : visible ? 'slideDown' : 'slideUp']();
        }
    }

    $(document).ready(function() {
        $('.event-service-row > .trigger').on('click', function() {
            var toggler = $(this);
            toggler.siblings('.event-service-details').slideToggle({
                start: function() {
                    toggler.toggleClass('icon-expand icon-collapse');
                },
                duration: 'fast'
            });
        });

        $('.event-service-row-toggle').on('click', function(e) {
            e.preventDefault();
            var toggler = $(this);
            var togglerButton = $(this).parent().siblings('.trigger');
            toggler.parent().siblings('.event-service-details').slideToggle({
                start: function() {
                    togglerButton.toggleClass('icon-expand icon-collapse');
                },
                duration: 'fast'
            });
        });

        var threeRowsHeight = 70;
        $('.participant-list-wrapper').toggleClass('collapsible collapsed transparent-overlay',
            $('.participant-list').height() > threeRowsHeight);
        var initialHeight = $('.participant-list-wrapper').height();

        $('.participant-list-wrapper.transparent-overlay').on('click', function() {
            var toggler = $('.participant-list-wrapper > .trigger');
            var participantList = toggler.siblings('.participant-list');
            var wrapper = participantList.parent();
            if (wrapper.hasClass('collapsed')) {
                var newHeight = participantList.height();
                participantList.height(initialHeight);
                wrapper.removeClass('collapsed transparent-overlay');
                wrapper.animate({
                    height: newHeight
                }, {
                    duration: 'fast',
                    start: function() {
                        toggler.addClass('icon-collapse').removeClass('icon-expand');
                    },
                    complete: function() {
                        participantList.height(newHeight);
                    }
                });
            } else {
                wrapper.addClass('transparent-overlay');
                wrapper.animate({
                    height: initialHeight
                }, {
                    duration: 'fast',
                    start: function() {
                        toggler.removeClass('icon-collapse').addClass('icon-expand');
                    },
                    complete: function() {
                        wrapper.addClass('collapsed');
                    }
                });
            }
        });

        $('a.js-show-note-toggle').on('click', function(e) {
            e.preventDefault();
            toggleNote($(this));
        });

        $('input.js-toggle-note-cb').on('change', function(e, immediate) {
            toggleNote($(this), this.checked, immediate);
        });

        $('input.js-toggle-note-cb').trigger('change', [true]);

        $('.js-note-editor').ajaxDialog({
            title: $T("Edit minutes"),
            confirmCloseUnsaved: true,
            onClose: function(data, customData) {
                if (data || customData) {
                    location.reload();
                }
            }
        });

        setupEventDisplay();
    });
})();
