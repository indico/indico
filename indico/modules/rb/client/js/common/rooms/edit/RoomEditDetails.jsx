import {Form, Header, Tab} from 'semantic-ui-react';
import React from 'react';
import PropTypes from 'prop-types';
import {FavoritesProvider} from 'indico/react/hooks';
import {FinalPrincipal} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {FinalInput, FinalTextArea} from 'indico/react/forms';

function RoomEditDetails({active}) {
  return (
    <Tab.Pane active={active}>
      <Header>
        <Translate>Contact</Translate>
      </Header>
      <FavoritesProvider>
        {favoriteUsersController => (
          <FinalPrincipal
            name="owner"
            favoriteUsersController={favoriteUsersController}
            label={Translate.string('Owner')}
            hideErrorPopup={!active}
            allowNull
            required
          />
        )}
      </FavoritesProvider>
      <Form.Group widths="equal">
        <FinalInput
          fluid
          name="keyLocation"
          label={Translate.string('Where is the key?')}
          hideErrorPopup={!active}
        />
        <FinalInput
          fluid
          name="telephone"
          label={Translate.string('Telephone')}
          hideErrorPopup={!active}
        />
      </Form.Group>
      <Header>
        <Translate>Information</Translate>
      </Header>
      <Form.Group widths="equal">
        <FinalInput
          fluid
          type="number"
          name="capacity"
          label={Translate.string('Capacity')}
          min={1}
          hideErrorPopup={!active}
          required
        />
        <FinalInput
          fluid
          name="division"
          label={Translate.string('Division')}
          hideErrorPopup={!active}
          required
        />
      </Form.Group>
      <FinalTextArea
        name="comments"
        label={Translate.string('Comments')}
        hideErrorPopup={!active}
      />
    </Tab.Pane>
  );
}

RoomEditDetails.propTypes = {
  active: PropTypes.bool,
};

RoomEditDetails.defaultProps = {
  active: true,
};

export default RoomEditDetails;
