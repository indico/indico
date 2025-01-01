// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form} from 'semantic-ui-react';

import {FinalDropdown, FinalSubmitButton} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import ReviewConditionsContext from './context';

import './ReviewConditionForm.module.scss';

export default function ReviewConditionForm({types, onSubmit, onDismiss}) {
  const {fileTypes} = useContext(ReviewConditionsContext);
  const options = fileTypes.map(fileType => ({text: fileType.name, value: fileType.id}));

  return (
    <div styleName="condition-form">
      <FinalForm
        onSubmit={onSubmit}
        initialValues={{file_types: types}}
        subscription={{submitting: true}}
      >
        {({handleSubmit, submitting}) => (
          <Form onSubmit={handleSubmit}>
            <div styleName="file-types-dropdown">
              <FinalDropdown
                placeholder={Translate.string('Select filetypes to create a condition')}
                name="file_types"
                options={options}
                hideValidationError
                required
                selection
                multiple
                search
              />
            </div>
            <div styleName="action-buttons">
              <FinalSubmitButton icon="checkmark" size="mini" circular primary />
              <Button
                icon="cancel"
                size="mini"
                onClick={onDismiss}
                disabled={submitting}
                circular
              />
            </div>
          </Form>
        )}
      </FinalForm>
    </div>
  );
}

ReviewConditionForm.propTypes = {
  types: PropTypes.arrayOf(PropTypes.number),
  onSubmit: PropTypes.func.isRequired,
  onDismiss: PropTypes.func.isRequired,
};

ReviewConditionForm.defaultProps = {
  types: [],
};
