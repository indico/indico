// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Button, Popup} from 'semantic-ui-react';

import './PermissionTree.module.scss';

// TODO: maybe move this to the backend?
export const PERMISSION_COLORS = {
    moderate: 'purple',
    readAccess: 'teal',
    fullAccess: 'red',
    book: 'green',
    prebook: 'orange',
    override: 'pink'
};

/**
 * A component that displays a tree of permissions with clickable options
 */
const PermissionTree = ({tree, exclude, hide, disabled, onSelect}) => {
    const triggerFactory = (id, title, itemDisabled) => (
        <Button size="mini"
                basic
                disabled={disabled || itemDisabled}
                color={PERMISSION_COLORS[id]}
                content={title}
                onClick={() => onSelect(id)} />
    );
    const entries = Object.entries(tree).filter(([id]) => !hide.includes(id));

    return (
        <div styleName="permission-tree">
            {entries.map(([id, {description, title, children}]) => {
                const itemDisabled = exclude.includes(id);
                return (
                    <React.Fragment key={id}>
                        <div styleName="permission-option">
                            <Popup trigger={triggerFactory(id, title, itemDisabled)}
                                   content={description}
                                   position="right center"
                                   inverted />
                        </div>
                        {children && (
                            <PermissionTree tree={children}
                                            disabled={itemDisabled}
                                            exclude={exclude}
                                            hide={hide}
                                            onSelect={onSelect} />
                        )}
                    </React.Fragment>
                );
            })}
        </div>
    );
};

const PermissionTreeData = PropTypes.objectOf(PropTypes.shape({
    description: PropTypes.string,
    title: PropTypes.string,
    children: () => PermissionTreeData
}));

PermissionTree.propTypes = {
    tree: PermissionTreeData.isRequired,
    onSelect: PropTypes.func.isRequired,
    exclude: PropTypes.arrayOf(PropTypes.string),
    hide: PropTypes.arrayOf(PropTypes.string),
    disabled: PropTypes.bool
};

PermissionTree.defaultProps = {
    exclude: [],
    hide: [],
    disabled: false,
};

export default React.memo(PermissionTree);
