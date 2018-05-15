/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

    var FULL_ACCESS_PERMISSIONS = '_full_access';
    var READ_ACCESS_PERMISSIONS = '_read_access';

    $.widget('indico.permissionswidget', {
        options: {
            objectType: null,
            permissionsInfo: null
        },

        _update: function() {
            // Sort entries aphabetically and by type
            this.data = _.chain(this.data).sortBy(function(item) {
                return item[0].name || item[0].id;
            }).sortBy(function(item) {
                return item[0]._type;
            }).value();

            // Sort permissions alphabetically
            this.data.forEach(function(item) {
                item[1].sort();
            });

            this.$dataField.val(JSON.stringify(this.data));
            this.element.trigger('change');
        },
        _renderRoleCode: function(code, color) {
            return $('<span>', {
                class: 'role-code',
                text: code,
                css: {
                    borderColor: '#' + color,
                    color: '#' + color
                }
            });
        },
        _renderLabel: function(principal) {
            var $labelBox = $('<div>', {class: 'label-box flexrow f-a-center'});
            var type = principal._type;
            if (type === 'EventRole') {
                $labelBox.append(this._renderRoleLabel(principal));
            } else {
                $labelBox.append(this._renderOtherLabel(principal, type));
            }
            return $labelBox;
        },
        _renderRoleLabel: function(principal) {
            var $text = $('<span>', {
                class: 'text-normal entry-label',
                text: principal.name,
                'data-tooltip': principal.name
            });
            var $code = this._renderRoleCode(principal.code, principal.color);
            return [$code, $text];
        },
        _renderOtherLabel: function(principal, type) {
            var iconClass, extraText;
            if (type === 'Avatar') {
                iconClass = 'icon-user';
                extraText = principal.email;
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
            var tooltip = extraText ? '{0} ({1})'.format(text, extraText) : text;
            var textDiv = $('<div>', {class: 'text-normal entry-label', 'data-tooltip': tooltip});
            textDiv.append($('<span>', {text: text}));
            if (extraText) {
                textDiv.append('<br>');
                textDiv.append($('<span>', {class: 'text-not-important entry-label-extra', text: extraText}));
            }
            return [
                $('<span>', {class: 'entry-icon '  + iconClass}),
                textDiv
            ];
        },
        _renderPermissions: function(principal, permissions) {
            var self = this;
            var $permissions = $('<div>', {class: 'permissions-box flexrow f-a-center f-self-stretch'});
            var $permissionsList = $('<ul>').appendTo($permissions);
            // When full access is enabled, always show read access
            if (_.contains(permissions, FULL_ACCESS_PERMISSIONS) && !_.contains(permissions, READ_ACCESS_PERMISSIONS)) {
                permissions.push(READ_ACCESS_PERMISSIONS);
                if (principal._type !== 'DefaultEntry') {
                    self._updateItem(principal, permissions);
                }
            }
            permissions.forEach(function(item) {
                var permissionInfo = self.options.permissionsInfo[item];
                var applyOpacity = item === READ_ACCESS_PERMISSIONS && _.contains(permissions, FULL_ACCESS_PERMISSIONS)
                    && principal._type !== 'DefaultEntry';
                var cssClasses = (applyOpacity ? 'disabled ' : '') + permissionInfo.css_class;
                $permissionsList.append(
                    $('<li>', {class: 'i-label bold ' + cssClasses, title: permissionInfo.description})
                        .append(permissionInfo.title)
                );
            });
            if (principal._type !== 'DefaultEntry') {
                $permissions.append(this._renderPermissionsButtons(principal, permissions));
            }
            return $permissions;
        },
        _renderPermissionsButtons: function(principal, permissions) {
            var $buttonsGroup = $('<div>', {class: 'group flexrow'});
            $buttonsGroup.append(this._renderEditBtn(principal, permissions), this._renderDeleteBtn(principal));
            return $buttonsGroup;
        },
        _renderEditBtn: function(principal, permissions) {
            if (principal._type === 'IPNetworkGroup') {
                return $('<button>', {
                    type: 'button',
                    class: 'i-button text-color borderless icon-only icon-edit disabled',
                    title: $T.gettext('IP networks cannot have management permissions')
                });
            } else {
                return $('<button>', {
                    'type': 'button',
                    'class': 'i-button text-color borderless icon-only icon-edit',
                    'data-href': build_url(Indico.Urls.PermissionsDialog, {type: this.options.objectType}),
                    'data-title': $T.gettext('Assign Permissions'),
                    'data-method': 'POST',
                    'data-ajax-dialog': '',
                    'data-params': JSON.stringify({principal: JSON.stringify(principal), permissions: permissions})
                });
            }
        },
        _renderDeleteBtn: function(principal) {
            var self = this;
            return $('<button>', {
                'type': 'button',
                'class': 'i-button text-color borderless icon-only icon-remove',
                'data-principal': JSON.stringify(principal)
            }).on('click', function() {
                var $this = $(this);
                var confirmed;
                if (principal._type === 'Avatar' && principal.id === $('body').data('user-id')) {
                    var title = $T.gettext("Delete entry '{0}'".format(principal.name || principal.id));
                    var message = $T.gettext("Are you sure you want to remove yourself from the list?");
                    confirmed = confirmPrompt(message, title);
                } else {
                    confirmed = $.Deferred().resolve();
                }
                confirmed.then(function() {
                    self._updateItem($this.data('principal'), []);
                });
            });
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
            $dropdown.children(':not(.default)').remove();
            $dropdown.parent().dropdown({
                selector: '.js-dropdown'
            });
            var $dropdownLink = $dropdown.prev('.js-dropdown');
            var items = $dropdown.data('items');
            var isRoleDropdown = $dropdown.hasClass('entry-role-dropdown');
            items.forEach(function(item) {
                if (self._findEntryIndex(item) === -1) {
                    if (isRoleDropdown) {
                        $dropdown.find('.separator').before(self._renderDropdownItem(item));
                    } else {
                        $dropdown.append(self._renderDropdownItem(item));
                    }
                }
            });
            if (isRoleDropdown) {
                var isEmpty = !$dropdown.children().not('.default').length;
                $('.entry-role-dropdown .separator').toggleClass('hidden', isEmpty);
            } else if (!$dropdown.children().length) {
                $dropdownLink.addClass('disabled').attr('title', $T.gettext('All IP Networks were added'));
            } else {
                $dropdownLink.removeClass('disabled');
            }
        },
        _renderDropdownItem: function(principal) {
            var self = this;
            var $dropdownItem = $('<li>', {'class': 'entry-item', 'data-principal': JSON.stringify(principal)});
            var $itemContent = $('<a>');
            if (principal._type === 'EventRole') {
                $itemContent.append(this._renderRoleCode(principal.code, principal.color).addClass('dropdown-icon'));
            }
            var $text = $('<span>', {text: principal.name});
            $dropdownItem.append($itemContent.append($text)).on('click', function() {
                // Grant read access by default
                self._addItems([$(this).data('principal')], [READ_ACCESS_PERMISSIONS]);
            });
            return $dropdownItem;
        },
        _renderDuplicatesTooltip: function(idx) {
            this.$permissionsWidgetList.find('>li').not('.disabled').eq(idx).qtip({
                content: {
                    text: $T.gettext('This entry was already added')
                },
                show: {
                    ready: true,
                    effect: function() {
                        $(this).fadeIn(300);
                    }
                },
                hide: {
                    event: 'unfocus click'
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
                    classes: 'qtip-warning'
                }
            });
        },
        _render: function() {
            var self = this;
            this.$permissionsWidgetList.empty();

            this.data.forEach(function(item) {
                self.$permissionsWidgetList.append(self._renderItem(item));
            });
            // Add default entries
            var anonymous = [{_type: 'DefaultEntry', name: $T.gettext('Anonymous'), id: 'anonymous'},
                [READ_ACCESS_PERMISSIONS]];
            this.$permissionsWidgetList.append(this._renderItem(anonymous));

            var managersTitle = this.options.objectType === 'event' ?
                $T.gettext('Category Managers') : $T.gettext('Event Managers');
            var categoryManagers = [{_type: 'DefaultEntry', name: managersTitle}, [FULL_ACCESS_PERMISSIONS]];
            this.$permissionsWidgetList.prepend(this._renderItem(categoryManagers));
            this.$permissionsWidgetList.find('.anonymous').toggle(!this.isEventProtected);

            this._renderDropdown(this.$roleDropdown);
            if (this.$ipNetworkDropdown.length) {
                this._renderDropdown(this.$ipNetworkDropdown);
            }
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
        _addItems: function(principals, permissions) {
            var self = this;
            var news = [];
            var repeated = [];
            principals.forEach(function(principal) {
                var idx = self._findEntryIndex(principal);
                if (idx === -1) {
                    self.data.push([principal, permissions]);
                    news.push(principal);
                } else {
                    repeated.push(principal);
                }
            });
            this._update();
            this._render();
            news.forEach(function(principal) {
                self.$permissionsWidgetList.children('li:not(.disabled)').eq(self._findEntryIndex(principal))
                    .effect('highlight', {color: Palette.highlight}, 'slow');
            });
            repeated.forEach(function(principal) {
                self._renderDuplicatesTooltip(self._findEntryIndex(principal));
            });
        },
        _addUserGroup: function() {
            var self = this;
            function _addPrincipals(principals) {
                /// Grant read access by default
                self._addItems(principals, [READ_ACCESS_PERMISSIONS]);
            }

            var dialog = new ChooseUsersPopup(
                $T.gettext("Select a user or group to add"),
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

            // Manage changes on the permissions dialog
            this.element.on('indico:permissionsChanged', function(evt, permissions, principal) {
                self._updateItem(principal, permissions);
            });

            // Manage changes on the event protection mode field
            this.element.on('indico:protectionModeChanged', function(evt, isProtected) {
                self.isEventProtected = isProtected;
                self._render();
            });

            // Manage the addition to users/groups to the acl
            $('.js-add-user-group').on('click', function() {
                self._addUserGroup();
            });

            // Manage the creation of new roles
            $('.js-new-role').on('ajaxDialog:closed', function(evt, data) {
                if (data && data.role) {
                    self.$roleDropdown.data('items').push(data.role);
                    self._addItems([data.role], [READ_ACCESS_PERMISSIONS]);
                }
            });

            // Apply ellipsis + tooltip on long names
            this.$permissionsWidgetList.on('mouseenter', '.entry-label', function() {
                var $this = $(this);
                if (this.offsetWidth < this.scrollWidth && !$this.attr('title')) {
                    $this.attr('title', $this.attr('data-tooltip'));
                }
            });
        }
    });
})(jQuery);
