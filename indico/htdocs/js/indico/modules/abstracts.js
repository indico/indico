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
            var $page = $('.management-page');

            evt.preventDefault();

            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                data: getFormParams($form),
                success: function(data) {
                    if (data.page_html) {
                        $page.replaceWith(data.page_html);
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
})(window);
