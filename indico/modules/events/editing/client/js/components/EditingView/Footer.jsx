// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.
import logoURL from 'indico-url:assets.image';
import configURL from 'indico-url:core.config';

import React, {useState} from 'react';
import {Image, Modal} from 'semantic-ui-react';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import './Footer.module.scss';

export default function Footer() {
  const [tosModal, setTosModal] = useState(false);

  const {data} = useIndicoAxios({
    url: configURL(),
    camelize: true,
    trigger: 'once',
  });

  const config = data;
  if (!config) {
    return null;
  }

  const {helpURL, hasTos, contactEmail, tosHtml} = config;
  return (
    <div styleName="editing-footer">
      <div styleName="logo">
        <Image src={logoURL({filename: 'indico_small.png'})} styleName="image" />
        <span styleName="text">
          <Translate>Powered by </Translate>
          <a href="http://getindico.io">Indico</a>
        </span>
      </div>
      <div styleName="information">
        {helpURL && (
          <span>
            <a href={helpURL}>
              <Translate>Help</Translate>
            </a>
          </span>
        )}
        <span>
          <a href={`mailto: ${contactEmail}`}>
            <Translate>Contact</Translate>
          </a>
        </span>
        {hasTos && tosHtml && (
          <Modal
            open={tosModal}
            closeIcon
            onClose={() => setTosModal(false)}
            trigger={
              <span>
                <a onClick={() => setTosModal(true)}>
                  <Translate>Terms and Conditions</Translate>
                </a>
              </span>
            }
          >
            <Modal.Header>
              <Translate>Terms and Conditions</Translate>
            </Modal.Header>
            <Modal.Content>
              <div dangerouslySetInnerHTML={{__html: tosHtml}} />
            </Modal.Content>
          </Modal>
        )}
      </div>
    </div>
  );
}
