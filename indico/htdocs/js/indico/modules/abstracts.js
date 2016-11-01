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

/* global setupListGenerator:false, initForms:false, showFormErrors:false, getFormParams:false */

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
        $('body').on('indico:confirmed', '.judge-button', function(evt) {
            var $box = $('#abstract-decision-box');
            var $this = $(this);
            var $form = $box.find('form');

            evt.preventDefault();

            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                data: getFormParams($form),
                success: function(data) {
                    if (data.page_html) {
                        $('.management-page').replaceWith(data.page_html);
                        $box = $('#abstract-decision-box');
                    } else {
                        $box.html(data.box_html);
                    }
                    initForms($box);
                    showFormErrors($box);
                }
            });
        }).on('indico:confirmed', '.review-button', function(evt) {
            var $this = $(this);
            var $box = $this.closest('.abstract-review-box');
            var $form = $box.find('form');

            evt.preventDefault();

            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                data: getFormParams($form),
                success: function(data) {
                    var $page = $('.management-page');
                    if (data.page_html) {
                        $page.replaceWith(data.page_html);
                        $page = $('.management-page');
                    } else {
                        $box.replaceWith(data.box_html);
                    }
                    initForms($page);
                    showFormErrors($page);
                }
            });
        }).on('click', '.change-review-button', function(evt) {
            evt.preventDefault();

            var $reviewDisplay = $(this).closest('.i-timeline-item');
            var $reviewBox = $reviewDisplay.next('.abstract-review-box');
            $reviewDisplay.hide();
            $reviewBox.show();
        }).on('indico:htmlUpdated', function() {
            initForms($(this));
            showFormErrors($(this));
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
})(window);
