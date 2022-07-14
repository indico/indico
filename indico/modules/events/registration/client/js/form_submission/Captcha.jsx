// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import generateCaptchaURL from 'indico-url:core.generate_captcha';

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {Message, Icon, Button, Form, Popup, Placeholder} from 'semantic-ui-react';

import {FinalInput} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import './Captcha.module.scss';

export default function Captcha({name}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [image, setImage] = useState(null);
  const [audio, setAudio] = useState(null);

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
        <Button icon type="button" disabled={loading || error || !audio} onClick={toggleAudio}>
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
          icon
          type="button"
          loading={loading}
          disabled={loading}
          onClick={() => {
            if (playing) {
              toggleAudio();
            }
            fetchCaptcha();
          }}
        >
          <Icon name="redo" />
        </Button>
      }
    />
  );

  return (
    <Message info style={{marginTop: 25}}>
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
          <div style={{marginTop: 20}} className="ui form">
            <Form.Field>
              <label>
                <Translate>Answer</Translate>
              </label>
              <FinalInput name={name} required style={{maxWidth: 200}} />
            </Form.Field>
          </div>
        </>
      )}
    </Message>
  );
}

Captcha.propTypes = {
  name: PropTypes.string,
};

Captcha.defaultProps = {
  name: 'captcha',
};
