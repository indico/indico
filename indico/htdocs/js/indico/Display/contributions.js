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

$(function() {
    $('.information .trigger').click(function() {
            var $this = $(this),
            transition_opts = {
                duration: 250,
                easing: 'easeInQuad'
            };

        if ($this.data('hidden')) {
            $this.siblings('.extra-parameters').slideDown(transition_opts);
            $this.data('hidden', false).removeClass('icon-expand').addClass('icon-collapse');
        } else {
            $this.siblings('.extra-parameters').slideUp(transition_opts);
            $this.data('hidden', true).removeClass('icon-collapse').addClass('icon-expand');
        }
    });

    $('.icon-user, .track-assignment, .session-assignment').bind('mouseenter', function (){
        var $this = $(this);
        if (this.offsetWidth < this.scrollWidth && !$this.attr('title')) {
            $this.attr('title', $this.text());
        }
    });

    $('.content, h1').mathJax();
});
