// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {FORM_ERROR} from 'final-form';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Form, Header, List} from 'semantic-ui-react';

import {FinalCheckbox, FinalSubmitButton} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import './DataExportForm.module.scss';

const descriptions = {
  personal_data: Translate.string('Basic information about your account'),
  settings: Translate.string('Your global Indico settings'),
  contribs: Translate.string('Data about your contributions in events'),
  note_revisions: Translate.string('Data about minutes you wrote in events'),
  registrations: Translate.string('Data you submitted when registering for events'),
  room_booking: Translate.string('Your rooms and reservations'),
  abstracts_papers: Translate.string('Data about your abstract and paper submissions'),
  survey_submissions: Translate.string('Your survey answers'),
  attachments: Translate.string('Data about materials you uploaded'),
  editables: Translate.string('Data about editables submitted through the Editing module'),
  misc: Translate.string('Other data such as your API tokens and OAuth applications'),
};

export default function DataExportForm({onSubmit, exportOptions}) {
  return (
    <>
      <p styleName="form-description">
        <Translate>
          Here, you can request to export all data concerning you that is currently stored in
          Indico.
        </Translate>
      </p>
      <FinalForm
        onSubmit={onSubmit}
        initialValues={{includeFiles: false, options: {}}}
        initialValuesEqual={_.isEqual}
        validate={({options}) => {
          if (!Object.values(options).some(v => v)) {
            return {
              [FORM_ERROR]: Translate.string(
                'At least one option in the data section must be selected'
              ),
            };
          }
        }}
      >
        {fprops => (
          <Form onSubmit={fprops.handleSubmit}>
            <DataSelection exportOptions={exportOptions} />
            <AdditionalOptions />
            <div styleName="submit">
              <FinalSubmitButton label={Translate.string('Export my data')} />
            </div>
          </Form>
        )}
      </FinalForm>
    </>
  );
}

DataExportForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  exportOptions: PropTypes.array.isRequired,
};

function DataSelection({exportOptions}) {
  return (
    <>
      <Header size="medium" dividing>
        <Translate context="user data export">Data selection</Translate>
      </Header>
      <List>
        {exportOptions.map(([key, name]) => (
          <List.Item key={key}>
            <List.Content>
              <Toggle name={`options.${key}`} title={name} description={descriptions[key]} />
            </List.Content>
          </List.Item>
        ))}
      </List>
    </>
  );
}

DataSelection.propTypes = {
  exportOptions: PropTypes.array.isRequired,
};

function AdditionalOptions() {
  return (
    <>
      <Header size="medium" dividing>
        <Translate context="user data export">Additional options</Translate>
      </Header>
      <List>
        <List.Item>
          <List.Content>
            <Toggle
              name="includeFiles"
              title={Translate.string('Include files')}
              description={Translate.string(
                'If checked, for each selected option, a copy of all your uploaded files ' +
                  'will be included in the export. Note that depending on the number of ' +
                  'files, this may significantly increase the download size of the export'
              )}
            />
          </List.Content>
        </List.Item>
      </List>
    </>
  );
}

function Toggle({name, title, description}) {
  return (
    <div styleName="toggle">
      <FinalCheckbox name={name} label={title} />
      <div styleName="description">{description}</div>
    </div>
  );
}

Toggle.propTypes = {
  name: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
};
