// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Form as FinalForm} from 'react-final-form';
import {Form, Modal} from 'semantic-ui-react';

import {FinalDropdown, FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import './JudgmentModal.module.scss';

const judgmentOptions = [
  {text: Translate.string('To be corrected'), value: 'to_be_corrected'},
  {text: Translate.string('Needs confirmation'), value: 'needs_confirmation'},
  {text: Translate.string('Rejected'), value: 'rejected'},
];

export default function JudgmentModal({onClose}) {
  const judgeRevision = formData => {
    console.log(formData);
  };

  return (
    <FinalForm
      onSubmit={judgeRevision}
      subscription={{submitting: true}}
      initialValues={{judgment: 'to_be_corrected'}}
    >
      {fprops => (
        <Modal onClose={onClose} closeOnDimmerClick={false} open closeOnEscape closeIcon>
          <Modal.Content>
            <Form id="judgment-form" onSubmit={fprops.handleSubmit}>
              <div>TODO: Files field</div>
              <FinalDropdown
                width={6}
                name="judgment"
                options={judgmentOptions}
                selection
                required
              />
              <FinalTextArea
                name="comment"
                placeholder={Translate.string('Leave a comment...')}
                hideValidationError
              />
              <div>TODO: Tags field</div>
            </Form>
          </Modal.Content>
          <Modal.Actions>
            <FinalSubmitButton form="judgment-form" label={Translate.string('Submit')} />
          </Modal.Actions>
        </Modal>
      )}
    </FinalForm>
  );
}

JudgmentModal.propTypes = {
  onClose: PropTypes.func,
};

JudgmentModal.defaultProps = {
  onClose: null,
};
