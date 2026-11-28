// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
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
import {Icon, Menu} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {selectors as configSelectors} from '../common/config';

import SidebarDialog from './SidebarDialog';

import './SidebarFooter.module.scss';

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
      <Menu.Item>
        {items.map(([id, item]) => {
          const {href, icon, modal, caption, ...extraProps} = item;
          const Control = modal ? 'button' : 'a';
          return (
            <ind-with-tooltip key={id}>
              <Control
                href={modal ? undefined : href}
                type={modal ? 'button' : undefined}
                styleName="footer-control"
                onClick={modal ? e => openModal(e, id) : undefined}
                {...(modal ? {} : extraProps)}
              >
                <Icon size="large" name={icon} />
                <span data-tip-content>{caption}</span>
              </Control>
            </ind-with-tooltip>
          );
        })}
      </Menu.Item>
      {contactEmail && (
        <SidebarDialog
          open={currentModal === 'contact'}
          short
          title={Translate.string('Contact')}
          onClose={() => setModal(null)}
        >
          <div>
            <Translate>If you need support, you can contact the following email address:</Translate>
          </div>
          <div>
            <a href={`mailto:${contactEmail}`}>{contactEmail}</a>
          </div>
        </SidebarDialog>
      )}
      {tosHTML && (
        <SidebarDialog
          open={currentModal === 'tos'}
          title={Translate.string('Terms and Conditions')}
          onClose={() => setModal(null)}
        >
          <div dangerouslySetInnerHTML={{__html: tosHTML}} />
        </SidebarDialog>
      )}
      {privacyPolicyHTML && (
        <SidebarDialog
          open={currentModal === 'privacy'}
          title={Translate.string('Privacy Policy')}
          onClose={() => setModal(null)}
        >
          <div dangerouslySetInnerHTML={{__html: privacyPolicyHTML}} />
        </SidebarDialog>
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
