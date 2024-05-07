// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import userPreferencesMastodonServer from 'indico-url:users.user_preferences_mastodon_server';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
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

function CopyToClipboard({eventUrl}) {
  return (
    <Input
      label={
        <Button
          icon="copy"
          onClick={() => navigator.clipboard.writeText(eventUrl)}
          content={Translate.string('Copy Link')}
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
};

function CalendarButtons({googleCalParams, outlookCalParams}) {
  const calendars = [
    {
      name: 'Google Calendar',
      logo: `${Indico.Urls.ImagesBase}/google_cal.svg`,
      url: 'https://www.google.com/calendar/render?',
      params: googleCalParams,
    },
    {
      name: 'Outlook',
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
            <img src={calendar.logo} alt={Translate.string(calendar.name)} />
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

function SocialButton({name, logo, url, color, render, button, buttonProps}) {
  const buttonElement = button ? (
    <Button basic color={color} styleName="share-button" {...buttonProps}>
      <img src={logo} alt={Translate.string(name)} />
      <span>{name}</span>
    </Button>
  ) : (
    <Button as="a" href={url} target="_blank" basic color={color} styleName="share-button">
      <img src={logo} alt={Translate.string(name)} />
      <span>{name}</span>
    </Button>
  );
  return (
    <GridColumn styleName="share-button-column">
      {render ? render(buttonElement) : buttonElement}
    </GridColumn>
  );
}

SocialButton.propTypes = {
  name: PropTypes.string.isRequired,
  logo: PropTypes.string.isRequired,
  url: PropTypes.string,
  color: PropTypes.string.isRequired,
  render: PropTypes.func.isRequired,
  button: PropTypes.bool,
  buttonProps: PropTypes.object,
};

SocialButton.defaultProps = {
  url: null,
  button: false,
  buttonProps: {},
};

function SetupMastodonServer({setMastodonOpen, button}) {
  const [error, setError] = useState(false);
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
              await indicoAxios.patch(userPreferencesMastodonServer(), {
                server_url: mastodonServerURL,
              });
              setError(null);
            } catch (e) {
              if (_.get(e, 'response.status') !== 418) {
                return handleAxiosError(e);
              }
              setError(e.response.data.message);
              return;
            }
            setMastodonOpen(false);
            Indico.User.mastodonServerURL = mastodonServerURL;
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
                    id="mastodon-server-url"
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
      </Popup.Content>
    </Popup>
  );
}

SetupMastodonServer.propTypes = {
  setMastodonOpen: PropTypes.func.isRequired,
  button: PropTypes.element.isRequired,
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
          <CopyToClipboard eventUrl={eventUrl} />
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
            <SocialButton
              name="Mastodon"
              logo={`${Indico.Urls.ImagesBase}/mastodon.svg`}
              color="violet"
              render={button => (
                <SetupMastodonServer button={button} setMastodonOpen={setMastodonOpen} />
              )}
              button
              buttonProps={{
                as: 'a',
                target: '_blank',
                href: Indico.User.mastodonServerURL
                  ? `${Indico.User.mastodonServerURL}/share?text=${eventName} (${eventStartDt}) · Indico (${eventUrl})`
                  : null,
              }}
            />
            <SocialButton
              name="Twitter"
              logo={`${Indico.Urls.ImagesBase}/twitter.svg`}
              url={`https://twitter.com/intent/tweet?text=${eventName} (${eventStartDt}) · Indico (${eventUrl})`}
              color="blue"
              render={button => button}
            />
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
