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
import {Translate, Param} from 'indico/react/i18n';

import './Footer.module.scss';

const buildFooterItems = config => {
  const {
    helpURL,
    hasTos,
    contactEmail,
    tosHtml,
    tosURL,
    hasPrivacyPolicy,
    privacyPolicyHtml,
    privacyPolicyURL,
  } = config;

  const footerItems = [];
  if (helpURL) {
    footerItems.push({
      id: 'help',
      caption: Translate.string('Help'),
      href: helpURL,
    });
  }
  footerItems.push({
    id: 'contact',
    caption: Translate.string('Contact'),
    href: `mailto:${contactEmail}`,
  });
  if (hasTos) {
    footerItems.push({
      id: 'tos',
      caption: Translate.string('Terms and Conditions'),
      href: tosURL,
      modal: tosHtml,
    });
  }
  if (hasPrivacyPolicy) {
    footerItems.push({
      id: 'privacy',
      caption: Translate.string('Privacy'),
      href: privacyPolicyURL,
      modal: privacyPolicyHtml,
    });
  }

  return footerItems;
};

export default function Footer() {
  const [currentModal, setCurrentModal] = useState(false);

  const {data: config} = useIndicoAxios({
    url: configURL(),
    camelize: true,
    trigger: 'once',
  });

  if (!config) {
    return null;
  }

  const triggerModal = (e, id) => {
    setCurrentModal(id);
    e.preventDefault();
  };

  const footerItems = buildFooterItems(config);
  return (
    <div styleName="editing-footer">
      <div styleName="logo">
        <Image src={logoURL({filename: 'indico_small.png'})} styleName="image" />
        <span styleName="text">
          <Translate>
            Powered by <Param name="indico" value={<a href="https://getindico.io">Indico</a>} />
          </Translate>
        </span>
      </div>
      <div styleName="information">
        {footerItems.map(({id, caption, href, modal, ...props}) => (
          <span key={id}>
            <a href={href} onClick={modal && (e => triggerModal(e, id))} {...props}>
              {caption}
            </a>
            {modal && (
              <Modal open={currentModal === id} closeIcon onClose={() => setCurrentModal(false)}>
                <Modal.Header>{caption}</Modal.Header>
                <Modal.Content>
                  <div dangerouslySetInnerHTML={{__html: modal}} />
                </Modal.Content>
              </Modal>
            )}
          </span>
        ))}
      </div>
    </div>
  );
}
