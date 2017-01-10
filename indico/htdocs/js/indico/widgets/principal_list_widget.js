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

(function(global) {
    'use strict';

    global.setupPrincipalListWidget = function setupPrincipalListWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            eventId: null,
            openImmediately: false,
            groups: null,
            allowExternal: false,
            allowNetworks: false,
            networks: []
        }, options);

        var field = $('#' + options.fieldId);
        var principals = JSON.parse(field.val());

        function addPrincipal(newPrincipals, setResult) {
            // remove existing ones first to avoid duplicates
            newPrincipals = _.filter(newPrincipals, function(principal) {
                return !_.findWhere(principals, {identifier: principal.identifier});
            });
            principals = _.sortBy(principals.concat(newPrincipals), function(principal) {
                var weight = (principal._type == 'Avatar') ? 0 : (principal._type == 'Email' ? 1 : (principal.isGroup ? 2 : 3));
                var name = principal._type !== 'Email' ? principal.name : principal.email;
                return [weight, name.toLowerCase()];
            });
            field.val(JSON.stringify(principals));
            field.trigger('change');
            setResult(true, principals);
        }

        function removePrincipal(principal, setResult) {
            principals = _.without(principals, _.findWhere(principals, {
                identifier: principal.get('identifier')
            }));
            field.val(JSON.stringify(principals));
            field.trigger('change');
            setResult(true);
        }

        var widget = new UserListField(
            'PluginOptionPeopleListDiv', 'user-list', principals,
            true, null, true,
            options.groups,
            options.eventId,
            null, false, false, false,
            // Disable favorite button for EventPerson mode
            options.eventId !== null,
            addPrincipal, userListNothing, removePrincipal, options.allowExternal,
            options.allowNetworks, options.networks
        );

        $E('userGroupList-' + options.fieldId).set(widget.draw());

        if (options.openImmediately) {
            $('#userGroupList-' + options.fieldId + ' input[type=button]').trigger('click');
        }
    };
})(window);
