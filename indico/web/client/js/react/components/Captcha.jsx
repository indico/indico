// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import generateCaptchaURL from 'indico-url:core.generate_captcha';

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {useFormState} from 'react-final-form';
import {Message, Icon, Button, Form, Popup, Placeholder, Input} from 'semantic-ui-react';

import {FinalInput} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {renderPluginComponents} from 'indico/utils/plugins';

import './Captcha.module.scss';

export default function Captcha({name, settings, wtf}) {
  const pluginCaptcha = renderPluginComponents('captcha', {settings, wtf});
  if (pluginCaptcha.length) {
    return pluginCaptcha;
  }
  return <IndicoCaptcha name={name} wtf={wtf} />;
}

Captcha.propTypes = {
  name: PropTypes.string,
  wtf: PropTypes.bool,
  settings: PropTypes.object,
};

Captcha.defaultProps = {
  name: 'captcha',
  wtf: false,
  settings: {},
};

function IndicoCaptcha({name, wtf}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [image, setImage] = useState(null);
  const [audio, setAudio] = useState(null);
  const {submitting} = wtf
    ? {submitting: false}
    : // eslint-disable-next-line react-hooks/rules-of-hooks
      useFormState({
        subscription: {
          submitting: true,
        },
      });

  const fetchCaptcha = async () => {
    setLoading(true);
    setError(false);
    try {
      const {data} = await indicoAxios.get(generateCaptchaURL());
      setImage(`data:image/png;base64,${data.image}`);
      const newAudio = new Audio(`data:audio/mp3;base64,${data.audio}`);
      newAudio.onended = () => setPlaying(false);
      setAudio(newAudio);
    } catch (err) {
      setError(true);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => fetchCaptcha(), []);

  const toggleAudio = () => {
    if (playing) {
      audio.pause();
      audio.currentTime = 0;
    } else {
      audio.play();
    }
    setPlaying(p => !p);
  };

  const playBtn = (
    <Popup
      content={playing ? Translate.string('Pause') : Translate.string('Play')}
      trigger={
        <Button
          styleName="captcha-control"
          icon
          type="button"
          disabled={loading || error || !audio || submitting}
          onClick={toggleAudio}
        >
          <Translate as="span">Hear the characters</Translate>
          <Icon name={playing ? 'stop' : 'play'} />
        </Button>
      }
    />
  );

  const reloadBtn = (
    <Popup
      content={Translate.string('Refresh CAPTCHA')}
      trigger={
        <Button
          styleName="captcha-control"
          icon
          type="button"
          loading={loading}
          disabled={loading || submitting}
          onClick={() => {
            if (playing) {
              toggleAudio();
            }
            fetchCaptcha();
          }}
        >
          <Translate as="span">Try different characters</Translate>
          <Icon name="redo" />
        </Button>
      }
    />
  );

  return (
    <Message info style={wtf ? {marginTop: 0} : {marginTop: 25}}>
      <Message.Header>
        <Translate>Confirm that you are not a robot</Translate> 🤖
      </Message.Header>
      <p>
        <Translate>
          Type the characters you see in the image. You can also listen to the audio instead
        </Translate>
      </p>
      {error && (
        <div styleName="error">
          <Message error>
            <Translate>Failed to load CAPTCHA, try refreshing it</Translate>
          </Message>
          {reloadBtn}
        </div>
      )}
      {!error && (
        <>
          <div styleName="captcha">
            {image ? <img src={image} /> : <Placeholder style={{width: 160, height: 60}} />}
            <Button.Group icon>
              {playBtn}
              {reloadBtn}
            </Button.Group>
          </div>
          {/* SUI's .error classes only work when there is a parent with .ui.form class.
              Using <Form /> would cause a DOM nesting warning since there is already a plain <form>
              wrapping the whole regform */}
          <div styleName="captcha-form" className="ui form">
            <Form.Field>
              <label styleName="captcha-answer">
                <Translate as="span">Answer</Translate>
                {wtf ? (
                  <Input name={name} id="input-captcha" required style={{maxWidth: 200}} />
                ) : (
                  <FinalInput name={name} id="input-captcha" required style={{maxWidth: 200}} />
                )}
              </label>
            </Form.Field>
          </div>
        </>
      )}
    </Message>
  );
}

IndicoCaptcha.propTypes = {
  name: PropTypes.string.isRequired,
  wtf: PropTypes.bool.isRequired,
};
