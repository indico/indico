// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
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

import './ICSCalendarLink.module.scss';

const initialState = {
  open: false,
  url: null,
  text: null,
  source: null,
};

function popupReducer(state, action) {
  switch (action.type) {
    case 'CLOSE':
      return {...state, url: null, open: false};
    case 'OPEN':
      return {open: true, key: action.key, source: action.source};
    case 'LOADED':
      return {...state, url: action.url, source: null};
    default:
      return state;
  }
}

export default function ICSCalendarLink({endpoint, params, renderButton, popupPosition, options}) {
  const [popupState, dispatch] = useReducer(popupReducer, initialState);
  const [copied, setCopied] = useState(false);

  const copyButton = (
    <Button
      icon="copy"
      onClick={async () => {
        await navigator.clipboard.writeText(popupState.url);
        setCopied(true);
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
      const source = indicoAxios.CancelToken.source();
      dispatch({type: 'OPEN', key, source});
      const url = await fetchURL(extraParams, source);
      dispatch({type: 'LOADED', url});
    }
  };

  return (
    <Popup
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
      popperDependencies={[copied]}
      on="click"
      onOpen={async () => {
        const {key, extraParams} = options[0];
        await handleSetOption(key, extraParams);
        setCopied(false);
      }}
      onClose={() => {
        handleClose();
      }}
      wide
    >
      <Header styleName="export-header">
        <Button.Group size="small">
          {options.map(({key, text, extraParams}, idx) => (
            <React.Fragment key={key}>
              <Button
                key={key}
                content={text}
                onClick={() => handleSetOption(key, extraParams)}
                primary={key === popupState.key}
                label={idx === 0 ? Translate.string('Export') : undefined}
                labelPosition={idx === 0 ? 'left' : undefined}
              />
              {idx < options.length - 1 && <Button.Or text={Translate.string('or')} />}
            </React.Fragment>
          ))}
        </Button.Group>
      </Header>
      <Popup.Content>
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
        {copied && (
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
  options: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      text: PropTypes.string.isRequired,
      extraParams: PropTypes.objectOf(PropTypes.string),
    })
  ),
};

ICSCalendarLink.defaultProps = {
  params: {},
  renderButton: null,
  popupPosition: 'left center',
  options: [],
};
