// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import userPreferencesMastodonServer from 'indico-url:users.user_preferences_mastodon_server';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import ReactDOM from 'react-dom';
import {Form as FinalForm, Field} from 'react-final-form';
import {
  Header,
  HeaderContent,
  Button,
  Input,
  Popup,
  Icon,
  Grid,
  GridColumn,
  Message,
} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import './ind_share_widget.module.scss';

function CopyToClipboard({eventUrl, setCopied, isCopied}) {
  useEffect(() => {
    if (isCopied) {
      const timer = setTimeout(() => setCopied(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [isCopied, setCopied]);

  return (
    <Input
      label={
        <Button
          icon={isCopied ? 'check' : 'copy'}
          positive={isCopied}
          onClick={() => {
            navigator.clipboard.writeText(eventUrl);
            setCopied(true);
          }}
          content={isCopied ? Translate.string('Copied!') : Translate.string('Copy Link')}
        />
      }
      labelPosition="right"
      defaultValue={eventUrl}
      readOnly
      fluid
    />
  );
}

CopyToClipboard.propTypes = {
  eventUrl: PropTypes.string.isRequired,
  setCopied: PropTypes.func.isRequired,
  isCopied: PropTypes.bool.isRequired,
};

function CalendarButtons({googleCalParams, outlookCalParams}) {
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
            href={`${calendar.url}${calendar.params}`}
            target="_blank"
            basic
            color={calendar.color}
            styleName="share-button"
          >
            <img src={calendar.logo} alt={calendar.name} />
            <Translate as="span">{calendar.name}</Translate>
          </Button>
        </GridColumn>
      ))}
    </Grid>
  );
}

CalendarButtons.propTypes = {
  googleCalParams: PropTypes.string.isRequired,
  outlookCalParams: PropTypes.string.isRequired,
};

function TwitterButton({shareText}) {
  return (
    <GridColumn styleName="share-button-column">
      <Button
        as="a"
        href={`https://twitter.com/intent/tweet?text=${shareText}`}
        target="_blank"
        basic
        color="blue"
        styleName="share-button"
      >
        <img src={`${Indico.Urls.ImagesBase}/twitter.svg`} alt={Translate.string('Twitter')} />
        <Translate>Twitter</Translate>
      </Button>
    </GridColumn>
  );
}

TwitterButton.propTypes = {
  shareText: PropTypes.string.isRequired,
};

function MastodonButton({shareText, setMastodonOpen}) {
  const href = Indico.User.mastodonServerURL
    ? `${Indico.User.mastodonServerURL}/share?text=${shareText}`
    : null;
  const isLoggedIn = !_.isEmpty(Indico.User);
  const button = (
    <Button
      basic
      color={isLoggedIn ? 'violet' : 'grey'}
      styleName="share-button"
      as="a"
      target="_blank"
      href={href}
    >
      <img src={`${Indico.Urls.ImagesBase}/mastodon.svg`} alt={Translate.string('Mastodon')} />
      <Translate>Mastodon</Translate>
    </Button>
  );

  return (
    <GridColumn styleName="share-button-column">
      {isLoggedIn ? (
        <SetupMastodonServer
          button={button}
          setMastodonOpen={setMastodonOpen}
          shareText={shareText}
        />
      ) : (
        <Popup
          trigger={button}
          content={Translate.string('Please login to share on Mastodon')}
          position="top right"
          wide
        />
      )}
    </GridColumn>
  );
}

MastodonButton.propTypes = {
  shareText: PropTypes.string.isRequired,
  setMastodonOpen: PropTypes.func.isRequired,
};

