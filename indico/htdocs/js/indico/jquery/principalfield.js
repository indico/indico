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

(function($) {
    'use strict';

    $.widget('indico.principalfield', {
        options: {
            eventId: null,
            suggestedUsers: null,
            allowExternalUsers: true,
            enableGroupsTab: false,
            showFavoriteUsers: true,
            render: function(users) {},
            onRemove: function() {},
            onSelect: function(users) {},
        },

        _create: function _create() {
            var self = this;
            self.users = JSON.parse(self.element.val() || '[]');
            self.options.render(self.users);
        },

        _update: function _update() {
            var self = this;
            var users = self.users ? JSON.stringify(self.users) : '[]';
            self.element.val(users);
            self.element.trigger('change');
            self.options.render(self.users);
        },

        choose: function choose() {
            var self = this;
            function handleUsersChosen(users) {
                self.users = users;
                self.options.onSelect(self.users);
                self._update();
            }
            var userChoosePopup = new ChooseUsersPopup($T("Choose user"), true, self.options.eventId,
                                                       self.options.enableGroupsTab, self.options.showFavoriteUsers,
                                                       self.options.suggestedUsers, true, true, false,
                                                       handleUsersChosen, null,
                                                       self.options.allowExternalUsers);
            userChoosePopup.execute();
        },

        remove: function remove() {
            var self = this;
            self.users = [];
            self.options.onRemove();
            self._update();
        }
    });
})(jQuery);
