// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Form, Header, Tab} from 'semantic-ui-react';
import _ from 'lodash';
import PropTypes from 'prop-types';
import {ACLField} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {FinalField, FinalRadio, parsers as p} from 'indico/react/forms';

export default function RoomEditPermissions({
  active,
  permissionManager,
  permissionInfo,
  favoriteUsersController,
}) {
  return (
    <Tab.Pane active={active}>
      <Header>
        <Translate>Permissions</Translate>
      </Header>
      <Form.Field>
        <h5>
          <Translate>Booking Mode</Translate>
        </h5>
        <p className="field-description">
          <Translate>
            Restricted rooms can only be booked by users defined in the room ACL
          </Translate>
        </p>
        <Form.Group>
          <FinalRadio name="protection_mode" value="public" label={Translate.string('Public')} />
          <FinalRadio
            name="protection_mode"
            value="protected"
            label={Translate.string('Restricted')}
          />
        </Form.Group>
      </Form.Field>
      {permissionManager && permissionInfo && (
        <FinalField
          name="acl_entries"
          component={ACLField}
          favoriteUsersController={favoriteUsersController}
          label={Translate.string('Permissions')}
          permissions={false}
          readAccessAllowed={false}
          isEqual={_.isEqual}
          withGroups
          permissionInfo={permissionInfo}
          permissionManager={permissionManager}
        />
      )}
    </Tab.Pane>
  );
}

RoomEditPermissions.propTypes = {
  active: PropTypes.bool,
  permissionInfo: PropTypes.shape({
    permissions: PropTypes.object,
    tree: PropTypes.object,
    default: PropTypes.string,
  }),
  permissionManager: PropTypes.shape({
    setPermissionForId: PropTypes.func.isRequired,
  }),
  favoriteUsersController: PropTypes.array.isRequired,
};

RoomEditPermissions.defaultProps = {
  active: true,
  permissionInfo: null,
  permissionManager: null,
};
