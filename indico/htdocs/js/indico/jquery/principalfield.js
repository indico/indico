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
            multiChoice: false,
            overwriteChoice: true,
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

        _add: function _add(people) {
            var self = this;

            function cleanDuplicates(people) {
                _.each(self.users, function(person) {
                    people = _.without(people, _.findWhere(people, {
                        _type: person._type,
                        id: person.id
                    }));
                });
                return people;
            }

            self.users = self.options.overwriteChoice? people : self.users.concat(cleanDuplicates(people));
            self.options.onSelect(self.users);
            self._update();
        },

        choose: function choose() {
            var self = this;
            function handle(people) { self._add(people); }
            var userChoosePopup = new ChooseUsersPopup($T("Choose person"), true, self.options.eventId,
                                                       self.options.enableGroupsTab, self.options.showFavoriteUsers,
                                                       self.options.suggestedUsers, !self.options.multiChoice,
                                                       true, false, handle, null,
                                                       self.options.allowExternalUsers);
            userChoosePopup.execute();
        },

        enter: function enter() {
            var self = this;
            function handle(person) { self._add([person.getAll()]); }
            var personCreatePopup = new UserDataPopup($T("Enter person"), $O(), handle, false, false, false, false);
            personCreatePopup.open();
        },

        remove: function remove() {
            var self = this;
            self.users = [];
            self.options.onRemove();
            self._update();
        },

        removeOne: function removeOne(userId) {
            var self = this;
            var user = _.findWhere(self.users, {id: userId});
            self.users = _.without(self.users, user);
            self._update();
        },

        set: function set(userId, data) {
            var self = this;
            var user = _.findWhere(self.users, {id: userId});
            $.extend(user, data);
            self._update();
        }
    });
})(jQuery);
