// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import exportBookingsURL from 'indico-url:rb.export_bookings';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form, Modal} from 'semantic-ui-react';

import {FinalDateRangePicker} from 'indico/react/components';
import {
  validators as v,
  FinalRadio,
  handleSubmitError,
  FinalSubmitButton,
} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';

import FinalRoomSelector from '../../components/RoomSelector';

export default function BookingExportModal({rooms, onClose}) {
  const handleSubmit = async formData => {
    const {
      rooms: selectedRooms,
      dates: {startDate, endDate},
      ...rest
    } = formData;
    const roomIds = selectedRooms.map(room => room.id);
    let response;
    try {
      response = await indicoAxios.post(
        exportBookingsURL(),
        snakifyKeys({roomIds, startDate, endDate, ...rest})
      );
    } catch (error) {
      return handleSubmitError(error);
    }
    location.href = response.data.url;
  };

  const renderModalContent = fprops => {
    return (
      <>
        <Modal.Header>
          <Translate>Export bookings</Translate>
        </Modal.Header>
        <Modal.Content>
          <Form id="export-bookings-form" onSubmit={fprops.handleSubmit}>
            <h5>
              <Translate>File format</Translate>
            </h5>
            <Form.Group>
              <FinalRadio name="format" value="csv" validate={v.required} label="CSV" />
              <FinalRadio name="format" value="xlsx" validate={v.required} label="XLSX" />
            </Form.Group>
            <FinalDateRangePicker
              name="dates"
              label={Translate.string('Period')}
              required
              allowNull
            />
            <FinalRoomSelector
              name="rooms"
              label={Translate.string('Rooms to export')}
              validate={val => {
                if (!val || !val.length) {
                  return Translate.string('Please choose at least one room.');
                }
              }}
              required
            />
          </Form>
        </Modal.Content>
        <Modal.Actions>
          <FinalSubmitButton label={Translate.string('Export')} form="export-bookings-form" />
          <Button type="button" onClick={onClose}>
            <Translate>Close</Translate>
          </Button>
        </Modal.Actions>
      </>
    );
  };

  return (
    <Modal open onClose={onClose} size="tiny" closeIcon>
      <FinalForm
        onSubmit={handleSubmit}
        render={renderModalContent}
        initialValues={{rooms, dates: null}}
        initialValuesEqual={_.isEqual}
        subscription={{}}
      />
    </Modal>
  );
}

BookingExportModal.propTypes = {
  rooms: PropTypes.array.isRequired,
  onClose: PropTypes.func.isRequired,
};
