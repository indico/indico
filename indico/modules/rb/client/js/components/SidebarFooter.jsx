// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contactURL from 'indico-url:core.contact';
import tosURL from 'indico-url:legal.display_tos';
import privacyPolicyURL from 'indico-url:legal.display_privacy';

import React, {useState} from 'react';
import PropTypes from 'prop-types';
import {Menu, Modal} from 'semantic-ui-react';
import {connect} from 'react-redux';
import {Translate} from 'indico/react/i18n';
import {selectors as configSelectors} from '../common/config';

function SidebarFooter({
  hasTOS,
  tosHTML,
  hasPrivacyPolicy,
  privacyPolicyHTML,
  helpURL,
  contactEmail,
}) {
  const [contactVisible, setContactVisible] = useState(false);
  const [termsVisible, setTermsVisible] = useState(false);
  const [privacyPolicyVisible, setPrivacyPolicyVisible] = useState(false);

  return (
    <>
      {helpURL && (
        <Menu.Item as="a" href={helpURL} target="_blank" rel="noopener noreferrer">
          <Translate>Help</Translate>
        </Menu.Item>
      )}
      {contactEmail && (
        <Menu.Item
          href={contactURL()}
          onClick={evt => {
            evt.preventDefault();
            setContactVisible(true);
          }}
        >
          <Translate>Contact</Translate>
        </Menu.Item>
      )}
      {(hasTOS || tosHTML) && (
        <Menu.Item
          href={tosURL()}
          target="_blank"
          rel="noopener noreferrer"
          onClick={evt => {
            if (tosHTML) {
              evt.preventDefault();
              setTermsVisible(true);
            }
          }}
        >
          <Translate>Terms and Conditions</Translate>
        </Menu.Item>
      )}
      {(hasPrivacyPolicy || privacyPolicyHTML) && (
        <Menu.Item
          href={privacyPolicyURL()}
          target="_blank"
          rel="noopener noreferrer"
          onClick={evt => {
            if (privacyPolicyHTML) {
              evt.preventDefault();
              setPrivacyPolicyVisible(true);
            }
          }}
        >
          <Translate>Privacy Policy</Translate>
        </Menu.Item>
      )}
      {contactEmail && (
        <Modal open={contactVisible} size="tiny" closeIcon onClose={() => setContactVisible(false)}>
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
        <Modal open={termsVisible} closeIcon onClose={() => setTermsVisible(false)}>
          <Modal.Header>
            <Translate>Terms and Conditions</Translate>
          </Modal.Header>
          <Modal.Content>
            <div dangerouslySetInnerHTML={{__html: tosHTML}} />
          </Modal.Content>
        </Modal>
      )}
      {privacyPolicyHTML && (
        <Modal open={privacyPolicyVisible} closeIcon onClose={() => setPrivacyPolicyVisible(false)}>
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
