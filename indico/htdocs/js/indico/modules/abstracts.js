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

/* global setupListGenerator:false, setupSearchBox:false */

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
        var applySearchFilters = setupListGenerator(filterConfig);
        abstractListContainer.on('indico:htmlUpdated', function() {
            abstractListContainer.find('.js-mathjax').mathJax();
            _.defer(applySearchFilters);
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

            if ($this.hasClass('disabled')) {
                return;
            }

            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                data: JSON.stringify({stop_on_match: stopOnMatch}),
                dataType: 'json',
                contentType: 'application/json',
                error: handleAjaxError,
                success: function() {
                    $this.data('stop-on-match', stopOnMatch);
                    $this.toggleClass('stop-processing-enabled', stopOnMatch);
                }
            });
        });
    };

    global.setupCallForAbstractsPage = function setupCallForAbstractsPage(options) {
        options = $.extend({
            hasAbstracts: false
        }, options);

        // show the form after login when using the submit button as a guest
        if (location.hash === '#submit-abstract') {
            $(document).ready(function() {
                $('.js-show-abstract-form').trigger('click');
            });
        }

        if (options.hasAbstracts) {
            var filterConfig = {
                itemHandle: 'div.contribution-row',
                listItems: '#display-contribution-list div.contribution-row',
                term: '#search-input',
                state: '#filtering-state',
                placeholder: '#filter-placeholder'
            };

            var applySearchFilters = setupSearchBox(filterConfig);
            applySearchFilters();
        }
    };
})(window);
