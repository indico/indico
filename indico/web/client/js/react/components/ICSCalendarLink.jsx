// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import signURL from 'indico-url:core.sign_url';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, Dropdown, Icon, Input, Label, Grid, Popup, Header} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {snakifyKeys} from 'indico/utils/case';

import './ICSCalendarLink.module.scss';

export default function ICSCalendarLink({
  endpoint,
  params,
  renderButton,
  dropdownPosition,
  popupPosition,
  options,
  ...restProps
}) {
  const [copied, setCopied] = useState(false);
  const [option, setOption] = useState(null);
  const [open, setOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const copyButton = (
    <Button
      icon="copy"
      onClick={async () => {
        await navigator.clipboard.writeText(option.url);
        setCopied(true);
      }}
    />
  );

  const fetchURL = async extraParams => {
    try {
      const {
        data: {url: signedURL},
      } = await indicoAxios.post(
        signURL(),
        snakifyKeys({endpoint, params: {...params, ...extraParams}})
      );
      return signedURL;
    } catch (error) {
      handleAxiosError(error);
    }
  };

  const handleSetOption = async (text, extraParams) => {
    setOpen(!open);
    setOption({
      text,
      url: await fetchURL(extraParams),
    });
  };

  let trigger;

  if (options.length > 1) {
    trigger = (
      <Dropdown
        styleName="height-full"
        icon={null}
        trigger={
          renderButton ? (
            renderButton(() => {}, {open: dropdownOpen || open})
          ) : (
            <Button icon size="small">
              <Icon name="calendar alternate outline" />
              <Icon name="caret down" />
            </Button>
          )
        }
        pointing={dropdownPosition}
        onOpen={() => {
          setDropdownOpen(true);
        }}
        onClose={() => {
          setDropdownOpen(false);
        }}
        {...restProps}
      >
        <Dropdown.Menu>
          <Dropdown.Header>
            <Translate>Export</Translate>
          </Dropdown.Header>
          <Dropdown.Divider />
          {options.map(({key, text, extraParams}) => (
            <Dropdown.Item
              key={key}
              text={text}
              onClick={() => handleSetOption(text, extraParams)}
            />
          ))}
        </Dropdown.Menu>
      </Dropdown>
    );
  } else {
    const {text, extraParams} = options[0];
    trigger = renderButton ? (
      renderButton(() => handleSetOption(text, extraParams), {open})
    ) : (
      <Button icon size="small" onClick={() => handleSetOption(text, extraParams)}>
        <Icon name="calendar alternate outline" />
        <Icon name="caret down" />
      </Button>
    );
  }

  return (
    <Popup
      trigger={trigger}
      position={popupPosition}
      open={open}
      popperDependencies={[copied]}
      on="click"
      onOpen={() => {
        setCopied(false);
      }}
      onClose={() => {
        setOpen(false);
      }}
      wide
    >
      <Header
        styleName="export-header"
        content={Translate.string('Export')}
        subheader={option && <Label color="blue">{option.text}</Label>}
      />
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
          loading={!option}
          size="mini"
          fluid
          value={option ? option.url : ''}
          action={option && navigator.clipboard && copyButton}
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
            href={option ? option.url : ''}
            icon="download"
            disabled={!option}
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
  dropdownPosition: PropTypes.string,
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
  dropdownPosition: 'top right',
  popupPosition: 'left center',
  options: [],
};
