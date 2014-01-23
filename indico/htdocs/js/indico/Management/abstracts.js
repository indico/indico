/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
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



// Drag and drop for the authors
$('#sortspace').tablesorter({

    onDropFail: function() {
        var popup = new AlertPopup($T('Warning'), $T('You cannot move the author to this list because there is already an author with the same email address.'));
        popup.open();
    },
    canDrop: function(sortable, element) {
        if (sortable.attr('id') == 'inPlacePrAuthors') {
            return authorsManager.canDropElement('pr', element.attr('id'));
        } else if (sortable.attr('id') == 'inPlaceCoAuthors') {
            return authorsManager.canDropElement('co', element.attr('id'));
        }
        return false;
    },
    onUpdate: function() {
        authorsManager.updatePositions();
        authorsManager.checkPrAuthorsList();
        return;
    },
    sortables: '.sortblock ul', // relative to element
    sortableElements: '> li', // relative to sortable
    handle: '.authorTable', // relative to sortable element - the handle to start sorting
    placeholderHTML: '<li></li>' // the html to put inside the placeholder element
});

// Pagedown editor stuff


function block_handler(text, rbg) {
    return text.replace(/^ {0,3}""" *\n((?:.*?\n)+?) {0,3}""" *$/gm, function (whole, inner) {
        return "<blockquote>" + rbg(inner) + "</blockquote>\n";
    });
}

$(function() {

    $('textarea.wmd-input:visible').each(function(i, elem) {
        $(elem).pagedown();
    });

    _(['markdown-info', 'latex-info', 'wmd-help-button']).each(function(name) {
        $('.' + name).qtip({
            content: $('#' + name + '-text').html(),
            hide: {
                event: 'unfocus'
            },
            show: {
                solo: true
            },
            style: {
                classes: 'informational'
            }
        }).click(function() {
            return false;
        });
    });
});