function SetupMastodonServer({setMastodonOpen, button, shareText}) {
  const [error, setError] = useState(false);
  const [serverURL, setServerURL] = useState(null);

  useEffect(() => {
    if (serverURL) {
      Indico.User.mastodonServerURL = serverURL;
    }
  }, [serverURL]);

  if (Indico.User.mastodonServerURL) {
    return button;
  }

  return (
    <Popup
      wide
      pinned
      position="top right"
      onOpen={() => setMastodonOpen(true)}
      onClose={() => {
        setError(false);
        setMastodonOpen(false);
      }}
      trigger={button}
      on="click"
    >
      <Popup.Content>
        {!serverURL ? (
          <>
            <Message icon info styleName="empty-mastodon-server-notice">
              <Icon name="star" />
              <Translate>
                You have not added a preferred Mastodon server on your profile yet. Please add one
                below.
              </Translate>
            </Message>
            <FinalForm
              onSubmit={async ({mastodonServerURL}) => {
                try {
                  await indicoAxios.post(userPreferencesMastodonServer(), {
                    server_url: mastodonServerURL,
                  });
                  setError(false);
                } catch (e) {
                  if (_.get(e, 'response.status') !== 418) {
                    return handleAxiosError(e);
                  }
                  setError(e.response.data.message);
                  return;
                }
                setServerURL(mastodonServerURL);
              }}
              render={({handleSubmit}) => (
                <form onSubmit={handleSubmit}>
                  <Field
                    name="mastodonServerURL"
                    render={({input}) => (
                      <Input
                        error={!!error}
                        label={
                          <Button
                            icon="save"
                            positive
                            type="submit"
                            content={Translate.string('Save')}
                          />
                        }
                        required
                        labelPosition="right"
                        placeholder="https://mastodon.social"
                        fluid
                        {...input}
                      />
                    )}
                  />
                  {error && (
                    <div styleName="error-message">
                      <Icon name="times" />
                      {error}
                    </div>
                  )}
                </form>
              )}
            />
          </>
        ) : (
          <>
            <Message icon positive styleName="saved-mastodon-server-notice">
              <Icon name="check circle outline" />
              <Translate>
                Preferred Mastodon server added! You can now share this event below.
              </Translate>
            </Message>

            <Button
              as="a"
              target="_blank"
              href={`${serverURL}/share?text=${shareText}`}
              icon="share square"
              content={Translate.string('Share on Mastodon')}
              positive
              fluid
              onClick={() => setMastodonOpen(false)}
            />
          </>
        )}
      </Popup.Content>
    </Popup>
  );
}

SetupMastodonServer.propTypes = {
  setMastodonOpen: PropTypes.func.isRequired,
  button: PropTypes.element.isRequired,
  shareText: PropTypes.string.isRequired,
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
  const [isMastodonOpen, setMastodonOpen] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  const shareText = `${eventName} (${eventStartDt}) · Indico (${eventUrl})`;
  return (
    <Popup
      trigger={
        <img
          src={shareIcon}
          styleName={isPopupOpen ? 'share-widget show' : 'share-widget'}
          tabIndex={0}
          aria-label={Translate.string('Share this page')}
          aria-modal
        />
      }
      content={
        <>
          <div styleName="share-header-title">
            <Icon name="share alternate" styleName="icon" />
            <Translate as="strong">Share this page</Translate>
          </div>
          <Header size="tiny" styleName="share-section-header">
            <Icon name="linkify" styleName="icon" />
            <HeaderContent styleName="title">
              <Translate>Direct link</Translate>
            </HeaderContent>
          </Header>
          <CopyToClipboard eventUrl={eventUrl} setCopied={setIsCopied} isCopied={isCopied} />
          <Header size="tiny" styleName="share-section-header">
            <Icon name="calendar alternate outline" styleName="icon" />
            <HeaderContent styleName="title">
              <Translate>Add to calendar</Translate>
            </HeaderContent>
          </Header>
          <CalendarButtons googleCalParams={googleCalParams} outlookCalParams={outlookCalParams} />
          <Header size="tiny" styleName="share-section-header">
            <Icon name="share square" styleName="icon" />
            <HeaderContent styleName="title">
              <Translate>Share on social media</Translate>
            </HeaderContent>
          </Header>
          <Grid columns={2} stretched>
            <MastodonButton shareText={shareText} setMastodonOpen={setMastodonOpen} />
            <TwitterButton shareText={shareText} />
          </Grid>
        </>
      }
      on="click"
      onOpen={() => setIsPopupOpen(true)}
      onClose={() => !isMastodonOpen && setIsPopupOpen(false)}
      position="top right"
      pinned
      open={isPopupOpen}
      wide="very"
      style={{width: '450px'}}
    />
  );
}

ShareWidget.propTypes = {
  eventName: PropTypes.string.isRequired,
  eventStartDt: PropTypes.string.isRequired,
  eventUrl: PropTypes.string.isRequired,
  shareIcon: PropTypes.string.isRequired,
  googleCalParams: PropTypes.string.isRequired,
  outlookCalParams: PropTypes.string.isRequired,
};

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
