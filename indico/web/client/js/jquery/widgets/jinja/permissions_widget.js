// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global ChooseUsersPopup:false */

import Palette from 'indico/utils/palette';

(function($) {
  const FULL_ACCESS_PERMISSIONS = '_full_access';
  const READ_ACCESS_PERMISSIONS = '_read_access';

  $.widget('indico.permissionswidget', {
    options: {
      objectType: null,
      permissionsInfo: null,
      hiddenPermissions: null,
      hiddenPermissionsInfo: null,
    },

    _update() {
      // Sort entries aphabetically and by type
      this.data = _.chain(this.data)
        .sortBy(item => item[0].name || item[0].id)
        .sortBy(item => item[0]._type)
        .value();

      // Sort permissions alphabetically
      this.data.forEach(item => {
        item[1].sort();
      });

      this.$dataField.val(JSON.stringify(this.data));
      this.element.trigger('change');
    },
    _renderRoleCode(code, color) {
      return $('<span>', {
        class: 'role-code',
        text: code,
        css: {
          borderColor: `#${color}`,
          color: `#${color}`,
        },
      });
    },
    _renderLabel(principal) {
      const $labelBox = $('<div>', {class: 'label-box flexrow f-a-center'});
      const type = principal._type;
      if (type === 'EventRole') {
        $labelBox.append(this._renderEventRoleLabel(principal));
      } else if (type === 'CategoryRole') {
        $labelBox.append(this._renderCategoryRoleLabel(principal));
      } else {
        $labelBox.append(this._renderOtherLabel(principal, type));
      }
      return $labelBox;
    },
    _renderEventRoleLabel(principal) {
      const $text = $('<span>', {
        'class': 'text-normal entry-label',
        'text': principal.name,
        'data-tooltip-text': principal.name,
      });
      const $code = this._renderRoleCode(principal.code, principal.color);
      return [$code, $text];
    },
    _renderCategoryRoleLabel(principal) {
      const text = principal.name;
      const extraText = principal.category;
      const $code = this._renderRoleCode(principal.code, principal.color);
      const tooltip = `${text} (${extraText})`;
      const textDiv = $('<div>', {
        'class': 'text-normal entry-label',
        'data-tooltip-text': tooltip,
      });
      textDiv.append($('<span>', {text}));
      textDiv.append('<br>');
      textDiv.append($('<span>', {class: 'text-not-important entry-label-extra', text: extraText}));
      return [$code, textDiv];
    },
    _renderOtherLabel(principal, type) {
      let iconClass, extraText;
      if (type === 'Avatar') {
        iconClass = 'icon-user';
        extraText = principal.email;
      } else if (type === 'Email') {
        iconClass = 'icon-mail';
      } else if (type === 'DefaultEntry' && principal.id === 'anonymous') {
        iconClass = 'icon-question';
      } else if (type === 'IPNetworkGroup') {
        iconClass = 'icon-lan';
      } else if (type === 'LocalGroup') {
        iconClass = 'icon-users';
      } else if (type === 'MultipassGroup') {
        iconClass = 'icon-users';
        extraText = principal.provider_title;
      } else {
        iconClass = 'icon-users';
      }
      const text = principal.name;
      const tooltip = extraText ? `${text} (${extraText})` : text;
      const textDiv = $('<div>', {
        'class': 'text-normal entry-label',
        'data-tooltip-text': tooltip,
      });
      textDiv.append($('<span>', {text}));
      if (extraText) {
        textDiv.append('<br>');
        textDiv.append(
          $('<span>', {class: 'text-not-important entry-label-extra', text: extraText})
        );
      }
      return [$('<span>', {class: `entry-icon ${iconClass}`}), textDiv];
    },
    _renderPermissions(principal, permissions) {
      const $permissions = $('<div>', {class: 'permissions-box flexrow f-a-center f-self-stretch'});
      const $permissionsList = $('<ul>').appendTo($permissions);
      // When full access is enabled, always show read access
      if (
        _.contains(permissions, FULL_ACCESS_PERMISSIONS) &&
        !_.contains(permissions, READ_ACCESS_PERMISSIONS)
      ) {
        permissions.push(READ_ACCESS_PERMISSIONS);
        if (principal._type !== 'DefaultEntry' && principal._type !== 'AdditionalUsers') {
          this._updateItem(principal, permissions);
        }
      }
      permissions.forEach(item => {
        const permissionInfo = this.options.permissionsInfo[item];
        const applyOpacity =
          item === READ_ACCESS_PERMISSIONS &&
          _.contains(permissions, FULL_ACCESS_PERMISSIONS) &&
          principal._type !== 'DefaultEntry';
        const cssClasses =
          (applyOpacity ? 'disabled ' : '') +
          (permissionInfo.color ? `color-${permissionInfo.color} ` : '') +
          (permissionInfo.css_class ? `${permissionInfo.css_class} ` : '');
        $permissionsList.append(
          $('<li>', {
            class: `i-label bold ${cssClasses}`,
            title: permissionInfo.description,
          }).append(permissionInfo.title)
        );
      });
      if (principal._type !== 'DefaultEntry' && principal._type !== 'AdditionalUsers') {
        $permissions.append(this._renderPermissionsButtons(principal, permissions));
      }
      return $permissions;
    },
    _renderPermissionsButtons(principal, permissions) {
      const $buttonsGroup = $('<div>', {class: 'group flexrow'});
      $buttonsGroup.append(
        this._renderEditBtn(principal, permissions),
        this._renderDeleteBtn(principal)
      );
      return $buttonsGroup;
    },
    _renderEditBtn(principal, permissions) {
      if (principal._type === 'IPNetworkGroup') {
        return $('<button>', {
          type: 'button',
          class: 'i-button text-color borderless icon-only icon-edit disabled',
          title: $T.gettext('IP networks cannot have management permissions'),
        });
      } else {
        return $('<button>', {
          'type': 'button',
          'class': 'i-button text-color borderless icon-only icon-edit',
          'data-href': build_url(Indico.Urls.PermissionsDialog, {type: this.options.objectType}),
          'data-title': $T.gettext('Assign Permissions'),
          'data-method': 'POST',
          'data-ajax-dialog': '',
          'data-params': JSON.stringify({principal: JSON.stringify(principal), permissions}),
        });
      }
    },
    _renderDeleteBtn(principal) {
      const self = this;
      return $('<button>', {
        'type': 'button',
        'class': 'i-button text-color borderless icon-only icon-remove',
        'data-principal': JSON.stringify(principal),
      }).on('click', function() {
        const $this = $(this);
        let confirmed;
        if (principal._type === 'Avatar' && principal.id === $('body').data('user-id')) {
          const title = $T.gettext("Delete entry '{0}'".format(principal.name || principal.id));
          const message = $T.gettext('Are you sure you want to remove yourself from the list?');
          confirmed = confirmPrompt(message, title);
        } else {
          confirmed = $.Deferred().resolve();
        }
        confirmed.then(() => {
          self._updateItem($this.data('principal'), []);
        });
      });
    },
    _renderItem(item) {
      const $item = $('<li>', {class: 'flexrow f-a-center'});
      const [principal, permissions] = item;
      $item.append(this._renderLabel(principal));
      $item.append(this._renderPermissions(principal, permissions));
      $item.toggleClass(`disabled ${principal.id}`, principal._type === 'DefaultEntry');
      return $item;
    },
    _renderHiddenPermissions(item) {
      const $item = $('<li>', {
        class: 'flexrow f-a-center',
      });
      const [principal, description, $permissionsList] = item;
      $permissionsList.hide();

      const $dropdownButton = $('<button>', {
        type: 'button',
        class: 'i-button text-color borderless icon-only icon-expand hidden-permissions-icon',
      }).on('click', () => {
        $permissionsList.toggle();
        $dropdownButton.toggleClass('icon-expand icon-collapse');
      });
      const $hiddenPermissionsDiv = $('<div>', {
        class: 'permissions-box f-a-center f-self-stretch',
      });
      const $descriptionDiv = $('<div>', {class: 'flexrow f-a-center'});

      $descriptionDiv.append(
        $('<div>', {class: 'hidden-permissions-description', text: description})
      );
      $descriptionDiv.append($dropdownButton);
      $hiddenPermissionsDiv.append($descriptionDiv);
      $hiddenPermissionsDiv.append($permissionsList);
      $item.append(this._renderLabel(principal).toggleClass(`disabled ${principal.id}`));
      $item.append($hiddenPermissionsDiv);
      return $item;
    },
    _renderHiddenPermissionsList(hiddenUserPermissions, permissionsInfo) {
      const $list = $('<ul>', {class: 'hidden-permissions-list'});
      hiddenUserPermissions.forEach(([user, perms]) => {
        const permissionList = perms
          .map(x => permissionsInfo[x])
          .filter(x => x !== null)
          .join(', ');
        const $user = $('<strong />', {text: user.name});
        const $permissions = `: ${permissionList}`;
        const $entry = $('<li>')
          .append($user)
          .append($permissions);
        $list.append($entry);
      });
      return $list;
    },
    _renderDropdown($dropdown) {
      $dropdown.children(':not(.default)').remove();
      $dropdown.parent().dropdown({
        selector: '.js-dropdown',
      });
      const $dropdownLink = $dropdown.prev('.js-dropdown');
      const items = $dropdown.data('items');
      const isRoleDropdown = $dropdown.hasClass('entry-role-dropdown');
      items.forEach(item => {
        if (this._findEntryIndex(item) === -1) {
          if (isRoleDropdown) {
            $dropdown.find('.separator').before(this._renderDropdownItem(item));
          } else {
            $dropdown.append(this._renderDropdownItem(item));
          }
        }
      });
      if (isRoleDropdown) {
        const isEmpty = !$dropdown.children().not('.default').length;
        $('.entry-role-dropdown .separator').toggleClass('hidden', isEmpty);
      } else if (!$dropdown.children().length) {
        $dropdownLink.addClass('disabled').attr('title', $T.gettext('All options have been added'));
      } else {
        $dropdownLink.removeClass('disabled');
      }
    },
    _renderDropdownItem(principal) {
      const self = this;
      const $dropdownItem = $('<li>', {
        'class': 'entry-item',
        'data-principal': JSON.stringify(principal),
      });
      const $itemContent = $('<a>');
      if (principal._type === 'EventRole' || principal._type === 'CategoryRole') {
        $itemContent.append(
          this._renderRoleCode(principal.code, principal.color).addClass('dropdown-icon')
        );
      }
      const $text = $('<span>', {text: principal.name});
      $dropdownItem.append($itemContent.append($text)).on('click', function() {
        // Grant read access by default
        self._addItems([$(this).data('principal')], [READ_ACCESS_PERMISSIONS]);
      });
      return $dropdownItem;
    },
    _renderDuplicatesTooltip(idx) {
      this.$permissionsWidgetList
        .find('>li')
        .not('.disabled')
        .eq(idx)
        .qtip({
          content: {
            text: $T.gettext('This entry was already added'),
          },
          show: {
            ready: true,
            effect() {
              $(this).fadeIn(300);
            },
          },
          hide: {
            event: 'unfocus click',
          },
          events: {
            hide() {
              $(this).fadeOut(300);
              $(this).qtip('destroy');
            },
          },
          position: {
            my: 'center left',
            at: 'center right',
          },
          style: {
            classes: 'qtip-warning',
          },
        });
    },
    _render() {
      this.$permissionsWidgetList.empty();
      this.data.forEach(item => {
        this.$permissionsWidgetList.append(this._renderItem(item));
      });
      // Add default entries
      const anonymous = [
        {_type: 'DefaultEntry', name: $T.gettext('Anonymous'), id: 'anonymous'},
        [READ_ACCESS_PERMISSIONS],
      ];
      this.$permissionsWidgetList.append(this._renderItem(anonymous));

      if (this.options.hiddenPermissions.length > 0) {
        const additionalPermissions = [
          {
            _type: 'AdditionalUsers',
            name: $T.gettext('Additional users'),
            id: 'additional',
          },
          $T
            .gettext('{0} users have implicit read access due to other roles')
            .format(this.options.hiddenPermissions.length),
          this._renderHiddenPermissionsList(
            this.options.hiddenPermissions,
            this.options.hiddenPermissionsInfo
          ),
        ];
        this.$permissionsWidgetList.append(this._renderHiddenPermissions(additionalPermissions));
      }

      let managersTitle;
      if (this.options.objectType === 'event') {
        managersTitle = $T.gettext('Category Managers');
      } else if (this.options.objectType === 'category') {
        managersTitle = $T.gettext('Parent Category Managers');
      } else {
        managersTitle = $T.gettext('Event Managers');
      }
      const managers = [{_type: 'DefaultEntry', name: managersTitle}, [FULL_ACCESS_PERMISSIONS]];
      this.$permissionsWidgetList.prepend(this._renderItem(managers));
      this.$permissionsWidgetList.find('.anonymous').toggle(!this.isEventProtected);

      if (this.$eventRoleDropdown.length) {
        this._renderDropdown(this.$eventRoleDropdown);
      }
      if (this.$categoryRoleDropdown.length) {
        this._renderDropdown(this.$categoryRoleDropdown);
      }
      if (this.$ipNetworkDropdown.length) {
        this._renderDropdown(this.$ipNetworkDropdown);
      }
    },
    _findEntryIndex(principal) {
      return _.findIndex(this.data, item => item[0].identifier === principal.identifier);
    },
    _updateItem(principal, newPermissions) {
      const idx = this._findEntryIndex(principal);
      if (newPermissions.length) {
        this.data[idx][1] = newPermissions;
      } else {
        this.data.splice(idx, 1);
      }
      this._update();
      this._render();
    },
    _addItems(principals, permissions) {
      const news = [];
      const repeated = [];
      principals.forEach(principal => {
        const idx = this._findEntryIndex(principal);
        if (idx === -1) {
          this.data.push([principal, permissions]);
          news.push(principal);
        } else {
          repeated.push(principal);
        }
      });
      this._update();
      this._render();
      news.forEach(principal => {
        this.$permissionsWidgetList
          .children('li:not(.disabled)')
          .eq(this._findEntryIndex(principal))
          .effect('highlight', {color: Palette.highlight}, 'slow');
      });
      repeated.forEach(principal => {
        this._renderDuplicatesTooltip(this._findEntryIndex(principal));
      });
    },
    _addUserGroup() {
      const _addPrincipals = principals => {
        // Grant read access by default
        this._addItems(principals, [READ_ACCESS_PERMISSIONS]);
      };

      const dialog = new ChooseUsersPopup(
        $T.gettext('Select a user or group to add'),
        true,
        null,
        true,
        true,
        null,
        false,
        false,
        false,
        _addPrincipals,
        null,
        true
      );

      dialog.execute();
    },
    _create() {
      this.$permissionsWidgetList = this.element.find('.permissions-widget-list');
      this.$dataField = this.element.find('input[type=hidden]');
      this.$eventRoleDropdown = this.element.find('.entry-role-dropdown');
      this.$categoryRoleDropdown = this.element.find('.entry-category-role-dropdown');
      this.$ipNetworkDropdown = this.element.find('.entry-ip-network-dropdown');
      this.data = JSON.parse(this.$dataField.val());
      this._update();
      this._render();

      // Manage changes on the permissions dialog
      this.element.on('indico:permissionsChanged', (evt, permissions, principal) => {
        this._updateItem(principal, permissions);
      });

      // Manage changes on the event protection mode field
      this.element.on('indico:protectionModeChanged', (evt, isProtected) => {
        this.isEventProtected = isProtected;
        this._render();
      });

      // Manage the addition to users/groups to the acl
      $('.js-add-user-group').on('click', () => {
        this._addUserGroup();
      });

      // Manage the creation of new roles
      $('.js-new-role').on('ajaxDialog:closed', (evt, data) => {
        if (data && data.role) {
          this.$eventRoleDropdown.data('items').push(data.role);
          this._addItems([data.role], [READ_ACCESS_PERMISSIONS]);
        }
      });

      // Apply ellipsis + tooltip on long names
      this.$permissionsWidgetList.on('mouseenter', '.entry-label', function() {
        const $this = $(this);
        if (this.offsetWidth < this.scrollWidth && !$this.attr('title')) {
          $this.attr('title', $this.attr('data-tooltip-text'));
        }
      });
    },
  });
})(jQuery);
