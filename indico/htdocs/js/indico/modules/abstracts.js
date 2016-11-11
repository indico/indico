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
        $('body').on('indico:confirmed', '.js-comment, .js-review', function(evt) {
            evt.preventDefault();

            var $this = $(this);
            var $box = $this.parents('.i-timeline-item');
            var $form = $box.find('form');
            var $page = $('.management-page');

            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                data: getFormParams($form),
                success: function(data) {
                    if (data.page_html) {
                        var $newPage = $(data.page_html);
                        $page.replaceWith($newPage);
                        $page = $newPage;
                    } else {
                        $form.replaceWith(data.form_html);
                    }
                    initForms($page);
                    showFormErrors($page);
                }
            });
        }).on('indico:confirmed', '.js-judge', function(evt) {
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
        }).on('declarative:success', '.js-delete-comment', function() {
            $(this).parents('.i-timeline-item').remove();
        }).on('declarative:success', '.js-edit-review', function(evt, data) {
            var $oldContent = $(this).parents('.i-timeline-item').find('.i-box-content');
            var $newContent = $(data.form_html);
            $oldContent.replaceWith($newContent);
            $newContent.find('.js-edit-cancel').on('indico:confirmed', function(evt_) {
                evt_.preventDefault();
                $newContent.replaceWith($oldContent);
            });
            initForms($newContent);
        }).on('indico:htmlUpdated', function(evt) {
            var $target = $(evt.target);
            initForms($target.find('form'));
            showFormErrors($target);
        }).on('focus', '.new-comment textarea', function() {
            var $commentForm = $(this).closest('form');
            $commentForm.find('.form-group').show('fast');
            $commentForm.removeClass('unfocused');
        }).on('click', '.new-comment', function(evt) {
            evt.stopPropagation();
        });

        $(window).on('click', function() {
            var $commentForm = $('form.new-comment');
            if (!$commentForm.find('textarea').val().trim().length) {
                $commentForm.addClass('unfocused');
                $commentForm.find('.form-group ~ .form-group').hide('fast');
            }
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
