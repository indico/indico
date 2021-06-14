// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import signURL from 'indico-url:core.sign_url';

import PropTypes from 'prop-types';
import React, {useReducer} from 'react';
import {Button, Icon, Input, Label, Grid, Popup, Header} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';

import './ICSCalendarLink.module.scss';

const initialState = {
  key: null,
  open: false,
  url: null,
  source: null,
  copied: false,
};

function popupReducer(state, action) {
  switch (action.type) {
    case 'CLOSE':
      return initialState;
    case 'OPEN':
      return {...initialState, open: true, key: action.key, source: action.source};
    case 'LOADED':
      return {...state, url: action.url, source: null};
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
        {idx < options.length - 1 && <Button.Or text={Translate.string('or')} />}
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

export default function ICSCalendarLink({endpoint, params, renderButton, popupPosition, options}) {
  const [popupState, dispatch] = useReducer(popupReducer, initialState);

  const copyButton = (
    <Button
      icon="copy"
      onClick={async () => {
        await navigator.clipboard.writeText(popupState.url);
        dispatch({type: 'COPIED'});
      }}
    />
  );

  const fetchURL = async (extraParams, source) => {
    try {
      const {
        data: {url: signedURL},
      } = await indicoAxios.post(
        signURL(),
        snakifyKeys({endpoint, params: {...params, ...extraParams}}),
        {cancelToken: source.token}
      );
      return signedURL;
    } catch (error) {
      handleAxiosError(error);
    }
  };

  const handleClose = () => {
    if (popupState.source) {
      popupState.source.cancel();
    }
    dispatch({type: 'CLOSE'});
  };

  const handleSetOption = async (key, extraParams) => {
    if (!popupState.open || popupState.key !== key) {
      if (popupState.source) {
        popupState.source.cancel();
      }
      const source = indicoAxios.CancelToken.source();
      dispatch({type: 'OPEN', key, source});
      const url = await fetchURL(extraParams, source);
      dispatch({type: 'LOADED', url});
    }
  };

  return (
    <Popup
      styleName="popup"
      trigger={
        renderButton ? (
          renderButton({open: popupState.open})
        ) : (
          <Button icon size="small">
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
        <strong styleName="export-option">Synchronise with your calendar</strong>
        <p>
          <Translate>
            You may copy-paste the following URL into your scheduling application. Contents will be
            automatically synchronised.
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
        <strong styleName="export-option">Download</strong>
        <div styleName="download-option">
          <span>
            <Translate>
              Download an iCalendar file that you can use in calendaring applications.
            </Translate>
          </span>
          <Button
            styleName="download-button"
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
};

ICSCalendarLink.defaultProps = {
  params: {},
  renderButton: null,
  popupPosition: 'left center',
  options: ICSExportOptions.defaultProps.options,
};
