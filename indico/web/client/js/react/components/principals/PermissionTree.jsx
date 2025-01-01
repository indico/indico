// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Button, Popup} from 'semantic-ui-react';

import './PermissionTree.module.scss';

/**
 * A component that displays a tree of permissions with clickable options
 */
const PermissionTree = ({tree, permissionMap, exclude, hide, disabled, onSelect}) => {
  const triggerFactory = (id, itemDisabled) => (
    <Button
      size="mini"
      basic
      disabled={disabled || itemDisabled}
      color={permissionMap[id].color}
      content={permissionMap[id].title}
      onClick={() => onSelect(id)}
    />
  );
  const entries = Object.entries(tree).filter(([id]) => !hide.includes(id));

  return (
    <div styleName="permission-tree">
      {entries.map(([id, {description, children}]) => {
        const itemDisabled = exclude.includes(id);
        return (
          <React.Fragment key={id}>
            <div styleName="permission-option">
              <Popup
                trigger={triggerFactory(id, itemDisabled)}
                content={description}
                position="right center"
                popperModifiers={[
                  {name: 'hide', enabled: false},
                  {name: 'preventOverflow', enabled: false},
                ]}
                inverted
              />
            </div>
            {children && (
              <PermissionTree
                tree={children}
                permissionMap={permissionMap}
                disabled={itemDisabled}
                exclude={exclude}
                hide={hide}
                onSelect={onSelect}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

const PermissionTreeData = PropTypes.objectOf(
  PropTypes.shape({
    description: PropTypes.string,
    title: PropTypes.string,
    children: () => PermissionTreeData,
  })
);

PermissionTree.propTypes = {
  tree: PermissionTreeData.isRequired,
  permissionMap: PropTypes.objectOf(PropTypes.object).isRequired,
  onSelect: PropTypes.func.isRequired,
  exclude: PropTypes.arrayOf(PropTypes.string),
  hide: PropTypes.arrayOf(PropTypes.string),
  disabled: PropTypes.bool,
};

PermissionTree.defaultProps = {
  exclude: [],
  hide: [],
  disabled: false,
};

export default React.memo(PermissionTree);
