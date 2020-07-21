// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.
import menuEntriesURL from 'indico-url:event_editing.api_menu_entries';

import React from 'react';
import {useParams} from 'react-router-dom';
import PropTypes from 'prop-types';
import {Header} from 'semantic-ui-react';
import {useIndicoAxios} from 'indico/react/hooks';
import {useNumericParam} from 'indico/react/util/routing';

import MenuBar from './MenuBar';
import Footer from './Footer';

import './EditingView.module.scss';

export default function EditingView({eventTitle, children}) {
  const eventId = useNumericParam('confId');
  const contribId = useNumericParam('contrib_id');
  const {type} = useParams();
  const {data, lastData} = useIndicoAxios({
    url: menuEntriesURL({confId: eventId}),
    trigger: eventId,
  });

  const menuItems = data || lastData;
  if (!menuItems) {
    return null;
  }

  return (
    <div styleName="editing-view">
      <MenuBar eventId={eventId} menuItems={menuItems} editableType={type} contribId={contribId} />
      <div styleName="contents">
        <div styleName="timeline">
          <Header as="h2" styleName="header">
            {eventTitle}
          </Header>
          {children}
        </div>
        <Footer />
      </div>
    </div>
  );
}

EditingView.propTypes = {
  eventTitle: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};
