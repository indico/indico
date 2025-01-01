// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contactURL from 'indico-url:core.contact';
import privacyPolicyURL from 'indico-url:legal.display_privacy';
import tosURL from 'indico-url:legal.display_tos';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {connect} from 'react-redux';
import {Icon, Menu, Modal} from 'semantic-ui-react';

import {ResponsivePopup} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {Responsive} from 'indico/react/util';

import {selectors as configSelectors} from '../common/config';

const buildMenuItems = (
  helpURL,
  hasTOS,
  hasTOSHTML,
  hasPrivacyPolicy,
  hasPrivacyPolicyHTML,
  contactEmail
) => {
  const menuItems = [
    [
      'help',
      {
        href: helpURL,
        target: '_blank',
        rel: 'noopener noreferrer',
        caption: Translate.string('Help'),
        icon: 'question',
      },
    ],
  ];

  if (contactEmail) {
    menuItems.push([
      'contact',
      {
        href: contactURL(),
        modal: true,
        caption: Translate.string('Contact'),
        icon: 'at',
      },
    ]);
  }
  if (hasTOS) {
    menuItems.push([
      'tos',
      {
        href: tosURL(),
        modal: hasTOSHTML,
        target: '_blank',
        rel: 'noopener noreferrer',
        caption: Translate.string('Terms and Conditions'),
        icon: 'file text',
      },
    ]);
  }
  if (hasPrivacyPolicy) {
    menuItems.push([
      'privacy',
      {
        href: privacyPolicyURL(),
        modal: hasPrivacyPolicyHTML,
        target: '_blank',
        rel: 'noopener noreferrer',
        caption: Translate.string('Privacy Policy'),
        icon: 'eye',
      },
    ]);
  }
  return menuItems;
};

function SidebarFooter({
  hasTOS,
  tosHTML,
  hasPrivacyPolicy,
  privacyPolicyHTML,
  helpURL,
  contactEmail,
}) {
  const [currentModal, setModal] = useState(null);

  function openModal(e, id) {
    setModal(id);
    e.preventDefault();
  }

  const items = buildMenuItems(
    helpURL,
    hasTOS,
    !!tosHTML,
    hasPrivacyPolicy,
    !!privacyPolicyHTML,
    contactEmail
  );

  return (
    <>
      <Responsive.Phone andLarger minHeight={600}>
        <Menu.Item>
          {items.map(([id, item]) => {
            // XXX: Babel doesn't transpile [x, {y, ...rest}] correctly
            // https://github.com/babel/babel/issues/10257
            const {href, icon, modal, caption, ...extraProps} = item;
            return (
              <ResponsivePopup
                key={id}
                inverted
                position="bottom right"
                trigger={
                  <a
                    href={href}
                    onClick={modal ? e => openModal(e, id) : undefined}
                    {...extraProps}
                  >
                    <Icon size="large" name={icon} />
                  </a>
                }
              >
                {caption}
              </ResponsivePopup>
            );
          })}
        </Menu.Item>
      </Responsive.Phone>
      {contactEmail && (
        <Modal
          open={currentModal === 'contact'}
          size="tiny"
          closeIcon
          onClose={() => setModal(null)}
        >
          <Modal.Header>
            <Translate>Contact</Translate>
          </Modal.Header>
          <Modal.Content>
            <div>
              <Translate>
                If you need support, you can contact the following email address:
              </Translate>
            </div>
            <div>
              <a href={`mailto:${contactEmail}`}>{contactEmail}</a>
            </div>
          </Modal.Content>
        </Modal>
      )}
      {tosHTML && (
        <Modal open={currentModal === 'tos'} closeIcon onClose={() => setModal(null)}>
          <Modal.Header>
            <Translate>Terms and Conditions</Translate>
          </Modal.Header>
          <Modal.Content>
            <div dangerouslySetInnerHTML={{__html: tosHTML}} />
          </Modal.Content>
        </Modal>
      )}
      {privacyPolicyHTML && (
        <Modal open={currentModal === 'privacy'} closeIcon onClose={() => setModal(null)}>
          <Modal.Header>
            <Translate>Privacy Policy</Translate>
          </Modal.Header>
          <Modal.Content>
            <div dangerouslySetInnerHTML={{__html: privacyPolicyHTML}} />
          </Modal.Content>
        </Modal>
      )}
    </>
  );
}

SidebarFooter.propTypes = {
  hasTOS: PropTypes.bool.isRequired,
  tosHTML: PropTypes.string,
  hasPrivacyPolicy: PropTypes.bool.isRequired,
  privacyPolicyHTML: PropTypes.string,
  helpURL: PropTypes.string.isRequired,
  contactEmail: PropTypes.string,
};

SidebarFooter.defaultProps = {
  tosHTML: null,
  privacyPolicyHTML: null,
  contactEmail: null,
};

export default connect(state => ({
  contactEmail: configSelectors.getContactEmail(state),
  helpURL: configSelectors.getHelpURL(state),
  hasTOS: configSelectors.hasTOS(state),
  tosHTML: configSelectors.getTOSHTML(state),
  hasPrivacyPolicy: configSelectors.hasPrivacyPolicy(state),
  privacyPolicyHTML: configSelectors.getPrivacyPolicyHTML(state),
}))(SidebarFooter);
