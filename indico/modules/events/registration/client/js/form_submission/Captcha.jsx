import generateCaptcha from 'indico-url:event_registration.api_generate_captcha';

import PropTypes from 'prop-types';
import React, {useEffect, useState} from 'react';
import {Input, Message, Icon, Button, Form} from 'semantic-ui-react';

import {FinalField, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import './Captcha.module.scss';

export default function Captcha({name, regformId}) {
  const [captcha, setCaptcha] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const fetchCaptcha = () => {
    setLoading(true);
    indicoAxios
      .get(generateCaptcha({reg_form_id: regformId}))
      .then(res => {
        setCaptcha(res.data);
        setError(false);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };
  useEffect(fetchCaptcha, [regformId]);

  const parse = val => ({id: captcha.id, answer: val});

  const reloadBtn = (
    <div style={{marginLeft: 'auto'}}>
      <Button icon labelPosition="right" type="button" loading={loading} onClick={fetchCaptcha}>
        <Icon name="redo" />
        Reload
      </Button>
    </div>
  );

  return (
    <Message info style={{marginTop: 25}}>
      <Message.Header>
        <Translate>Confirm that you are not a robot 🤖</Translate>
      </Message.Header>
      <p>
        <Translate>
          Type the characters you see in the image. You can also listen to the audio instead
        </Translate>
      </p>
      <div styleName="captcha">
        {error && (
          <div>
            <Message error>
              <Translate>Failed to load CAPTCHA, try reloading</Translate>
            </Message>
          </div>
        )}
        {!error && captcha && (
          <>
            <div>
              <img src={`data:image/png;base64,${captcha.image}`} />
            </div>
            <div>
              <audio controls src={`data:audio/mp3;base64,${captcha.audio}`}>
                <source src={`data:audio/mp3;base64,${captcha.audio}`} type="audio/mpeg" />
              </audio>
            </div>
            {reloadBtn}
          </>
        )}
        {reloadBtn}
      </div>
      {/* SUI's .error classes only work when there is a parent with .ui.form class.
      Using <Form /> would cause a DOM nesting warning since there is already a plain <form>
      wrapping the whole regform */}
      <div style={{marginTop: 20}} className="ui form">
        <Form.Field>
          <label>Answer</label>
          <FinalField
            name={name}
            required
            parse={parse}
            format={val => val.answer}
            validate={val => v.required(val.answer)}
            component={Input}
            style={{maxWidth: 200}}
          />
        </Form.Field>
      </div>
    </Message>
  );
}

Captcha.propTypes = {
  name: PropTypes.string,
  regformId: PropTypes.number.isRequired,
};

Captcha.defaultProps = {
  name: 'captcha',
};
