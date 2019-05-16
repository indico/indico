// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';

/**
 * This class encapsulates the logic of a hierarchical permission system.
 */
export class PermissionManager {
    constructor(tree, defaultPermission) {
        this.index = this._buildIndex(tree);
        this.defaultPermission = defaultPermission;
    }

    _buildIndex(tree) {
        return Object.entries(tree).reduce((accum, [id, {children}]) => {
            accum[id] = children ? Object.keys(children) : null;
            return {...accum, ...(children ? this._buildIndex(children) : [])};
        }, {});
    }

    _getDescendants(permissionId) {
        const children = this.index[permissionId];
        if (children) {
            return [...children, ..._.flatten(children.map(p => this._getDescendants(p)))];
        } else {
            return [];
        }
    }

    /**
     * This method allows for a permission to be set taking into account that it
     * possibly already implies others, which may have to be removed from the list.
     * e.g. "manage" will already imply "read", so, `["read"] + ["manage"] -> ["manage"]`
     *
     * @param {Object} aclMap - the object to set the permission at
     * @param {String} id - the ID of the ACL entry (user/group)
     * @param {String} permission - the ID of the permission
     * @param {Boolean} value - `true` to set the permission, `false` to remove it
     */
    setPermissionForId(aclMap, id, permission, value) {
        let newPermissions;
        if (value) {
            // adding a permission
            const descendants = this._getDescendants(permission);
            // check that the other permissions are not descendants of the one that is about to be added
            newPermissions = aclMap[id].filter(p => !descendants.includes(p)).concat([permission]);
        } else {
            // removing a permission
            newPermissions = _.without(aclMap[id], permission);
        }

        // don't allow the permissions to be empty
        if (!newPermissions.length) {
            newPermissions.push(this.defaultPermission);
        }

        return {
            ...aclMap,
            [id]: newPermissions
        };
    }
}

/**
 * This function will split the list of principals in available and pending entries (and sort them)
 * @param {Array} principalIds - list of displayed principal IDs
 * @param {Object} idMap - an object mapping available IDs and their representations
 * @param {Function} pendingReprFunction - maps each entry id to a provisional representation of a pending entry
 * @param {Function} sortingKeyFunc - maps each available entry to a sorting key
 * @param {Function} pendingSortingKeyFunc - maps each pending entry to a sorting key
 * @returns {Array} [entries, pendingEntries]
 */
export const getPrincipalList = (principalIds, idMap, pendingReprFunction, sortingKeyFunc, pendingSortingKeyFunc) => {
    return [
        _.sortBy(principalIds.filter(x => x in idMap).map(x => idMap[x]), sortingKeyFunc),
        _.sortBy(principalIds.filter(x => !(x in idMap)).map(pendingReprFunction), pendingSortingKeyFunc),
    ];
};
