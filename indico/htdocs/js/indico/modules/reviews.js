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

/* global Palette:false */

(function(global) {
    'use strict';

    global.setupReviewingPage = function setupReviewingPage() {
        $('body').on('declarative:success', '.js-delete-comment', function() {
            $(this).closest('.i-timeline-item').remove();
        }).on('ajaxForm:show', '.js-edit-comment, .js-edit-review', function() {
            var $this = $(this);
            var $item = $this.closest('.i-timeline-item-box');
            if ($item.hasClass('header-indicator-top')) {
                $item.removeClass('header-indicator-top');
                $item.addClass('content-indicator-top');
            }
            if ($item.hasClass('header-indicator-left')) {
                $item.removeClass('header-indicator-left');
                $item.addClass('content-indicator-left');
            }
            if ($item.hasClass('header-only')) {
                $item.removeClass('header-only');
            }
            $this.closest('.i-box-header').hide();
        }).on('ajaxForm:hide', '.js-edit-comment, .js-edit-review', function() {
            var $this = $(this);
            var $item = $this.closest('.i-timeline-item-box');
            $this.closest('.i-box-header').show();
            if ($item.hasClass('content-indicator-top')) {
                $item.removeClass('content-indicator-top');
                $item.addClass('header-indicator-top');
            }
            if ($item.hasClass('content-indicator-left')) {
                $item.removeClass('content-indicator-left');
                $item.addClass('header-indicator-left');
            }
            if ($item.data('no-comment') !== undefined) {
                $item.addClass('header-only');
            }
        }).on('focus', '.new-comment textarea', function() {
            var $box = $('#review-timeline-input');
            var $commentForm = $box.find('form');
            $box.find('.review-trigger').hide('blind', {direction: 'left'}, 'fast');
            $commentForm.find('.form-group').show('fast');
            $commentForm.removeClass('unfocused');
            $commentForm.trigger('ajaxForm:externalShow');
        }).on('click', '.new-comment .js-new-cancel', function(evt) {
            evt.preventDefault();
            var $box = $('#review-timeline-input');
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
            var $reviewBox = $('#proposal-review-{0}'.format(reviewId));
            $reviewBox.find('.js-edit-review').trigger('click');
            $('body, html').animate({scrollTop: $reviewBox.offset().top}, 'fast');
            $reviewBox.find('.i-timeline-item-box').effect('highlight', {color: Palette.highlight}, 'slow');
        }).on('click', '.js-ratings-toggle', function() {
            var $this = $(this);
            $this.find('.js-show-ratings, .js-hide-ratings').toggleClass('weak-hidden');
            var $reviewBox = $this.closest('.i-timeline-item-box');
            if ($reviewBox.data('no-comment') !== undefined) {
                if ($reviewBox.hasClass('header-only')) {
                    $reviewBox.removeClass('header-only');
                    $reviewBox.find('.ratings-details').slideToggle('fast');
                } else {
                    $reviewBox.addClass('header-only-transition');
                    $reviewBox.find('.ratings-details').slideToggle('fast', function() {
                        $reviewBox.removeClass('header-only-transition');
                        $reviewBox.addClass('header-only');
                    });
                }
            } else {
                $reviewBox.find('.ratings-details').slideToggle('fast');
            }
            $this.toggleClass('open');
        }).on('click', '.js-highlight-review', function() {
            $($(this).attr('href') + ' .i-box-header').effect('highlight', {color: Palette.highlight}, 'slow');
        });
    };
})(window);
