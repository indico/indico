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

type("RoomListWidget", ["ListWidget"],
    {
        _drawItem: function(room) {
            var self = this;
            var roomData = room.get();

            var removeButton = Widget.link(command(function() {
                self.removeProcess(room.key, function(result) {
                    if (result) {
                        self.set(room, null);
                    }
                });
            }, IndicoUI.Buttons.removeButton()));
            return Html.div({style:{display: 'inline'}},
                            Html.span({},
                                    Html.div({style: {cssFloat: "right", paddingRight: "10px"}},removeButton),
                                    $B(Html.span(), self.useValue ? roomData : room.key)
                                    ));
        }
    },

    function(style, removeProcess, useValue) {
        this.removeProcess = removeProcess;
        this.useValue = useValue || false;
        if (!exists(style)) {
            style = "user-list";
        }
        this.ListWidget(style);
    }
);
