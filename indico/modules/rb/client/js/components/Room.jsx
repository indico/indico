// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import Overridable from 'react-overridable';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Card, Icon, Label, Loader, Popup, Button} from 'semantic-ui-react';

import {TooltipIfTruncated, ResponsivePopup} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {Markdown, Slot} from 'indico/react/util';

import {actions as userActions, selectors as userSelectors} from '../common/user';

import DimmableImage from './DimmableImage';
import RoomFeatureEntry from './RoomFeatureEntry';
import SpriteImage from './SpriteImage';

import './Room.module.scss';

class Room extends React.Component {
  static propTypes = {
    room: PropTypes.object.isRequired,
    children: PropTypes.node,
    showFavoriteButton: PropTypes.bool,
    isFavorite: PropTypes.bool.isRequired,
    isCheckingUserRoomPermissions: PropTypes.bool.isRequired,
    addFavoriteRoom: PropTypes.func.isRequired,
    delFavoriteRoom: PropTypes.func.isRequired,
    customRoomComponent: PropTypes.elementType,
  };

  static defaultProps = {
    showFavoriteButton: false,
    children: null,
    customRoomComponent: null,
  };

  shouldComponentUpdate(nextProps) {
    const {
      isFavorite: nextIsFavorite,
      isCheckingUserRoomPermissions: nextIsCheckingUserRoomPermissions,
      room: nextRoom,
      children: nextChildren,
    } = nextProps;
    const {isFavorite, isCheckingUserRoomPermissions, room, children} = this.props;

    return (
      nextIsFavorite !== isFavorite ||
      nextIsCheckingUserRoomPermissions !== isCheckingUserRoomPermissions ||
      !_.isEqual(room, nextRoom) ||
      !_.isEqual(nextChildren, children)
    );
  }

  renderFavoriteButton() {
    const {addFavoriteRoom, delFavoriteRoom, room, isFavorite} = this.props;
    const button = (
      <Button
        icon="star"
        color={isFavorite ? 'yellow' : 'teal'}
        circular
        onClick={() => (isFavorite ? delFavoriteRoom : addFavoriteRoom)(room.id)}
      />
    );
    const tooltip = isFavorite
      ? Translate.string('Remove from favorites')
      : Translate.string('Add to favorites');
    return <ResponsivePopup trigger={button} content={tooltip} position="top center" />;
  }

  renderCardImage = (room, content, actions) => {
    const {showFavoriteButton} = this.props;
    const sprite = <SpriteImage pos={room.spritePosition} />;

    if ((actions !== undefined && actions.length !== 0) || showFavoriteButton) {
      const dimmerContent = (
        <div styleName="icons-wrapper">
          {actions}
          {showFavoriteButton && this.renderFavoriteButton()}
        </div>
      );
      return (
        <DimmableImage content={content} hoverContent={dimmerContent}>
          {sprite}
        </DimmableImage>
      );
    } else {
      return (
        <div styleName="room-image">
          <div styleName="room-extra-info">{content}</div>
          {sprite}
        </div>
      );
    }
  };

  renderRoomStatus = () => {
    const {
      room: {isReservable, canUserBook, canUserPrebook},
      isCheckingUserRoomPermissions,
    } = this.props;
    if (!isReservable) {
      return (
        <Popup
          key="not-bookable"
          trigger={<Icon name="dont" color="red" />}
          content={Translate.string('This space is not bookable')}
          position="top center"
          hideOnScroll
        />
      );
    } else if (isCheckingUserRoomPermissions) {
      return (
        <Popup
          key="check-pending"
          trigger={<Loader active inline size="tiny" />}
          content={Translate.string('Checking permissions...')}
          position="top center"
          hideOnScroll
        />
      );
    } else if (!canUserBook && !canUserPrebook) {
      return (
        <Popup
          key="not-authorized"
          trigger={<Icon name="lock" color="red" />}
          content={Translate.string('This space is not publicly available')}
          position="top center"
          hideOnScroll
        />
      );
    } else {
      return null;
    }
  };

  render() {
    const {
      room,
      children,
      isFavorite,
      // XXX: don't remove the unused ones below, they should not end up in restProps!
      showFavoriteButton,
      addFavoriteRoom,
      delFavoriteRoom,
      isCheckingUserRoomPermissions,
      customRoomComponent: CustomRoom,
      ...restProps
    } = this.props;
    const {content, actions} = Slot.split(children);

    if (CustomRoom) {
      return <CustomRoom roomInstance={this} {...this.props} />;
    }

    return (
      <Card styleName="room-card" {...restProps}>
        {isFavorite && <Label corner="right" icon="star" color="yellow" />}
        {this.renderCardImage(room, content, actions)}
        <Card.Content>
          <TooltipIfTruncated useEventTarget>
            <Card.Header styleName="room-title">{room.fullName}</Card.Header>
          </TooltipIfTruncated>
          <Card.Meta style={{fontSize: '0.8em'}}>{room.division}</Card.Meta>
          <Card.Description styleName="room-description">
            {room.comments && (
              <TooltipIfTruncated>
                <div styleName="room-comments">
                  <Markdown allowedElements={['br']} unwrapDisallowed>
                    {room.comments}
                  </Markdown>
                </div>
              </TooltipIfTruncated>
            )}
          </Card.Description>
        </Card.Content>
        <Card.Content styleName="room-content" extra>
          <Icon name="user" /> {room.capacity || Translate.string('Not specified')}
          <span styleName="room-details">
            {room.features.map(feature => (
              <RoomFeatureEntry key={feature.name} feature={feature} color="green" />
            ))}
            {this.renderRoomStatus()}
          </span>
        </Card.Content>
      </Card>
    );
  }
}

export default connect(
  () => {
    const isFavoriteRoom = userSelectors.makeIsFavoriteRoom();
    return (state, props) => ({
      isFavorite: isFavoriteRoom(state, props),
      isCheckingUserRoomPermissions: userSelectors.isCheckingUserRoomPermissions(state),
    });
  },
  dispatch =>
    bindActionCreators(
      {
        addFavoriteRoom: userActions.addFavoriteRoom,
        delFavoriteRoom: userActions.delFavoriteRoom,
      },
      dispatch
    )
)(Overridable.component('Room', Room));
