/* This file is part of Indico.
 * Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

 $(function initEventLayout() {
    $('.menu-entries').sortable({
        handle: '.drag-handle',
        placeholder: 'menu-entry-placeholder'
    })
    .on('sortupdate', function(evt, ui) {
        $.ajax({
            url: ui.item.children('.menu-entry').data('position-url'),
            type: 'POST',
            dataType: 'json',
            data: { position: ui.item.prev().children('.menu-entry').data('position') },
            complete: IndicoUI.Dialogs.Util.progress(),
            success: function(data) {
                if (handleAjaxError(data)) {
                    return;
                }
            }
        });
    });
    $('#menu-entries').on('click', '.menu-entry > .i-label > .actions > .edit-entry', function(evt) {
        evt.preventDefault();
        evt.stopPropagation();
        ajaxDialog({
            trigger: this,
            url: $(this).data('href'),
            title: $T.gettext('Menu Entry Settings'),
            onClose: function(data) {
                if (data) {
                    $(this.trigger).closest('.menu-entry').replaceWith(data.entry);
                }
            }
        });
    });

    $(document).on('indico:confirmed', '.menu-entry .enabled, .menu-entry .not-enabled', function(evt) {
        evt.preventDefault();

        var $this = $(this);
        $.ajax({
            url: $this.data('href'),
            method: $this.data('method'),
            complete: IndicoUI.Dialogs.Util.progress(),
            error: handleAjaxError,
            success: function(data) {
                var is_enabled = data.is_enabled;
                $this.toggleClass('enabled', is_enabled)
                    .toggleClass('not-enabled', !is_enabled)
                    .parent('.actions')
                        .parent('.i-label').toggleClass('stripped', !is_enabled);
            }
        });
    }).on('indico:confirmed', '.menu-entry .delete-entry', function(evt) {
        evt.preventDefault();

        var $this = $(this);
        $.ajax({
            url: $this.data('href'),
            method: $this.data('method'),
            complete: IndicoUI.Dialogs.Util.progress(),
            error: handleAjaxError,
            success: function(data) {
                if (data) {
                    $this.closest('.menu-entries').replaceWith(data.menu);
                }
            }
        });
    });
 });
