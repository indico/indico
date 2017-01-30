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

(function($) {
    'use strict';

    $.widget('indico.principalfield', {
        options: {
            eventId: null,
            suggestedUsers: null,
            allowExternalUsers: true,
            allowEmptyEmail: false,
            enableGroupsTab: false,
            multiChoice: false,
            overwriteChoice: true,
            showFavoriteUsers: true,
            render: function(people) {},
            onAdd: function(people) {},
            onRemove: function() {}
        },

        _create: function _create() {
            var self = this;
            self.people = JSON.parse(self.element.val() || '[]');
            self.options.render(self.people);
        },

        _update: function _update() {
            var self = this;
            var people = self.people ? JSON.stringify(self.people) : '[]';
            self.element.val(people);
            self.element.trigger('change');
            self.options.render(self.people);
        },

        add: function add(people) {
            var self = this;

            function getUserId(obj) {
                if (obj._type === 'Avatar') {
                    return obj.id;
                } else if (obj._type === 'EventPerson') {
                    return obj.user_id;
                }
            }

            function comparePersons(a, b) {
                var aUserId = getUserId(a);
                var bUserId = getUserId(b);


                if (a._type === b._type
                    && a.id !== undefined && b.id !== undefined
                    && a.id === b.id) {
                    return true;
                }

                if (aUserId !== undefined && bUserId !== undefined
                    && aUserId === bUserId) {
                    return true;
                }

                return !!a.email && !!b.email && a.email.toLowerCase() === b.email.toLowerCase();
            }

            function deduplicate(people) {
                var newPeople = [];
                people.forEach(function(person) {
                    var found = _.find(newPeople, function(newPerson) {
                        return comparePersons(person, newPerson);
                    });
                    if (!found) {
                        newPeople.push(person);
                    }
                });
                return newPeople;
            }

            function skipExisting(people) {
                _.each(self.people, function(person) {
                    people = _.without(people, _.find(people, function(p) {
                        return comparePersons(person, p);
                    }));
                });
                return people;
            }

            people = deduplicate(people);
            self.people = self.options.overwriteChoice ? people : self.people.concat(skipExisting(people));
            self.people = _.sortBy(self.people, 'name');
            self.options.onAdd(self.people);
            self._update();
        },

        choose: function choose() {
            var self = this;
            function handle(people) { self.add(people); }
            var userChoosePopup = new ChooseUsersPopup($T("Choose person"), true, self.options.eventId,
                                                       self.options.enableGroupsTab, self.options.showFavoriteUsers,
                                                       self.options.suggestedUsers, !self.options.multiChoice,
                                                       true, false, handle, null,
                                                       self.options.allowExternalUsers);
            userChoosePopup.execute();
        },

        edit: function edit(personId) {
            var self = this;
            var person = _.findWhere(self.people, {id: personId});
            function handle(person) { self.set(person.get('id'), person.getAll()); }
            var personEditPopup = new UserDataPopup($T("Edit information"), $O(person), handle, false, false, false,
                                                    self.options.allowEmptyEmail);
            personEditPopup.open();
        },

        enter: function enter() {
            var self = this;
            function handle(person) { self.add([person.getAll()]); }
            var personCreatePopup = new UserDataPopup($T("Enter person"), $O(), handle, false, false, false,
                                                      self.options.allowEmptyEmail);
            personCreatePopup.open();
        },

        remove: function remove() {
            var self = this;
            self.people = [];
            self.options.onRemove();
            self._update();
        },

        removeOne: function removeOne(personId) {
            var self = this;
            var person = _.findWhere(self.people, {id: personId});
            self.people = _.without(self.people, person);
            self._update();
        },

        set: function set(personId, data) {
            var self = this;
            var person = _.findWhere(self.people, {id: personId});
            $.extend(person, data);
            self._update();
        },

        refresh: function refresh() {
            this._update();
        }
    });
})(jQuery);
