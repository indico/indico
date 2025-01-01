// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import signURL from 'indico-url:core.sign_url';

import PropTypes from 'prop-types';
import React, {useReducer, useState} from 'react';
import {Button, Icon, Input, Label, Grid, Popup, Header} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';

import Checkbox from './Checkbox';

import './ICSCalendarLink.module.scss';

const initialState = {
  key: null,
  open: false,
  url: null,
  controller: null,
  copied: false,
};

function popupReducer(state, action) {
  switch (action.type) {
    case 'CLOSE':
      return initialState;
    case 'OPEN':
      return {...initialState, open: true, key: action.key, controller: action.controller};
    case 'LOADED':
      return {...state, url: action.url, controller: null};
    case 'COPIED':
      return {...state, copied: true};
    default:
      return state;
  }
}

const ICSExportOptions = ({options, selected, handleSetOption}) => (
  <Button.Group size="small" styleName="button-group">
    {options.map(({key, text, description, extraParams}, idx) => (
      <React.Fragment key={key}>
        <Popup
          position="top right"
          disabled={description === undefined}
          content={description}
          trigger={
            <Button
              key={key}
              content={text}
              onClick={() => handleSetOption(key, extraParams)}
              primary={key === selected}
              label={idx === 0 ? Translate.string('Export') : undefined}
              labelPosition={idx === 0 ? 'left' : undefined}
            />
          }
        />
      </React.Fragment>
    ))}
  </Button.Group>
);

ICSExportOptions.propTypes = {
  selected: PropTypes.string,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      text: PropTypes.string.isRequired,
      description: PropTypes.string,
      extraParams: PropTypes.objectOf(PropTypes.string),
    })
  ),
  handleSetOption: PropTypes.func.isRequired,
};

ICSExportOptions.defaultProps = {
  selected: undefined,
  options: [],
};

export default function ICSCalendarLink({
  endpoint,
  params,
  renderButton,
  popupPosition,
  options,
  eventInSeries, // only relevant for events, true if the event belongs to an event series
}) {
  const [popupState, dispatch] = useReducer(popupReducer, initialState);
  const [exportEventSeries, setExportEventSeries] = useState(false);

  const copyButton = (
    <Button
      icon="copy"
      title={Translate.string('Copy to clipboard')}
      onClick={async () => {
        await navigator.clipboard.writeText(popupState.url);
        dispatch({type: 'COPIED'});
      }}
    />
  );

  const fetchURL = async (extraParams, controller) => {
    try {
      const {
        data: {url: signedURL},
      } = await indicoAxios.post(
        signURL(),
        snakifyKeys({endpoint, params: {...params, ...extraParams}}),
        {signal: controller.signal}
      );
      return signedURL;
    } catch (error) {
      handleAxiosError(error);
      return null;
    }
  };

  const handleClose = () => {
    if (popupState.controller) {
      popupState.controller.abort();
    }
    dispatch({type: 'CLOSE'});
  };

  const _handleSetOption = async (key, extraParams) => {
    if (popupState.controller) {
      popupState.controller.abort();
    }
    const controller = new AbortController();
    dispatch({type: 'OPEN', key, controller});
    const url = await fetchURL(extraParams, controller);
    if (url !== null) {
      dispatch({type: 'LOADED', url});
    }
  };

  const handleSetOption = (key, extraParams) => {
    if (!popupState.open || popupState.key !== key) {
      if (exportEventSeries) {
        extraParams = {...extraParams, series: true};
      }
      _handleSetOption(key, extraParams);
    }
  };

  return (
    <Popup
      styleName="popup"
      trigger={
        renderButton ? (
          renderButton({open: popupState.open})
        ) : (
          <Button icon size="small" title={Translate.string('Export')}>
            <Icon name="calendar alternate outline" />
            <Icon name="caret down" />
          </Button>
        )
      }
      position={popupPosition}
      open={popupState.open}
      popperDependencies={[popupState.copied]}
      on="click"
      onOpen={async () => {
        const {key, extraParams} = options[0];
        await handleSetOption(key, extraParams);
      }}
      onClose={() => {
        handleClose();
      }}
      wide
    >
      <Header styleName="export-header">
        <ICSExportOptions
          options={options}
          selected={popupState.key}
          handleSetOption={handleSetOption}
        />
      </Header>
      <Popup.Content styleName="content">
        {eventInSeries && (
          <>
            <strong styleName="export-option">
              <Translate>Export options</Translate>
            </strong>
            <div
              styleName="export-event-series"
              onClick={() => {
                const option = options.find(opt => opt.key === popupState.key);
                let extraParams = option?.extraParams || {};
                if (!exportEventSeries) {
                  extraParams = {...extraParams, series: true};
                }
                setExportEventSeries(!exportEventSeries);
                _handleSetOption(popupState.key, extraParams);
              }}
            >
              <Translate>Export all events in this event series</Translate>
              <Checkbox showAsToggle label="" checked={exportEventSeries} />
            </div>
          </>
        )}
        <strong styleName="export-option">
          <Translate>Synchronize with your calendar</Translate>
        </strong>
        <p>
          <Translate>
            You may copy-paste the following URL into your scheduling application. Contents will be
            automatically synchronized.
          </Translate>
        </p>
        <Input
          placeholder={Translate.string('Loading…')}
          readOnly
          loading={!popupState.url}
          size="mini"
          fluid
          value={popupState.url || ''}
          action={popupState.url && navigator.clipboard ? copyButton : null}
        />
        {popupState.copied && (
          <Grid centered>
            <Grid.Row>
              <Label pointing="above" color="teal">
                <Translate>Copied!</Translate>
              </Label>
            </Grid.Row>
          </Grid>
        )}
        <strong styleName="export-option">
          <Translate>Download</Translate>
        </strong>
        <div styleName="download-option">
          <span>
            <Translate>
              Download an iCalendar file that you can use in calendaring applications.
            </Translate>
          </span>
          <Button
            styleName="download-button"
            title={Translate.string('Download')}
            as="a"
            href={popupState.url}
            icon="download"
            loading={!popupState.url}
            disabled={!popupState.url}
          />
        </div>
      </Popup.Content>
    </Popup>
  );
}

ICSCalendarLink.propTypes = {
  endpoint: PropTypes.string.isRequired,
  params: PropTypes.objectOf(PropTypes.string),
  renderButton: PropTypes.func,
  popupPosition: PropTypes.string,
  options: ICSExportOptions.propTypes.options,
  eventInSeries: PropTypes.bool,
};

ICSCalendarLink.defaultProps = {
  params: {},
  renderButton: null,
  popupPosition: 'left center',
  options: ICSExportOptions.defaultProps.options,
  eventInSeries: false,
};
