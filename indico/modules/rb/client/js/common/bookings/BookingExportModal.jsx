// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form, Modal} from 'semantic-ui-react';
import PropTypes from 'prop-types';
import {Translate} from 'indico/react/i18n';

import {FinalDatePeriod} from 'indico/react/components';
import FinalRoomSelector from '../../components/RoomSelector';

const BookingExportModal = props => {
  const {rooms, onClose} = props;

  const handleSubmit = async formData => {
    console.log('submit!', formData);
  };

  const renderModalContent = fprops => {
    const {submitting, hasValidationErrors, pristine, submitSucceeded} = fprops;
    return (
      <>
        <Modal.Header>
          <Translate>Export bookings</Translate>
        </Modal.Header>
        <Modal.Content>
          <Form
            id="export-bookings"
            onSubmit={fprops.handleSubmit}
            success={fprops.submitSucceeded}
          >
            <FinalDatePeriod name="dates" label={Translate.string('Period')} required allowNull />
            <FinalRoomSelector name="rooms" label={Translate.string('Rooms to export')} required />
          </Form>
        </Modal.Content>
        <Modal.Actions>
          <Button
            type="submit"
            form="blocking-form"
            disabled={submitting || hasValidationErrors || pristine || submitSucceeded}
            loading={submitting}
            primary
          >
            <Translate>Export</Translate>
          </Button>
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
        subscription={{
          submitting: true,
          hasValidationErrors: true,
          pristine: true,
          submitSucceeded: true,
        }}
      />
    </Modal>
  );
};

BookingExportModal.propTypes = {
  rooms: PropTypes.array,
  onClose: PropTypes.func.isRequired,
};

BookingExportModal.defaultProps = {
  rooms: [],
};

export default BookingExportModal;
