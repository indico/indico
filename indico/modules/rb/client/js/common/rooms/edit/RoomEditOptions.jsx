import {Dropdown, Form, Header, Tab} from 'semantic-ui-react';
import React from 'react';
import _ from 'lodash';
import {FieldArray} from 'react-final-form-arrays';
import PropTypes from 'prop-types';
import shortid from 'shortid';
import {Translate} from 'indico/react/i18n';
import {FinalCheckbox, FinalField, FinalInput} from 'indico/react/forms';
import EquipmentList from './EquipmentList';
import DailyAvailability from './DailyAvailability';
import NonBookablePeriods from './NonBookablePeriods';

function RoomEditOptions({active, showEquipment, globalAttributes}) {
  // TODO: is null
  const attributeTitles = globalAttributes
    ? _.fromPairs(globalAttributes.map(x => [x.name, x.title]))
    : [];
  const withKeyAttribute = value => value.map(e => ({...e, key: shortid.generate()}));

  return (
    <Tab.Pane active={active}>
      <Header>
        <Translate>Availability</Translate>
      </Header>
      <Form.Group>
        <FinalField
          name="bookableHours"
          component={DailyAvailability}
          isEqual={_.isEqual}
          format={value => (value === null ? [] : withKeyAttribute(value))}
          hideErrorPopup={!active}
        />
        <FinalField
          name="nonbookablePeriods"
          component={NonBookablePeriods}
          isEqual={_.isEqual}
          format={value => (value === null ? [] : withKeyAttribute(value))}
          hideErrorPopup={!active}
        />
      </Form.Group>
      <Header>
        <Translate>Equipment and custom attributes</Translate>
      </Header>
      <Form.Group>
        {showEquipment && (
          <FinalField
            name="availableEquipment"
            component={EquipmentList}
            isEqual={_.isEqual}
            componentLabel={Translate.string('Add new equipment')}
            hideErrorPopup={!active}
          />
        )}
        <FieldArray name="attributes" isEqual={_.isEqual}>
          {({fields}) => {
            if (!fields.value) {
              return null;
            }
            const fieldsByName = fields.map(x => x.name);
            const options = globalAttributes
              .map(x => ({
                key: x.name,
                text: x.title,
                value: x.name,
              }))
              .filter(attr => !fieldsByName.includes(attr.key));
            return (
              <div>
                <Dropdown
                  className="icon room-edit-modal-add-btn"
                  button
                  text={Translate.string('Add new attributes')}
                  floating
                  labeled
                  icon="add"
                  options={options}
                  search
                  disabled={options.length === 0}
                  selectOnBlur={false}
                  value={null}
                  onChange={(__, {value: name}) => {
                    fields.push({value: null, name});
                  }}
                />
                {fields.map((attribute, index) => (
                  <FinalInput
                    key={attribute}
                    name={`${attribute}.value`}
                    label={attributeTitles[fields.value[index].name]}
                    hideErrorPopup={!active}
                    required
                    icon={{
                      name: 'remove',
                      color: 'red',
                      link: true,
                      onClick: () => fields.remove(index),
                    }}
                  />
                ))}
                {fields.length === 0 && (
                  <div>
                    <Translate>No custom attributes found</Translate>
                  </div>
                )}
              </div>
            );
          }}
        </FieldArray>
      </Form.Group>
      <Header>
        <Translate>Options</Translate>
      </Header>
      <Form.Group grouped>
        <FinalCheckbox name="isReservable" label={Translate.string('Bookable')} hideErrorPopup />
        <FinalCheckbox
          name="reservationsNeedConfirmation"
          label={Translate.string('Require confirmation (pre-bookings)')}
          hideErrorPopup={!active}
        />
        <FinalCheckbox
          name="notificationsEnabled"
          label={Translate.string('Reminders enabled')}
          hideErrorPopup={!active}
        />
        <FinalCheckbox
          name="endNotificationsEnabled"
          label={Translate.string('Reminders of finishing bookings enabled')}
          hideErrorPopup={!active}
        />
      </Form.Group>
    </Tab.Pane>
  );
}

RoomEditOptions.propTypes = {
  active: PropTypes.bool,
  showEquipment: PropTypes.bool,
  globalAttributes: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string,
      title: PropTypes.string,
    })
  ),
};

RoomEditOptions.defaultProps = {
  active: true,
  showEquipment: false,
  globalAttributes: [],
};

export default RoomEditOptions;
