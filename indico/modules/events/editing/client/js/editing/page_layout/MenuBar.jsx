// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import contribDisplayURL from 'indico-url:contributions.display_contribution';
import editableTypeListURL from 'indico-url:event_editing.editable_type_list';
import manageEditableTypeURL from 'indico-url:event_editing.manage_editable_type';
import displayURL from 'indico-url:events.display';

import PropTypes from 'prop-types';
import React from 'react';
import {Link} from 'react-router-dom';
import {Header, Icon, Menu} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import Palette from 'indico/utils/palette';

import {EditableType, EditableEditingTitles} from '../../models';

import './MenuBar.module.scss';

function EditableListMenu({eventId, editableType}) {
  if (location.pathname === editableTypeListURL({event_id: eventId, type: editableType})) {
    return (
      <Menu vertical>
        <Menu.Item active>
          <Translate>Editable list</Translate>
        </Menu.Item>
      </Menu>
    );
  }
  return (
    <Menu vertical>
      <Menu.Item as={Link} to={editableTypeListURL({event_id: eventId, type: editableType})}>
        <span style={{color: Palette.blue}}>
          <Translate>Editable list</Translate>
        </span>
      </Menu.Item>
    </Menu>
  );
}

EditableListMenu.propTypes = {
  eventId: PropTypes.number.isRequired,
  editableType: PropTypes.oneOf(Object.values(EditableType)).isRequired,
};

export default function MenuBar({eventId, menuData, editableType, contribId}) {
  const displayViewURL =
    contribId === null
      ? displayURL({event_id: eventId})
      : contribDisplayURL({event_id: eventId, contrib_id: contribId});
  const managementViewURL = manageEditableTypeURL({event_id: eventId, type: editableType});
  const {items: menuItems, showManagementLink, showEditableList} = menuData;

  return (
    <div styleName="menu-bar">
      <Header as="h2" styleName="header">
        {EditableEditingTitles[editableType]}
      </Header>
      {showEditableList[editableType] && (
        <EditableListMenu eventId={eventId} editableType={editableType} />
      )}
      {!!menuItems.length && (
        <Menu vertical>
          <Menu.Item header>
            <span styleName="capitalized" style={{color: Palette.black}}>
              <Translate>other modules</Translate>
            </span>
          </Menu.Item>
          {menuItems.map(item => (
            <Menu.Item key={item.name} name={item.name} as="a" href={item.url}>
              <span style={{color: Palette.blue}}>
                {item.icon && <Icon name={item.icon.replace('icon-', '')} />}
                {item.title}
              </span>
            </Menu.Item>
          ))}
        </Menu>
      )}
      <Menu vertical>
        <Menu.Item header>
          <span styleName="capitalized" style={{color: Palette.black}}>
            <Translate>other views</Translate>
          </span>
        </Menu.Item>
        <Menu.Item name="display" as="a" href={displayViewURL}>
          <span style={{color: Palette.blue}}>
            <Icon name="tv" /> <Translate>Display</Translate>
          </span>
        </Menu.Item>
        {showManagementLink && (
          <Menu.Item name="management" as="a" href={managementViewURL}>
            <span style={{color: Palette.blue}}>
              <Icon name="pencil" /> <Translate>Management</Translate>
            </span>
          </Menu.Item>
        )}
      </Menu>
    </div>
  );
}

const menuEntryPropTypes = {
  name: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
  icon: PropTypes.string,
};

MenuBar.propTypes = {
  eventId: PropTypes.number.isRequired,
  contribId: PropTypes.number,
  menuData: PropTypes.shape({
    items: PropTypes.arrayOf(PropTypes.shape(menuEntryPropTypes)).isRequired,
    showManagementLink: PropTypes.bool.isRequired,
    showEditableList: PropTypes.shape({
      paper: PropTypes.bool.isRequired,
      slides: PropTypes.bool.isRequired,
      poster: PropTypes.bool.isRequired,
    }).isRequired,
  }).isRequired,
  editableType: PropTypes.oneOf(Object.values(EditableType)).isRequired,
};

MenuBar.defaultProps = {
  contribId: null,
};
