/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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

import rbURL from 'indico-url:rooms_new.roombooking';


$(document).ready(() => {
    $('#contribution, #session_block').on('change', (e) => {
        const $target = $(e.currentTarget);
        const $bookBtn = $target.closest('.searchable-field').find('.js-book-btn');
        const linkType = {
            contribution: 'contribution',
            session_block: 'sessionBlock',
        }[$target.attr('id')];
        const params = {
            link_type: linkType,
            link_id: $target.val(),
        };
        $bookBtn
            .toggleClass('disabled', !$target.val())
            .attr('href', rbURL({path: 'book', ...params}));
    });
});
