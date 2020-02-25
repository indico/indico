// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.
import menuEntriesURL from 'indico-url:event_editing.api_menu_entries';

import React from 'react';
import {useSelector} from 'react-redux';
import PropTypes from 'prop-types';
import {Header} from 'semantic-ui-react';
import {useIndicoAxios} from 'indico/react/hooks';

import {getStaticData} from '../../selectors';

import Timeline from '../Timeline';
import MenuBar from './MenuBar';

import './EditingView.module.scss';

export default function EditingView({eventTitle}) {
  const staticData = useSelector(getStaticData);
  const {eventId} = staticData;

  const menuItems = useIndicoAxios({
    url: menuEntriesURL({confId: eventId}),
    camelize: false,
    trigger: eventId,
  });

  if (!menuItems) {
    return null;
  }

  return (
    <div styleName="editing-view">
      <MenuBar eventId={eventId} eventTitle={eventTitle} menuItems={menuItems} />
      <div styleName="contents">
        <Header as="h2" styleName="header">
          {eventTitle}
        </Header>
        <Timeline />
      </div>
    </div>
  );
}

EditingView.propTypes = {
  eventTitle: PropTypes.string.isRequired,
};
