// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, Dropdown, Icon, Label, Popup} from 'semantic-ui-react';

import {PopoverDropdownMenu} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

import PermissionTree from './PermissionTree';

import './PrincipalPermissions.module.scss';

/**
 * A component that displays a list of permissions for a principal
 */
const PrincipalPermissions = ({
  permissions,
  permissionInfo: {permissions: permissionMap, tree: permissionTree, default: defaultPermission},
  onAddPermission,
  onRemovePermission,
  readAccessAllowed,
  fullAccessAllowed,
  readOnly,
}) => {
  const [open, setOpen] = useState(false);
  const trigger = (
    <Icon
      size="small"
      name="plus"
      title={Translate.string('Add permission')}
      circular
      styleName="permission-add-button"
      color={open ? 'blue' : null}
    />
  );

  const onClickAdd = id => {
    setOpen(false);
    onAddPermission(id);
  };

  const onClickRemove = id => {
    setOpen(false);
    onRemovePermission(id);
  };

  const onlyDefault = permissions.length === 1 && permissions[0] === defaultPermission;

  if (!readAccessAllowed) {
    permissions = _.without(permissions, 'readAccess');
  }

  if (!fullAccessAllowed) {
    permissions = _.without(permissions, 'fullAccess');
  }

  return (
    <div styleName="principal-permission">
      {permissions.map(permission => (
        <Popup
          key={permission}
          position="right center"
          popperModifiers={[
            {name: 'hide', enabled: false},
            {name: 'preventOverflow', enabled: false},
          ]}
          trigger={
            <Label as="div" size="tiny" color={permissionMap[permission].color}>
              {permissionMap[permission].title}
              {!onlyDefault && (
                <Icon name="close" onClick={() => !readOnly && onClickRemove(permission)} />
              )}
            </Label>
          }
          content={permissionMap[permission].description}
        />
      ))}
      {!readOnly && (
        <PopoverDropdownMenu
          onOpen={() => setOpen(true)}
          onClose={() => setOpen(false)}
          trigger={trigger}
          open={open}
          placement="right-start"
          overflow
        >
          <Dropdown.Header>
            <Translate>Add permission</Translate>
          </Dropdown.Header>
          <PermissionTree
            tree={permissionTree}
            permissionMap={permissionMap}
            exclude={permissions}
            hide={['readAccess']}
            onSelect={p => onClickAdd(p)}
          />
          <Button
            size="mini"
            fluid
            onClick={() => setOpen(false)}
            content={Translate.string('Cancel')}
          />
        </PopoverDropdownMenu>
      )}
    </div>
  );
};

PrincipalPermissions.propTypes = {
  /** The list of permissions, as an array of strings */
  permissions: PropTypes.arrayOf(PropTypes.string).isRequired,
  /** Called whenever a new permission is added */
  onAddPermission: PropTypes.func.isRequired,
  /** Called when a permission is deleted */
  onRemovePermission: PropTypes.func.isRequired,
  /** Object containing metadata about available permissions */
  permissionInfo: PropTypes.shape({
    permissions: PropTypes.object,
    tree: PropTypes.object,
    default: PropTypes.string,
  }).isRequired,
  /** Whether the 'read_access' permission is used/allowed */
  readAccessAllowed: PropTypes.bool,
  /** Whether the 'full_access' permission is used/allowed */
  fullAccessAllowed: PropTypes.bool,
  /** Whether the field is read-only */
  readOnly: PropTypes.bool,
};

PrincipalPermissions.defaultProps = {
  readAccessAllowed: true,
  fullAccessAllowed: true,
  readOnly: false,
};

export default React.memo(PrincipalPermissions);
