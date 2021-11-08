// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {useSelector, useDispatch} from 'react-redux';
import {Button, Modal, Form} from 'semantic-ui-react';

import {FinalInput, FinalTextArea, FinalSubmitButton, FinalCheckbox} from 'indico/react/forms';
import {Translate, Param} from 'indico/react/i18n';

import * as actions from './actions';
import {getSectionById} from './selectors';

import '../../styles/regform.module.scss';

export default function SectionSettingsModal({id, onClose}) {
  const dispatch = useDispatch();
  const {title, description, isPersonalData, isManagerOnly} = useSelector(state =>
    getSectionById(state, id)
  );

  const handleSubmit = async formData => {
    const rv = await dispatch(actions.updateSection(id, formData));
    if (rv.error) {
      return rv.error;
    }
    onClose();
  };

  return (
    <FinalForm
      onSubmit={handleSubmit}
      subscription={{submitting: true}}
      initialValues={{title, description, is_manager_only: isManagerOnly}}
    >
      {fprops => (
        <Modal
          onClose={onClose}
          size="tiny"
          closeIcon={!fprops.submitting}
          closeOnEscape={!fprops.submitting}
          closeOnDimmerClick={!fprops.submitting}
          open
        >
          <Modal.Header>
            <Translate>
              Configure section "<Param name="section" value={title} />"
            </Translate>
          </Modal.Header>
          <Modal.Content>
            <Form id="regform-section-form" onSubmit={fprops.handleSubmit}>
              <FinalInput name="title" label={Translate.string('Title')} required />
              <FinalTextArea name="description" label={Translate.string('Description')} />
              <FinalCheckbox
                disabled={isPersonalData}
                name="is_manager_only"
                label={Translate.string('Manager-only')}
                description={
                  <Translate>Whether the section is only visible for managers.</Translate>
                }
              />
            </Form>
          </Modal.Content>
          <Modal.Actions style={{display: 'flex', justifyContent: 'flex-end'}}>
            <FinalSubmitButton form="regform-section-form" label={Translate.string('Submit')} />
            <Button onClick={onClose} disabled={fprops.submitting}>
              <Translate>Cancel</Translate>
            </Button>
          </Modal.Actions>
        </Modal>
      )}
    </FinalForm>
  );
}

SectionSettingsModal.propTypes = {
  id: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
};
