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

$(function() {
    'use strict';

    var resultCache = [];
    var allItems = $(".index .item");

    $("#filter_text").keyup(function(){
        var searchString = $(this).val();

        allItems.addClass('visibility_hidden');
        var items;
        if (resultCache[searchString] === undefined) {
            items = $(".index .item .text").textContains(searchString).parent().parent();
            resultCache[searchString] = items;
        } else {
            items = resultCache[searchString];
        }
        items.removeClass('visibility_hidden');

        $("#numberFiltered").text(items.length);
        $("#numberFilteredText").text(items.length === 1 ? $T("author") : $T("authors"));
    });

    $(".material_icon").each(function() {
        $(this).qtip({
            style: {
                classes: 'material_tip'
            },
            content: {
                text: $(this).siblings('.material_list')
            },
            show: {
                event: 'click'
            },
            hide: {
                event: 'unfocus'
            },
            position: {
                my: 'top right',
                at: 'bottom left'
            }
        });
    });
});
