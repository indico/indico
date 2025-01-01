// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';

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
      [id]: newPermissions,
    };
  }
}

/**
 * This function will split the list of principals in available and pending entries (and sort them)
 * @param {Array} principalIds - list of displayed principal IDs
 * @param {Object} idMap - an object mapping available IDs and their representations
 * @returns {Array} [entries, pendingEntries]
 */
export const getPrincipalList = (principalIds, idMap) => {
  return [
    // resolved principals
    _.sortBy(
      principalIds.filter(x => x in idMap).map(x => idMap[x]),
      entry => `${PrincipalType.getSortOrder(entry.type)}-${entry.name.toLowerCase()}`
    ),
    // pending principals
    _.sortBy(
      principalIds
        .filter(x => !(x in idMap))
        .map(x => ({identifier: x, type: getTypeFromIdentifier(x)})),
      entry => `${PrincipalType.getSortOrder(entry.type)}-${entry.identifier.toLowerCase()}`
    ),
  ];
};

export class PrincipalType {
  /* eslint-disable lines-between-class-members */
  static user = 'user';
  static localGroup = 'local_group';
  static multipassGroup = 'multipass_group';
  static eventRole = 'event_role';
  static categoryRole = 'category_role';
  static registrationForm = 'registration_form';
  static email = 'email';
  static eventPerson = 'event_person';
  /* eslint-enable lines-between-class-members */

  static propType = PropTypes.oneOf([
    PrincipalType.user,
    PrincipalType.localGroup,
    PrincipalType.multipassGroup,
    PrincipalType.eventRole,
    PrincipalType.categoryRole,
    PrincipalType.registrationForm,
    PrincipalType.email,
    PrincipalType.eventPerson,
  ]);

  static getPendingText(type) {
    return {
      [PrincipalType.user]: Translate.string('Unknown user'),
      [PrincipalType.localGroup]: Translate.string('Unknown group'),
      [PrincipalType.multipassGroup]: Translate.string('Unknown group'),
      [PrincipalType.eventRole]: Translate.string('Unknown event role'),
      [PrincipalType.categoryRole]: Translate.string('Unknown category role'),
      [PrincipalType.registrationForm]: Translate.string('Unknown registration form'),
      [PrincipalType.eventPerson]: Translate.string('Unknown event person'),
    }[type];
  }

  static getDeletedText(type) {
    return {
      [PrincipalType.user]: Translate.string(
        'This user does not exist anymore. Please choose someone else.'
      ),
      [PrincipalType.localGroup]: Translate.string(
        'This group does not exist anymore. Please choose a different one.'
      ),
      [PrincipalType.multipassGroup]: Translate.string(
        'This group does not exist anymore. Please choose a different one.'
      ),
      [PrincipalType.registrationForm]: Translate.string(
        'This form does not exist anymore. Please choose a different one.'
      ),
      // event/category roles are hard-deleted
    }[type];
  }

  static getIcon(type) {
    return {
      [PrincipalType.user]: 'user',
      [PrincipalType.localGroup]: 'users',
      [PrincipalType.multipassGroup]: 'users',
      [PrincipalType.registrationForm]: 'id badge outline',
      [PrincipalType.email]: 'envelope outline',
      [PrincipalType.eventPerson]: 'user',
      // event/category roles have no icon but their code
    }[type];
  }

  static getSortOrder(type) {
    return {
      [PrincipalType.localGroup]: 0,
      [PrincipalType.multipassGroup]: 0,
      [PrincipalType.eventRole]: 1,
      [PrincipalType.categoryRole]: 2,
      [PrincipalType.registrationForm]: 3,
      [PrincipalType.user]: 4,
      [PrincipalType.email]: 5,
      [PrincipalType.eventPerson]: 6,
    }[type];
  }
}

export function getTypeFromIdentifier(identifier) {
  if (identifier.startsWith('User:') || identifier.startsWith('ExternalUser:')) {
    return PrincipalType.user;
  } else if (identifier.startsWith('Group::')) {
    return PrincipalType.localGroup;
  } else if (identifier.startsWith('Group:')) {
    return PrincipalType.multipassGroup;
  } else if (identifier.startsWith('EventRole:')) {
    return PrincipalType.eventRole;
  } else if (identifier.startsWith('CategoryRole:')) {
    return PrincipalType.categoryRole;
  } else if (identifier.startsWith('RegistrationForm:')) {
    return PrincipalType.registrationForm;
  } else if (identifier.startsWith('Email:')) {
    return PrincipalType.email;
  } else if (identifier.startsWith('EventPerson:')) {
    return PrincipalType.eventPerson;
  } else {
    throw new Error(`Identifier ${identifier} has unknown type`);
  }
}
