// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import exportBookingsURL from 'indico-url:rb.export_bookings';

import _ from 'lodash';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form, Modal} from 'semantic-ui-react';
import PropTypes from 'prop-types';

import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {FinalDatePeriod} from 'indico/react/components';
import {FinalRadio, handleSubmitError, FinalSubmitButton} from 'indico/react/forms';
import {snakifyKeys} from 'indico/utils/case';

import FinalRoomSelector from '../../components/RoomSelector';

function validate({format, dates, rooms}) {
  const errors = {};
  if (!format) {
    errors.type = Translate.string('Please choose a file format to export the bookings.');
  }
  if (!dates || !Object.values(dates).every(x => x)) {
    errors.dates = Translate.string('Please choose a valid period.');
  }
  if (!rooms || !rooms.length) {
    errors.rooms = Translate.string('Please choose at least one room to export its bookings.');
  }
  return errors;
}

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
              <FinalRadio name="format" value="csv" label={Translate.string('CSV')} />
              <FinalRadio name="format" value="xlsx" label={Translate.string('XLSX')} />
            </Form.Group>
            <FinalDatePeriod name="dates" label={Translate.string('Period')} required allowNull />
            <FinalRoomSelector name="rooms" label={Translate.string('Rooms to export')} required />
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
        validate={validate}
        onSubmit={handleSubmit}
        render={renderModalContent}
        initialValues={{rooms, dates: null}}
        initialValuesEqual={_.isEqual}
        subscription={{
          submitting: true,
          hasValidationErrors: true,
          pristine: true,
          submitSucceeded: true,
        }}
      />
    </Modal>
  );
}

BookingExportModal.propTypes = {
  rooms: PropTypes.array,
  onClose: PropTypes.func.isRequired,
};

BookingExportModal.defaultProps = {
  rooms: [],
};
