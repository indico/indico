// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import requestURL from 'indico-url:users.api_user_data_export';

import {FORM_ERROR} from 'final-form';
import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import ReactDOM from 'react-dom';
import {Form as FinalForm} from 'react-final-form';
import {Button, Form, Icon, Label, List, Message, Table} from 'semantic-ui-react';

import {FinalCheckbox, FinalSubmitButton, handleSubmitError} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import './DataExport.module.scss';

function DataExportForm({onSubmit, exportOptions}) {
  return (
    <FinalForm
      onSubmit={onSubmit}
      initialValues={{}}
      initialValuesEqual={_.isEqual}
      validate={values => {
        if (!Object.values(values).some(v => v)) {
          return {
            [FORM_ERROR]: Translate.string('At least one option must be selected'),
          };
        }
      }}
    >
      {fprops => (
        <Form onSubmit={fprops.handleSubmit}>
          <Translate as="p">Select what data you would like to export below:</Translate>
          <List relaxed>
            {exportOptions.map(([key, name]) => (
              <List.Item key={key}>
                <List.Content>
                  <List.Header>
                    <FinalCheckbox name={key} label={<label>{name}</label>} />
                  </List.Header>
                </List.Content>
              </List.Item>
            ))}
          </List>
          <div style={{textAlign: 'right'}}>
            <FinalSubmitButton label={Translate.string('Export my data')} />
          </div>
        </Form>
      )}
    </FinalForm>
  );
}

DataExportForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  exportOptions: PropTypes.array.isRequired,
};

function InfoTable({request, exportOptions}) {
  return (
    <Table celled>
      <Table.Header>
        <Table.Row>
          <Table.HeaderCell>
            <Translate context="user data export request date">Requested on</Translate>
          </Table.HeaderCell>
          <Table.HeaderCell>
            <Translate>Contents</Translate>
          </Table.HeaderCell>
        </Table.Row>
      </Table.Header>

      <Table.Body>
        <Table.Row>
          <Table.Cell>{moment(request.requestedDt).format('L')}</Table.Cell>
          <Table.Cell>
            {request.selectedOptions.map(opt => (
              <Label styleName="option-label" key={opt}>
                {exportOptions.find(([o]) => o === opt)[1]}
              </Label>
            ))}
          </Table.Cell>
        </Table.Row>
      </Table.Body>
    </Table>
  );
}

InfoTable.propTypes = {
  request: PropTypes.shape({
    requestedDt: PropTypes.string.isRequired,
    selectedOptions: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  exportOptions: PropTypes.array.isRequired,
};

function DataExport({userId, request, exportOptions}) {
  const userIdArgs = userId !== null ? {user_id: userId} : {};
  const [state, setState] = useState(request.state);

  const onSubmit = async data => {
    const selection = Object.keys(_.pickBy(data));
    let resp;
    try {
      resp = await indicoAxios.post(requestURL(userIdArgs), {options: selection});
    } catch (e) {
      return handleSubmitError(e);
    }
    setState(resp.data.state);
  };

  return (
    <div className="i-box-group vert">
      <div className="i-box">
        <div className="i-box-header">
          <div className="i-box-title">
            <Translate>Data export</Translate>
          </div>
        </div>
        <div className="i-box-content ui">
          <Translate as="p">
            Here, you can request to export all data concerning you that is currently stored in
            Indico.
          </Translate>
          <div styleName="divider" />
          <div styleName="data-export-body">
            {state === 'pending' && (
              <DataExportForm onSubmit={onSubmit} exportOptions={exportOptions} />
            )}
            {state === 'running' && (
              <div>
                <Message info>
                  <Message.Header>
                    <Translate>
                      We are preparing your data. We will notify you via email when the export is
                      finished.
                    </Translate>
                  </Message.Header>
                </Message>
              </div>
            )}
            {state === 'success' && (
              <div>
                <div>
                  <Message positive>
                    <Message.Header>
                      <Translate>Your data export is ready</Translate>
                    </Message.Header>
                    <Translate as="p" context="user data export">
                      You can download it from the link below
                    </Translate>
                  </Message>
                  {request.maxSizeExceeded && (
                    <Message warning>
                      <Translate as="p" context="user data export">
                        Some files were not exported due to exceeding the maximum allowed size of
                        the archive. Consider selecting less options
                      </Translate>
                    </Message>
                  )}
                  <InfoTable request={request} exportOptions={exportOptions} />
                  <div style={{display: 'flex', justifyContent: 'space-between'}}>
                    <Button primary icon labelPosition="right" as="a" href={request.url}>
                      <Translate>Download</Translate>
                      <Icon name="download" />
                    </Button>
                    <Button onClick={() => setState('pending')}>
                      <Translate>New export</Translate>
                    </Button>
                  </div>
                </div>
              </div>
            )}
            {state === 'failed' && (
              <div>
                <Message negative>
                  <Message.Header>
                    <Translate>Data export failed</Translate>
                  </Message.Header>
                  <Translate as="p" context="user data export">
                    You can request a new one
                  </Translate>
                </Message>
                <div>
                  <Button primary icon labelPosition="right" onClick={() => setState('pending')}>
                    <Translate>Retry</Translate>
                    <Icon name="redo" />
                  </Button>
                </div>
              </div>
            )}
            {state === 'expired' && (
              <div>
                <Message warning>
                  <Message.Header>
                    <Translate>Download link expired</Translate>
                  </Message.Header>
                </Message>
                <div>
                  <Button primary onClick={() => setState('pending')} icon labelPosition="right">
                    <Translate>New export</Translate>
                    <Icon name="zip" />
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

DataExport.propTypes = {
  userId: PropTypes.number,
  request: PropTypes.shape({
    state: PropTypes.string.isRequired,
    requestedDt: PropTypes.string,
    selectedOptions: PropTypes.array,
    maxSizeExceeded: PropTypes.bool,
    url: PropTypes.string,
  }).isRequired,
  exportOptions: PropTypes.array.isRequired,
};

DataExport.defaultProps = {
  userId: null,
};

window.setupDataExport = function setupDataExport(userId, request, exportOptions) {
  document.addEventListener('DOMContentLoaded', () => {
    ReactDOM.render(
      <DataExport userId={userId} request={camelizeKeys(request)} exportOptions={exportOptions} />,
      document.querySelector('#data-export-container')
    );
  });
};
