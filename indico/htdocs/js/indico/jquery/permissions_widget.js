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

    var permissionClasses = {
        access: 'accept',
        timetable: 'highlight',
        edit: 'danger',
        material: 'warning'
    };

    $.widget('indico.permissionswidget', {
        options: {
            event_id: null
        },

        _update: function() {
            this.$dataField.val(JSON.stringify(this.data));
        },
        _renderLabel: function(principal) {
            var $labelBox = $('<div>', {class: 'label-box'});
            var type = principal._type;
            if (type === 'EventRole') {
                var $text = $('<span>', {class: 'text-normal', text: principal.name});
                var $code = $('<span>', {
                    class: 'role-code',
                    text: principal.code,
                    css: {
                        'border-color': '#' + principal.color,
                        'color': '#' + principal.color
                    }
                });

                return $labelBox.append($('<span>', {class: 'flexrow f-a-center'}).append($code).append($text));
            } else {
                var iconClass = type === 'Avatar' || type === 'Email' ? 'icon-user' : 'icon-users';
                var text = type === 'Avatar' ? principal.name : principal.id;
                return $labelBox.append($('<span>', {class: 'label-icon text-normal ' + iconClass, text: text}));
            }
        },
        _renderPermissions: function(principal, permissions) {
            var self = this;
            var $permissions = $('<div>', {class: 'permissions-box flexrow f-a-center f-self-stretch'});
            var $permissionsList = $('<ul>').appendTo($permissions);
            permissions.forEach(function(item) {
                $permissionsList.append($('<li>', {class: 'i-label bold ' + permissionClasses[item]}).append(item));
            });

            var $buttonsGroup = $('<div>', {class: 'group flexrow'});
            var $permissionsEditBtn = $('<button>', {
                'type': 'button',
                'class': 'i-button text-color borderless icon-only icon-edit',
                'data-href': build_url(Indico.Urls.EventPermissions, {confId: this.options.event_id}),
                'data-title': $T.gettext('Assign Permissions'),
                'data-ajax-dialog': '',
                'data-params': JSON.stringify({principal: JSON.stringify(principal), permissions: permissions})
            });

            var $entryDeleteBtn = $('<button>', {
                'type': 'button',
                'class': 'i-button text-color borderless icon-only icon-remove',
                'data-principal': JSON.stringify(principal)
            }).on('click', function() {
                var $this = $(this);
                var title = $T.gettext("Delete entry '{0}'".format(principal.name || principal.id));
                var message = $T.gettext("Are you sure you want to permanently delete this entry?");
                confirmPrompt(message, title).then(function() {
                    self._updateItem($this.data('principal'), []);
                });
            });

            $buttonsGroup.append($permissionsEditBtn, $entryDeleteBtn);
            $buttonsGroup.appendTo($permissions);
            return $permissions;
        },
        _renderItem: function(item) {
            var $item = $('<li>', {class: 'flexrow f-a-center'});
            $item.append(this._renderLabel(item[0]));
            $item.append(this._renderPermissions(item[0], item[1]));
            return $item;
        },
        _render: function() {
            var self = this;
            this.$permissionsWidgetList.empty();
            this.data.forEach(function(item) {
                self.$permissionsWidgetList.append(self._renderItem(item));
            });
        },
        _findEntryIndex: function(principal) {
            var idx = _.findIndex(this.data, function(item) {
                return _.isMatch(item[0], principal);
            });
            return idx;
        },
        _updateItem: function(principal, newPermissions) {
            var idx = this._findEntryIndex(principal);
            if (newPermissions.length) {
                this.data[idx][1] = newPermissions;
            } else {
                this.data.splice(idx, 1);
            }
            this._update();
            this._render();
            $('#permissions-widget-permissions').trigger('change');
        },
        _create: function() {
            var self = this;
            this.$permissionsWidgetList = this.element.find('.permissions-widget-list');
            this.$dataField = this.element.find('input[type=hidden]');
            this.data = JSON.parse(this.$dataField.val());
            this._render();

            $('#permissions-widget-permissions').on('indico:permissionsChanged', function(evt, permissions, principal) {
                self._updateItem(principal, permissions);
            });
        }
    });
})(jQuery);
