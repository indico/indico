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

/* global choiceConfirmPrompt:false */

(function(global) {
    'use strict';

    // TODO: Add plugin i18n
    var $t = $T;

    global.eventManageVCRooms = function() {
        $('.js-vcroom-remove').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);
            var title, msg;

            function execute(url) {
                var csrf = $('<input>', {
                    type: 'hidden',
                    name: 'csrf_token',
                    value: $('#csrf-token').attr('content')
                });
                $('<form>', {
                    action: url,
                    method: 'post'
                }).append(csrf).appendTo('body').submit();
            }

            if ($this.data('numEvents') === 1) {
                title = $t('Delete videoconference room');
                msg = $t('Do you really want to remove this videoconference room from the event?') + ' ' +
                      $t('Since it is only used in this event, it will be deleted from the server, too!');
                confirmPrompt(msg, title).then(function() {
                    execute($this.data('href'));
                });
            } else {
                title = $t('Detach videoconference room');
                msg = $t.ngettext(
                    '*',
                    'This videoconference room is used in other Indico events.<br>Do you want to \
                     <strong>delete</strong> it from all {0} events or just <strong>detach</strong> \
                     it from this event?',
                    $this.data('numEvents')
                ).format($this.data('numEvents'));
                choiceConfirmPrompt(msg, title, $t('Detach'), $t('Delete')).then(function(choice) {
                    var url = build_url($this.data('href'), {delete_all: choice === 2 ? '1' : ''});
                    execute(url);
                });
            }
        });

        $('.js-vcroom-refresh').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);
            var csrf = $('<input>', {type: 'hidden', name: 'csrf_token', value: $('#csrf-token').attr('content')});
            $('<form>', {
                action: $this.data('href'),
                method: 'post'
            }).append(csrf).appendTo('body').submit();
        });

        $('.vc-room-entry.deleted').qtip({
            content: $T('This room has been deleted and cannot be used. \
                         You can detach it from the event, however.'),
            position: {
                my: 'top center',
                at: 'bottom center'
            }
        });

        $('.toggle-details').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);

            if ($this.closest('.vc-room-entry.deleted').length) {
                return;
            }

            $this.closest('tr').next('tr').find('.details-container').slideToggle({
                start: function() {
                    $this.toggleClass('icon-next icon-expand');
                }
            });
        }).filter('.vc-room-entry:not(.deleted) .toggle-details')
          .qtip({content: $T('Click to toggle collapse status')});

        $('.toggle .i-button').on('click', function(){
            var toggle = $(this);
            toggle.toggleClass('icon-eye icon-eye-blocked');
            var $input = toggle.siblings('input');
            $input.prop('type', $input.prop('type') === 'text' ? 'password' : 'text');
        });
    };
})(window);
