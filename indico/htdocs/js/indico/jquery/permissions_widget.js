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
        submit: 'warning'
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
            if (principal.type === 'role') {
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
                var iconClass = principal.type === 'user' ? 'icon-user' : 'icon-users';
                var text = principal.type === 'user' ? principal.name : principal.id;
                return $labelBox.append($('<span>', {class: 'label-icon text-normal ' + iconClass, text: text}));
            }
        },
        _renderPermissions: function(permissions) {
            var $permissions = $('<div>', {class: 'permissions-box flexrow f-a-center f-self-stretch'});
            var $permissionsList = $('<ul>').appendTo($permissions);
            permissions.forEach(function(item) {
                $permissionsList.append($('<li>', {class: 'i-label bold ' + permissionClasses[item]}).append(item));
            });

            var $permissionsEditBtn = $('<button>', {
                type: 'button',
                class: 'i-button text-color borderless icon-only icon-edit',
            });

            $permissionsEditBtn.ajaxDialog({
                url: build_url(Indico.Urls.EventPermissions, {confId: this.options.event_id}),
                title: $T.gettext('Assign Permissions'),
                // TODO: Provide real data & decide structure
                data: {
                    permissions: JSON.stringify([{
                        title: 'Event Management',
                        selected: false,
                        children: [
                            {
                                title: 'View',
                                selected: true
                            },
                            {
                                title: 'Manage Material',
                                selected: false
                            },
                            {
                                title: 'Manage Contributions',
                                selected: false
                            },
                            {
                                title: 'Manage Timetable',
                                selected: false
                            },
                            {
                                title: 'Manage Call for Abstracts',
                                selected: false,
                                children: [
                                    {
                                        title: 'Manage Programme',
                                        selected: false
                                    }
                                ]
                            },
                            {
                                title: 'Manage Call for Papers',
                                selected: false
                            }
                        ]
                    }])
                }
            });

            $permissionsEditBtn.appendTo($permissions);
            return $permissions;
        },
        _renderItem: function(item) {
            var $item = $('<li>', {class: 'flexrow f-a-center'});
            $item.append(this._renderLabel(item[0]));
            $item.append(this._renderPermissions(item[1]));
            return $item;
        },
        _render: function() {
            var self = this;
            this.data.permissions.forEach(function(item) {
                self.$permissionsWidgetList.append(self._renderItem(item));
            });
        },
        _create: function() {
            this.$permissionsWidgetList = this.element.find('.permissions-widget-list');
            this.$dataField = this.element.find('input[type=hidden]');
            this.data = JSON.parse(this.$dataField.val());
            this._render();
        }
    });
})(jQuery);
