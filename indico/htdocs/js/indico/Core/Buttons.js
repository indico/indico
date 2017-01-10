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

IndicoUI.Buttons = {
    /**
        * Returns an image with an 'remove' icon
        */
    removeButton: function(faded, fadedCaption){
        var caption = faded ? (exists(fadedCaption)? fadedCaption : 'Remove (blocked)') : 'Remove';
        return Html.img({
            alt: caption,
            title: caption,
            src: faded ? imageSrc("remove_faded") : imageSrc("remove"),
            style: {
                'marginLeft': '5px',
                'verticalAlign': 'middle'
            }
        });
    },
    /**
        * Returns an image with an 'edit' icon
        */
    editButton: function(faded, fadedCaption){
        var caption = faded ? (exists(fadedCaption) ? fadedCaption: 'Edit (blocked)') : 'Edit';
        return Html.img({

            alt: caption,
            title: caption,
            src: faded ? imageSrc("edit_faded") : imageSrc("edit"),
            style: {
                'marginLeft': '5px',
                'verticalAlign': 'middle'
            }
        });
    }
};
