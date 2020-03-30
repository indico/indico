import {Form, Header} from 'semantic-ui-react';
import React from 'react';
import {Translate} from 'indico/react/i18n';
import {FinalInput, parsers as p} from 'indico/react/forms';

function RoomEditLocation() {
  return (
    <>
      <Header>
        <Translate>Location</Translate>
      </Header>
      <FinalInput
        fluid
        name="verboseName"
        label={Translate.string('Name')}
        required={false}
        nullIfEmpty
      />
      <Form.Group widths="four">
        <Form.Field width={8}>
          <FinalInput name="site" label={Translate.string('Site')} required />
        </Form.Field>
        <FinalInput name="building" label={Translate.string('Building')} required />
        <FinalInput name="floor" label={Translate.string('Floor')} required />
        <FinalInput name="number" label={Translate.string('Number')} required />
      </Form.Group>
      <Form.Group widths="equal">
        <FinalInput
          fluid
          type="number"
          name="surfaceArea"
          label={Translate.string('Surface Area (m²)')}
          min={0}
        />
        <FinalInput
          fluid
          type="text"
          name="latitude"
          label={Translate.string('Latitude')}
          parse={v => p.number(v, false)}
        />
        <FinalInput
          fluid
          type="text"
          name="longitude"
          label={Translate.string('Longitude')}
          parse={v => p.number(v, false)}
        />
      </Form.Group>
      <Form.Group widths="equal">
        <FinalInput
          fluid
          type="number"
          name="maxAdvanceDays"
          label={Translate.string('Maximum advance time for bookings (days)')}
          min={1}
        />
        <FinalInput
          fluid
          type="number"
          name="bookingLimitDays"
          label={Translate.string('Max duration of a booking (day)')}
          min={1}
        />
      </Form.Group>
    </>
  );
}

export default RoomEditLocation;
