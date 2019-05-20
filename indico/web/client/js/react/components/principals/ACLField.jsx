// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';
import {Button, List} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';
import {UserSearch, GroupSearch} from '../principals/Search';
import {useFetchPrincipals, usePermissionInfo} from '../principals/hooks';
import {PendingPrincipalListItem, PrincipalListItem} from '../principals/items';
import {getPrincipalList} from '../principals/util';

import '../principals/PrincipalListField.module.scss';
import PrincipalPermissions from './PrincipalPermissions';


function buildACL(aclMap) {
    return Object.entries(aclMap).map(([ident, permissions]) => (
        [ident, _.sortBy(permissions.map(
            p => ((p === 'fullAccess' || p === 'readAccess') ? '_' : '') + _.snakeCase(p)
        ))]
    ));
}

const isGroup = identifier => identifier.startsWith('Group:');

/**
 * The ACLField is a PrincipalField on steroids. In addition to the functionality
 * present in ACLField, it keeps track of user permissions.
 */
const ACLField = (props) => {
    const {
        value, disabled, readOnly, onChange, onFocus, onBlur, withGroups,
        favoriteUsersController, readAccessAllowed
    } = props;
    const [favoriteUsers, [handleAddFavorite, handleDelFavorite]] = favoriteUsersController;

    const valueIds = value.map(([identifier]) => identifier);

    // Permission info - description of permission hierarchy
    const [permissionManager, permissionInfo] = usePermissionInfo();

    // keep track of permissions for each entry (ACL)
    const aclMap = Object.assign({}, ...value.map(([identifier, permissions]) => (
        {[identifier]: permissions.map(p => _.camelCase(p))}
    )));

    const setValue = func => {
        onChange(buildACL(func(aclMap)));
        onFocus();
        onBlur();
    };

    // fetch missing principals' information
    const informationMap = useFetchPrincipals(valueIds);

    const handleDelete = identifier => {
        setValue(prev => _.omit(prev, identifier));
    };
    const handleAddItems = data => {
        const newACLs = data.map(
            ({identifier}) => ({[identifier]: ['prebook']})
        );
        setValue(prev => ({...prev, ...Object.assign({}, ...newACLs)}));
    };

    // Handling of list of principals (shared with PrincipalListField)
    const [entries, pendingEntries] = getPrincipalList(
        valueIds,
        informationMap,
        id => ({identifier: id, group: isGroup(id)}),
        entry => `${entry.group ? 0 : 1}-${entry.name.toLowerCase()}`,
        entry => `${entry.group ? 0 : 1}-${entry.identifier.toLowerCase()}`
    );

    return (
        <>
            <List divided relaxed styleName="list">
                {entries.map(data => {
                    const permissions = aclMap[data.identifier];
                    const permissionList = permissionManager && (
                        <PrincipalPermissions permissions={permissions}
                                              permissionInfo={permissionInfo}
                                              onAddPermission={permId => {
                                                  setValue(prev => permissionManager.setPermissionForId(
                                                      prev, data.identifier, permId, true
                                                  ));
                                              }}
                                              onRemovePermission={permId => {
                                                  setValue(prev => permissionManager.setPermissionForId(
                                                      prev, data.identifier, permId, false
                                                  ));
                                              }}
                                              readAccessAllowed={readAccessAllowed}
                                              readOnly={readOnly} />
                    );
                    return (
                        <PrincipalListItem key={data.identifier}
                                           name={data.name}
                                           detail={data.detail}
                                           isGroup={data.group}
                                           favorite={!data.group && data.userId in favoriteUsers}
                                           onDelete={() => !disabled && handleDelete(data.identifier)}
                                           onAddFavorite={() => !disabled && handleAddFavorite(data.userId)}
                                           onDelFavorite={() => !disabled && handleDelFavorite(data.userId)}
                                           disabled={disabled}
                                           readOnly={readOnly}
                                           actions={permissionList} />
                    );
                })}
                {pendingEntries.map(data => (
                    <PendingPrincipalListItem key={data.identifier} isGroup={data.group} />
                ))}
                {!value.length && (
                    <List.Item styleName="empty">
                        <Translate>
                            This list is currently empty
                        </Translate>
                    </List.Item>
                )}
            </List>
            {!readOnly && (
                <Button.Group>
                    <Button icon="add" as="div" disabled />
                    <UserSearch existing={valueIds} onAddItems={handleAddItems} favorites={favoriteUsers}
                                disabled={disabled} />
                    {withGroups && <GroupSearch existing={valueIds} onAddItems={handleAddItems} disabled={disabled} />}
                </Button.Group>
            )}
        </>
    );
};

ACLField.propTypes = {
    /** Current value of the field, an array of `[identifier, [permissions]]` pairs */
    value: PropTypes.arrayOf(PropTypes.array).isRequired,
    /** Whether the field is disabled */
    disabled: PropTypes.bool.isRequired,
    /** Whether the field is read-only */
    readOnly: PropTypes.bool,
    /** Called when the field's value changes */
    onChange: PropTypes.func.isRequired,
    /** Called when the field is selected */
    onFocus: PropTypes.func.isRequired,
    /** Called when the field is deselected */
    onBlur: PropTypes.func.isRequired,
    /** Array of the form `[favoriteUsers, [handleAddFavorite, handleDelFavorite]]` */
    favoriteUsersController: PropTypes.array.isRequired,
    /** Whether groups are allowed in this ACL */
    withGroups: PropTypes.bool,
    /** Whether the 'read_access' permission is used/allowed */
    readAccessAllowed: PropTypes.bool
};

ACLField.defaultProps = {
    withGroups: false,
    readOnly: false,
    readAccessAllowed: true
};

export default React.memo(ACLField);
