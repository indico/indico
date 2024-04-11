// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import ReactDOM from 'react-dom';
import {
  Header,
  HeaderContent,
  Button,
  Input,
  Popup,
  Icon,
  Grid,
  GridColumn,
} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import './ind_share_widget.module.scss';

const copyToClipboard = url => {
  return (
    <Input
      label={
        <Button
          icon="copy"
          onClick={() => navigator.clipboard.writeText(url)}
          content={Translate.string('Copy Link')}
        />
      }
      labelPosition="right"
      defaultValue={url}
      readOnly
      fluid
    />
  );
};

const calendarButtons = (googleCalParams, outlookCalParams) => {
  const calendars = [
    {
      name: Translate.string('Google Calendar'),
      logo: `${Indico.Urls.ImagesBase}/google_cal.svg`,
      url: 'https://www.google.com/calendar/render?',
      params: googleCalParams,
    },
    {
      name: Translate.string('Outlook'),
      logo: `${Indico.Urls.ImagesBase}/outlook.svg`,
      url: 'https://outlook.office.com/calendar/deeplink/compose?',
      color: 'blue',
      params: outlookCalParams,
    },
  ];

  return (
    <Grid columns={2} stretched>
      {calendars.map(calendar => (
        <GridColumn key={calendar.name} styleName="share-button-column">
          <Button
            as="a"
            href={calendar.url + calendar.params}
            target="_blank"
            basic
            color={calendar.color}
            styleName="share-button"
          >
            <img src={calendar.logo} alt={calendar.name} />
            <span>{calendar.name}</span>
          </Button>
        </GridColumn>
      ))}
    </Grid>
  );
};

const socialButtons = text => {
  const networks = [
    {
      name: Translate.string('Mastodon'),
      logo: `${Indico.Urls.ImagesBase}/mastodon.svg`,
      url: `${Indico.User.mastodon_server_url}/share?text=${text}`,
      color: 'violet',
    },
    {
      name: Translate.string('Twitter'),
      logo: `${Indico.Urls.ImagesBase}/twitter.svg`,
      url: `https://twitter.com/intent/tweet?text=${text}`,
      color: 'blue',
    },
  ];

  return (
    <Grid columns={2} stretched>
      {networks.map(network => (
        <GridColumn key={network.name} styleName="share-button-column">
          <Button
            as="a"
            href={network.url}
            target="_blank"
            basic
            color={network.color}
            styleName="share-button"
          >
            <img src={network.logo} alt={network.name} />
            <span>{network.name}</span>
          </Button>
        </GridColumn>
      ))}
    </Grid>
  );
};

function ShareWidget({
  eventName,
  eventStartDt,
  eventUrl,
  shareIcon,
  googleCalParams,
  outlookCalParams,
}) {
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  return (
    <Popup
      trigger={
        <img src={shareIcon} styleName={isPopupOpen ? 'share-widget show' : 'share-widget'} />
      }
      content={
        <>
          <Header
            size="huge"
            icon="share alternate"
            content={Translate.string('Share this page')}
            styleName="header-text"
          />
          <Header size="tiny" styleName="share-section-header">
            <Icon name="linkify" styleName="icon" />
            <HeaderContent styleName="title">
              <Translate>Direct link</Translate>
            </HeaderContent>
          </Header>
          <div>{copyToClipboard(eventUrl)}</div>
          <Header size="tiny" styleName="share-section-header">
            <Icon name="calendar alternate outline" styleName="icon" />
            <HeaderContent styleName="title">
              <Translate>Add to calendar</Translate>
            </HeaderContent>
          </Header>
          {calendarButtons(googleCalParams, outlookCalParams)}
          <Header size="tiny" styleName="share-section-header">
            <Icon name="share square" styleName="icon" />
            <HeaderContent styleName="title">
              <Translate>Share on social media</Translate>
            </HeaderContent>
          </Header>
          {socialButtons(`${eventName} (${eventStartDt}) · Indico (${eventUrl})`)}
        </>
      }
      on="click"
      onOpen={() => setIsPopupOpen(true)}
      onClose={() => setIsPopupOpen(false)}
      position="top right"
      pinned
      wide="very"
      style={{width: '450px'}}
    />
  );
}

customElements.define(
  'ind-share-widget',
  class extends HTMLElement {
    connectedCallback() {
      ReactDOM.render(
        <ShareWidget
          eventName={this.getAttribute('event-name')}
          eventStartDt={this.getAttribute('event-start-dt')}
          eventUrl={this.getAttribute('event-url')}
          shareIcon={this.getAttribute('share-icon')}
          googleCalParams={this.getAttribute('google-cal-params')}
          outlookCalParams={this.getAttribute('outlook-cal-params')}
        />,
        this
      );
    }

    disconnectedCallback() {
      ReactDOM.unmountComponentAtNode(this);
    }
  }
);

ShareWidget.propTypes = {
  eventName: PropTypes.string.isRequired,
  eventStartDt: PropTypes.string.isRequired,
  eventUrl: PropTypes.string.isRequired,
  shareIcon: PropTypes.string.isRequired,
  googleCalParams: PropTypes.string.isRequired,
  outlookCalParams: PropTypes.string.isRequired,
};
