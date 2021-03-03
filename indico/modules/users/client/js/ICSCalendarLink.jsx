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

export default function ICSCalendarLink({endpoint, params, options, ...restProps}) {
  const [copied, setCopied] = useState(false);
  const [option, setOption] = useState(null);
  const [open, setOpen] = useState(false);

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

  const trigger = (
    <Dropdown
      {...restProps}
      icon={null}
      trigger={
        <Button icon size="small">
          <Icon name="calendar alternate outline" />
          <Icon name="caret down" />
        </Button>
      }
      pointing="top right"
    >
      <Dropdown.Menu>
        <Dropdown.Header>
          <Translate>Synchronise with your calendar</Translate>
        </Dropdown.Header>
        <Dropdown.Divider />
        {options.map(({key, text, extraParams}) => (
          <Dropdown.Item
            key={key}
            text={text}
            onClick={async () => {
              setOption({
                text,
                url: await fetchURL(extraParams),
              });
              setOpen(true);
            }}
          />
        ))}
      </Dropdown.Menu>
    </Dropdown>
  );

  return (
    <Popup
      trigger={trigger}
      position="left center"
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
        content={Translate.string('Sync with your calendar')}
        subheader={option && <Label color="blue">{option.text}</Label>}
      />
      <Popup.Content>
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
      </Popup.Content>
    </Popup>
  );
}

ICSCalendarLink.propTypes = {
  endpoint: PropTypes.string.isRequired,
  params: PropTypes.objectOf(PropTypes.string),
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
  options: [],
};
