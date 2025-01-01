// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import requestURL from 'indico-url:users.api_user_data_export';

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import ReactDOM from 'react-dom';
import {Button, Icon, Label, Message, Table} from 'semantic-ui-react';

import {handleSubmitError} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import DataExportForm from './DataExportForm';
import './DataExport.module.scss';

function DataExport({userId, request, exportOptions}) {
  const userIdArgs = userId !== null ? {user_id: userId} : {};
  const [state, setState] = useState(request.state);

  const onSubmit = async data => {
    const {includeFiles, options} = data;
    const selection = Object.keys(_.pickBy(options));
    let resp;
    try {
      resp = await indicoAxios.post(requestURL(userIdArgs), {
        include_files: includeFiles,
        options: selection,
      });
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
          {state === 'none' && <DataExportForm onSubmit={onSubmit} exportOptions={exportOptions} />}
          {state === 'running' && <ExportRunning />}
          {state === 'success' && (
            <ExportSuccess request={request} exportOptions={exportOptions} setState={setState} />
          )}
          {state === 'failed' && <ExportFailed setState={setState} />}
          {state === 'expired' && <ExportExpired setState={setState} />}
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

function ExportRunning() {
  return (
    <div>
      <Message info>
        <Message.Header>
          <Translate context="user data export">
            Your data is being prepared. We will notify you by email once it is available for
            download.
          </Translate>
        </Message.Header>
      </Message>
    </div>
  );
}

function ExportSuccess({request, exportOptions, setState}) {
  return (
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
              Some files were not exported due to exceeding the maximum allowed size of the archive.
              Consider selecting less options
            </Translate>
          </Message>
        )}
        <InfoTable request={request} exportOptions={exportOptions} />
        <div style={{display: 'flex', justifyContent: 'flex-end', gap: '0.5em'}}>
          <Button onClick={() => setState('none')}>
            <Translate context="user data export">New export</Translate>
          </Button>
          <Button primary icon labelPosition="right" as="a" href={request.url}>
            <Translate>Download</Translate>
            <Icon name="download" />
          </Button>
        </div>
      </div>
    </div>
  );
}

ExportSuccess.propTypes = {
  request: PropTypes.object.isRequired,
  exportOptions: PropTypes.array.isRequired,
  setState: PropTypes.func.isRequired,
};

function ExportFailed({setState}) {
  return (
    <div>
      <Message negative>
        <Message.Header>
          <Translate context="user data export">Data export failed</Translate>
        </Message.Header>
        <Translate as="p" context="user data export">
          You can request a new one
        </Translate>
      </Message>
      <div style={{display: 'flex', justifyContent: 'flex-end'}}>
        <Button primary icon labelPosition="right" onClick={() => setState('none')}>
          <Translate>Retry</Translate>
          <Icon name="redo" />
        </Button>
      </div>
    </div>
  );
}

ExportFailed.propTypes = {
  setState: PropTypes.func.isRequired,
};

function ExportExpired({setState}) {
  return (
    <div>
      <Message warning>
        <Message.Header>
          <Translate>Download link expired</Translate>
        </Message.Header>
      </Message>
      <div style={{display: 'flex', justifyContent: 'flex-end'}}>
        <Button primary onClick={() => setState('none')} icon labelPosition="right">
          <Translate context="user data export">New export</Translate>
          <Icon name="zip" />
        </Button>
      </div>
    </div>
  );
}

ExportExpired.propTypes = {
  setState: PropTypes.func.isRequired,
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
            <Translate context="user data export">Contents</Translate>
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

window.setupDataExport = function setupDataExport(userId, request, exportOptions) {
  document.addEventListener('DOMContentLoaded', () => {
    ReactDOM.render(
      <DataExport userId={userId} request={camelizeKeys(request)} exportOptions={exportOptions} />,
      document.querySelector('#data-export-container')
    );
  });
};
