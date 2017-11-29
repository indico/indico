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

/* global ChooseUsersPopup:false */

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
            this.element.trigger('change');
        },
        _renderRoleCode: function(code, color) {
            return $('<span>', {
                class: 'role-code',
                text: code,
                css: {
                    'border-color': '#' + color,
                    'color': '#' + color
                }
            });
        },
        _renderLabel: function(principal) {
            var $labelBox = $('<div>', {class: 'label-box'});
            var type = principal._type;
            if (type === 'EventRole') {
                var $text = $('<span>', {class: 'text-normal entry-label', text: principal.name});
                var $code = this._renderRoleCode(principal.code, principal.color);
                return $labelBox.append($('<span>', {class: 'flexrow f-a-center'}).append($code).append($text));
            } else {
                var iconClass;
                if (type === 'Avatar') {
                    iconClass = 'icon-user';
                } else if (type === 'Email') {
                    iconClass = 'icon-mail';
                } else {
                    iconClass = 'icon-users';
                }
                var text = type === 'Avatar' ? principal.name : principal.id;
                $labelBox.addClass('entry-label');
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
        _renderRoleDropdown: function() {
            var self = this;
            self.$roleDropdown.empty();
            var $roleDropdownLink = self.$roleDropdown.siblings('.js-dropdown');
            var eventRoles = self.$roleDropdown.data('event-roles');
            if (eventRoles.length) {
                eventRoles.forEach(function(role) {
                    if (self._findEntryIndex(role) === -1) {
                        self.$roleDropdown.append(self._renderRoleDropdownItem(role));
                    }
                });
                if (!self.$roleDropdown.children().length) {
                    $roleDropdownLink.addClass('disabled').attr('title', $T('All event roles were added'));
                } else {
                    $roleDropdownLink.removeClass('disabled');
                }
            } else {
                $roleDropdownLink.addClass('disabled').attr('title', $T('No roles created in this event'));
            }
        },
        _renderRoleDropdownItem: function(role) {
            var self = this;
            var $roleDropdownItem = $('<li>', {'class': 'role-item js-add-role', 'data-role': JSON.stringify(role) });
            var $code = this._renderRoleCode(role.code, role.color);
            var $text = $('<span>', {text: role.name});
            $roleDropdownItem.append($('<a>').append($code).append($text)).on('click', function() {
                self._addRole($(this).data('role'));
                $('#permissions-add-entry-menu-target').qbubble('hide');
            });
            return $roleDropdownItem;
        },
        _render: function() {
            var self = this;
            this.$permissionsWidgetList.empty();
            // TODO: Sort list properly
            this.data.forEach(function(item) {
                self.$permissionsWidgetList.append(self._renderItem(item));
            });
            this._renderRoleDropdown();
        },
        _findEntryIndex: function(principal) {
            return _.findIndex(this.data, function(item) {
                return item[0].identifier === principal.identifier;
            });
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
        },
        _addItem: function(principal, permissions) {
            var idx = this._findEntryIndex(principal);
            if (idx === -1) {
                this.data.push([principal, permissions]);
                this._update();
                this._render();
            } else {
                this.$permissionsWidgetList.find('>li').eq(idx).qtip({
                    content: {
                        text: $T('This entry was already added')
                    },
                    show: {
                        ready: true,
                        effect: function() {
                            $(this).fadeIn(300);
                        }
                    },
                    hide: {
                        event: 'unfocused click'
                    },
                    events: {
                        hide: function() {
                            $(this).fadeOut(300);
                            $(this).qtip('destroy');
                        }
                    },
                    position: {
                        my: 'center left',
                        at: 'center right'
                    },
                    style: {
                        classes: 'qtip-danger'
                    }
                });
            }
        },
        _addUserGroup: function() {
            var self = this;
            function _addPrincipals(principals) {
                principals.forEach(function(principal) {
                    // Grant 'access' permissions when a user/group is added for the first time.
                    self._addItem(principal, ['access']);
                });
            }

            var dialog = new ChooseUsersPopup(
                $T("Select a user or group to add"),
                true, null, true, true, null, false, false, false, _addPrincipals, null, true
            );

            dialog.execute();
        },
        _addRole: function(role) {
            // Grant 'access' permissions when a role is added for the first time.
            this._addItem(role, ['access']);
        },
        _create: function() {
            var self = this;
            this.$permissionsWidgetList = this.element.find('.permissions-widget-list');
            this.$dataField = this.element.find('input[type=hidden]');
            this.$roleDropdown = this.element.find('.entry-role-dropdown');
            this.data = JSON.parse(this.$dataField.val());
            this._render();

            this.element.on('indico:permissionsChanged', function(evt, permissions, principal) {
                self._updateItem(principal, permissions);
            });

            $('.js-add-user-group').on('click', function() {
                self._addUserGroup();
            });

            this.$permissionsWidgetList.on('mouseenter', '.entry-label', function() {
                var $this = $(this);
                if (this.offsetWidth < this.scrollWidth && !$this.attr('title')) {
                    $this.attr('title', $this.text());
                }
            });

            $('#permissions-add-entry-menu-target').qbubble({
                content: {
                    text: $('#permissions-add-entry-menu')
                },
                style: {
                    classes: 'qtip-allow-overflow'
                },
                position: {
                    my: 'top right',
                    at: 'bottom right'
                }
            });
        }
    });
})(jQuery);
