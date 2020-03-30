import {Form, Header} from 'semantic-ui-react';
import React from 'react';
import {FavoritesProvider} from 'indico/react/hooks';
import {FinalPrincipal} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {FinalInput, FinalTextArea} from 'indico/react/forms';

function RoomEditDetails() {
  return (
    <>
      <Header>
        <Translate>Contact</Translate>
      </Header>
      <FavoritesProvider>
        {favoriteUsersController => (
          <FinalPrincipal
            name="owner"
            favoriteUsersController={favoriteUsersController}
            label={Translate.string('Owner')}
            allowNull
            required
          />
        )}
      </FavoritesProvider>
      <Form.Group widths="equal">
        <FinalInput fluid name="keyLocation" label={Translate.string('Where is the key?')} />
        <FinalInput fluid name="telephone" label={Translate.string('Telephone')} />
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
          required
        />
        <FinalInput fluid name="division" label={Translate.string('Division')} required />
      </Form.Group>
      <FinalTextArea name="comments" label={Translate.string('Comments')} />
    </>
  );
}

export default RoomEditDetails;
