import {Form, Header, Tab} from 'semantic-ui-react';
import React from 'react';
import _ from 'lodash';
import PropTypes from 'prop-types';
import {FavoritesProvider} from 'indico/react/hooks';
import {ACLField} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {FinalField, FinalRadio, parsers as p} from 'indico/react/forms';
import {usePermissionInfo} from 'indico/react/components/principals/hooks';

function RoomEditPermissions({active}) {
  const [permissionManager, permissionInfo] = usePermissionInfo();

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
          <FinalRadio
            name="protectionMode"
            value="public"
            label={Translate.string('Public')}
            hideErrorPopup={!active}
          />
          <FinalRadio
            name="protectionMode"
            value="protected"
            label={Translate.string('Restricted')}
            hideErrorPopup={!active}
          />
        </Form.Group>
      </Form.Field>
      {permissionManager && permissionInfo && (
        <FavoritesProvider>
          {favoriteUsersController => (
            <FinalField
              name="aclEntries"
              component={ACLField}
              favoriteUsersController={favoriteUsersController}
              label={Translate.string('Permissions')}
              permissions={false}
              readAccessAllowed={false}
              isEqual={_.isEqual}
              withGroups
              permissionInfo={permissionInfo}
              permissionManager={permissionManager}
              hideErrorPopup={!active}
            />
          )}
        </FavoritesProvider>
      )}
    </Tab.Pane>
  );
}

RoomEditPermissions.propTypes = {
  active: PropTypes.bool,
};

RoomEditPermissions.defaultProps = {
  active: true,
};

export default RoomEditPermissions;
