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

/* global setupListGenerator:false */
/* global Palette:false */

(function(global) {
    'use strict';

    global.setupAbstractList = function setupAbstractList() {
        var abstractListContainer = $('#abstract-list');

        var filterConfig = {
            itemHandle: 'tr',
            listItems: '#abstract-list tbody tr',
            term: '#search-input',
            state: '#filtering-state',
            placeholder: '#filter-placeholder'
        };

        abstractListContainer.on('indico:htmlUpdated', function() {
            abstractListContainer.find('.js-mathjax').mathJax();
        });

        setupListGenerator(filterConfig);
    };

    global.setupAbstractPage = function setupAbstractPage() {
        $('body').on('declarative:success', '.js-delete-comment', function() {
            $(this).closest('.i-timeline-item').remove();
        }).on('ajaxForm:show', '.js-edit-comment, .js-edit-review', function() {
            $(this).closest('.i-box-header').hide();
        }).on('ajaxForm:hide', '.js-edit-comment, .js-edit-review', function() {
            $(this).closest('.i-box-header').show();
        }).on('focus', '.new-comment textarea', function() {
            var $box = $('#abstract-timeline-input');
            var $commentForm = $box.find('form');
            $box.find('.review-trigger').hide('blind', {direction: 'left'}, 'fast');
            $commentForm.find('.form-group').show('fast');
            $commentForm.removeClass('unfocused');
            $commentForm.trigger('ajaxForm:externalShow');
        }).on('click', '.new-comment .js-new-cancel', function(evt) {
            evt.preventDefault();
            var $box = $('#abstract-timeline-input');
            var $commentForm = $box.find('form');
            var $reviewTrigger = $box.find('.review-trigger');
            var deferred = $.Deferred();
            $commentForm.trigger('ajaxForm:externalHide', [deferred]);
            deferred.then(function() {
                $commentForm[0].reset();
                $commentForm.trigger('change');
                $commentForm.addClass('unfocused');
                $commentForm.find('.form-group ~ .form-group').hide('fast', function() {
                    $reviewTrigger.show('blind', {direction: 'left'}, 'fast');
                });
            });
        }).on('click', '.js-new-edit-review', function() {
            var reviewId = $(this).data('reviewId');
            var $reviewBox = $('#abstract-review-{0}'.format(reviewId));
            $reviewBox.find('.js-edit-review').trigger('click');
            $('body, html').animate({scrollTop: $reviewBox.offset().top}, 'fast');
            $reviewBox.find('.i-timeline-item-box').effect('highlight', {color: Palette.highlight}, 'slow');
        }).on('click', '.ratings-switch .i-button', function() {
            var $this = $(this);
            $this.toggleClass('open');
            $this.closest('.ratings-switch').siblings('.ratings-details').toggle();
        });
    };

    global.setupAbstractEmailTemplatesPage = function setupAbstractEmailTemplatesPage() {
        $('.js-edit-tpl-dropdown').parent().dropdown();
        $('.email-templates > ul').sortable({
            axis: 'y',
            containment: 'parent',
            cursor: 'move',
            distance: 2,
            handle: '.ui-i-box-sortable-handle',
            items: '> li',
            tolerance: 'pointer',
            forcePlaceholderSize: true,
            placeholder: 'regform-section-sortable-placeholder',
            update: function() {
                var $elem = $('.email-templates > ul');
                var sortedList = $elem.find('li.email-template').map(function(i, elem) {
                    return $(elem).data('id');
                }).get();

                $.ajax({
                    url: $elem.data('url'),
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({sort_order: sortedList}),
                    complete: IndicoUI.Dialogs.Util.progress(),
                    error: handleAjaxError
                });
            }
        });

        $('.email-preview-btn').on('click', function(evt) {
            evt.preventDefault();
            var id = $(this).data('id');
            var $previewBtn = $('#email-preview-btn-' + id);
            if ($previewBtn.data('visible')) {
                $previewBtn.text($T.gettext('Show preview'));
                $('#email-preview-' + id).slideToggle();
                $previewBtn.data('visible', false);
            } else {
                $previewBtn.text($T.gettext('Hide preview'));
                $('#email-preview-' + id).slideToggle();
                $previewBtn.data('visible', true);
            }
        });

        $('#email-template-manager .ui-i-box-sortable-handle').on('mousedown', function() {
            $('.email-preview').hide();
            $('.email-preview-btn').text($T.gettext('Show preview')).data('visible', false);
        });

        $('.js-toggle-stop-on-match').on('click', function(evt) {
            evt.preventDefault();
            var $this = $(this);
            var stopOnMatch = !$this.data('stop-on-match');
            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                data: JSON.stringify({stop_on_match: stopOnMatch}),
                dataType: 'json',
                contentType: 'application/json',
                error: handleAjaxError,
                success: function() {
                    $this.data('stop-on-match', stopOnMatch);
                    $this.toggleClass('danger text-color', stopOnMatch);
                }
            });
        });
    };

    global.setupCallForAbstractsPage = function setupCallForAbstractsPage() {
        // show the form after login when using the submit button as a guest
        if (location.hash === '#submit-abstract') {
            $(document).ready(function() {
                $('.js-show-abstract-form').trigger('click');
            });
        }
    };
})(window);
