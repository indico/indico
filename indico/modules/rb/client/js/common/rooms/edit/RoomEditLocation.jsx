import {Form, Header, Tab} from 'semantic-ui-react';
import React from 'react';
import PropTypes from 'prop-types';
import {Translate} from 'indico/react/i18n';
import {FinalInput, parsers as p} from 'indico/react/forms';

function RoomEditLocation({active}) {
  return (
    <Tab.Pane active={active}>
      <Header>
        <Translate>Location</Translate>
      </Header>
      <FinalInput
        fluid
        name="verboseName"
        label={Translate.string('Name')}
        required={false}
        nullIfEmpty
        hideErrorPopup={!active}
      />
      <Form.Group widths="four">
        <Form.Field width={8}>
          <FinalInput
            name="site"
            label={Translate.string('Site')}
            hideErrorPopup={!active}
            required
          />
        </Form.Field>
        <FinalInput
          name="building"
          label={Translate.string('Building')}
          hideErrorPopup={!active}
          required
        />
        <FinalInput
          name="floor"
          label={Translate.string('Floor')}
          hideErrorPopup={!active}
          required
        />
        <FinalInput
          name="number"
          label={Translate.string('Number')}
          hideErrorPopup={!active}
          required
        />
      </Form.Group>
      <Form.Group widths="equal">
        <FinalInput
          fluid
          type="number"
          name="surfaceArea"
          label={Translate.string('Surface Area (m²)')}
          min={0}
          hideErrorPopup={!active}
        />
        <FinalInput
          fluid
          type="text"
          name="latitude"
          label={Translate.string('Latitude')}
          parse={v => p.number(v, false)}
          hideErrorPopup={!active}
        />
        <FinalInput
          fluid
          type="text"
          name="longitude"
          label={Translate.string('Longitude')}
          parse={v => p.number(v, false)}
          hideErrorPopup={!active}
        />
      </Form.Group>
      <Form.Group widths="equal">
        <FinalInput
          fluid
          type="number"
          name="maxAdvanceDays"
          label={Translate.string('Maximum advance time for bookings (days)')}
          min={1}
          hideErrorPopup={!active}
        />
        <FinalInput
          fluid
          type="number"
          name="bookingLimitDays"
          label={Translate.string('Max duration of a booking (day)')}
          min={1}
          hideErrorPopup={!active}
        />
      </Form.Group>
    </Tab.Pane>
  );
}

RoomEditLocation.propTypes = {
  active: PropTypes.bool,
};

RoomEditLocation.defaultProps = {
  active: true,
};

export default RoomEditLocation;
