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

/* global ChooseUsersPopup:false, Palette:false */

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
            this.data = _(this.data).chain().sortBy(function(item) {
                return item[0].name || item[0].id;
            }).sortBy(function(item) {
                return item[0]._type;
            }).value();

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
                } else if (type === 'DefaultEntry' && principal.id === 'anonymous') {
                    iconClass = 'icon-question';
                } else if (type === 'IPNetworkGroup') {
                    iconClass = 'icon-lan';
                } else {
                    iconClass = 'icon-users';
                }
                var labelIsName = _.contains(['Avatar', 'DefaultEntry', 'IPNetworkGroup'], type);
                var text = labelIsName ? principal.name : principal.id;
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

            if (principal._type !== 'DefaultEntry') {
                var $buttonsGroup = $('<div>', {class: 'group flexrow'});
                if (principal._type !== 'IPNetworkGroup') {
                    var $permissionsEditBtn = $('<button>', {
                        'type': 'button',
                        'class': 'i-button text-color borderless icon-only icon-edit',
                        'data-href': build_url(Indico.Urls.EventPermissions, {confId: this.options.event_id}),
                        'data-title': $T.gettext('Assign Permissions'),
                        'data-ajax-dialog': '',
                        'data-params': JSON.stringify({principal: JSON.stringify(principal), permissions: permissions})
                    });
                    $buttonsGroup.append($permissionsEditBtn);
                }

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

                $buttonsGroup.append($entryDeleteBtn);
                $buttonsGroup.appendTo($permissions);
            }
            return $permissions;
        },
        _renderItem: function(item) {
            var $item = $('<li>', {class: 'flexrow f-a-center'});
            var principal = item[0];
            var permissions = item[1];
            $item.append(this._renderLabel(principal));
            $item.append(this._renderPermissions(principal, permissions));
            $item.toggleClass('disabled ' + principal.id, principal._type === 'DefaultEntry');
            return $item;
        },
        _renderDropdown: function($dropdown) {
            var self = this;
            $dropdown.empty();
            var $dropdownLink = $dropdown.prev('.js-dropdown');
            var items = $dropdown.data('items');
            var isRoleDropdown = $dropdown.hasClass('entry-role-dropdown');
            var tooltip;
            if (items.length) {
                items.forEach(function(item) {
                    if (self._findEntryIndex(item) === -1) {
                        $dropdown.append(self._renderDropdownItem(item));
                    }
                });
                if (!$dropdown.children().length) {
                    tooltip = isRoleDropdown ? $T('All event roles were added') : $T('All IP Networks were added');
                    $dropdownLink.addClass('disabled').attr('title', tooltip);
                } else {
                    $dropdownLink.removeClass('disabled');
                }
            } else {
                tooltip = isRoleDropdown ? $T('No roles created in this event') : $T('No IP Networks created');
                $dropdownLink.addClass('disabled').attr('title', tooltip);
            }
        },
        _renderDropdownItem: function(principal) {
            var self = this;
            var $dropdownItem = $('<li>', {'class': 'entry-item', 'data-principal': JSON.stringify(principal)});
            var $itemContent = $('<a>');
            if (principal._type === 'EventRole') {
                var $code = this._renderRoleCode(principal.code, principal.color);
                $itemContent.append($code);
            }
            var $text = $('<span>', {text: principal.name});
            $dropdownItem.append($itemContent.append($text)).on('click', function() {
                // Grant 'access' permissions when a role / IP Network is added.
                self._addItem($(this).data('principal'), ['access']);
                $('#permissions-add-entry-menu-target').qbubble('hide');
            });
            return $dropdownItem;
        },
        _render: function() {
            var self = this;
            this.$permissionsWidgetList.empty();

            this.data.forEach(function(item) {
                self.$permissionsWidgetList.append(self._renderItem(item));
            });
            // Add default entries
            var categoryManagers = [{
                _type: 'DefaultEntry', name: $T('Category Managers'), id: 'category-managers'
            }, ['edit']];
            var anonymous = [{_type: 'DefaultEntry', name: $T('Anonymous'), id: 'anonymous'}, ['access']];
            self.$permissionsWidgetList.prepend(self._renderItem(categoryManagers));
            self.$permissionsWidgetList.append(self._renderItem(anonymous));
            self.$permissionsWidgetList.find('.anonymous').toggle(!self.isEventProtected);

            this._renderDropdown(this.$roleDropdown);
            this._renderDropdown(this.$ipNetworkDropdown);
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
                var newIdx = this._findEntryIndex(principal);
                this.$permissionsWidgetList.find('>li').not('.disabled').eq(newIdx)
                    .effect('highlight', {color: Palette.highlight}, 'slow');
            } else {
                this.$permissionsWidgetList.find('>li').not('.disabled').eq(idx).qtip({
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
        _create: function() {
            var self = this;
            this.$permissionsWidgetList = this.element.find('.permissions-widget-list');
            this.$dataField = this.element.find('input[type=hidden]');
            this.$roleDropdown = this.element.find('.entry-role-dropdown');
            this.$ipNetworkDropdown = this.element.find('.entry-ip-network-dropdown');
            this.data = JSON.parse(this.$dataField.val());
            this._update();
            this._render();

            this.element.on('indico:permissionsChanged', function(evt, permissions, principal) {
                self._updateItem(principal, permissions);
            });

            this.element.on('indico:protectionModeChanged', function(evt, isProtected) {
                self.isEventProtected = isProtected;
                self._render();
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
