// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useMemo} from 'react';
import {Dropdown, Form, Header, Tab} from 'semantic-ui-react';
import _ from 'lodash';
import {FieldArray} from 'react-final-form-arrays';
import PropTypes from 'prop-types';
import {Translate} from 'indico/react/i18n';
import {FinalCheckbox, FinalField, FinalInput} from 'indico/react/forms';
import EquipmentList from './EquipmentList';
import DailyAvailability from './DailyAvailability';
import NonBookablePeriods from './NonBookablePeriods';

export default function RoomEditOptions({active, showEquipment, globalAttributes}) {
  const attributeTitles = useMemo(
    () => (globalAttributes ? _.fromPairs(globalAttributes.map(x => [x.name, x.title])) : []),
    [globalAttributes]
  );

  return (
    <Tab.Pane active={active}>
      <Header>
        <Translate>Availability</Translate>
      </Header>
      <Form.Group>
        <FinalField name="bookable_hours" component={DailyAvailability} isEqual={_.isEqual} />
        <FinalField name="nonbookable_periods" component={NonBookablePeriods} isEqual={_.isEqual} />
      </Form.Group>
      <Header>
        <Translate>Equipment and custom attributes</Translate>
      </Header>
      <Form.Group>
        {showEquipment && (
          <FinalField
            name="available_equipment"
            component={EquipmentList}
            isEqual={_.isEqual}
            componentLabel={Translate.string('Add new equipment')}
          />
        )}
        {globalAttributes && globalAttributes.length > 0 && (
          <FieldArray name="attributes" isEqual={_.isEqual}>
            {({fields}) => {
              if (!fields.value) {
                return null;
              }
              const fieldsByName = fields.value.map(x => x.name);
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
                      <Translate>No custom attributes defined</Translate>
                    </div>
                  )}
                </div>
              );
            }}
          </FieldArray>
        )}
      </Form.Group>
      <Header>
        <Translate>Options</Translate>
      </Header>
      <Form.Group grouped>
        <FinalCheckbox name="is_reservable" label={Translate.string('Bookable')} />
        <FinalCheckbox
          name="reservations_need_confirmation"
          label={Translate.string('Require confirmation (pre-bookings)')}
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
