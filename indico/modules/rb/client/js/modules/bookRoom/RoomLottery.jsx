// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// 2025 April fools joke - remove it once the joke is over (or people start complaining about it)

import PropTypes from 'prop-types';
import React, {useState, useEffect} from 'react';
import {useDispatch} from 'react-redux';
import {Button, Message} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {actions as roomActions} from '../../common/rooms';

function pickRoom(rooms, dispatch, setIsUnlucky) {
  const diceRoll = Math.floor(Math.random() * 20) + 1;
  const unluckyRolls = [1, 3, 4, 8, 13];
  if (unluckyRolls.includes(diceRoll)) {
    setIsUnlucky(true);
    return;
  }

  const roomIds = rooms.map(room => room.id);
  const randomIndex = Math.floor(Math.random() * roomIds.length);
  const selectedRoomId = roomIds[randomIndex];

  return dispatch(roomActions.openRoomDetailsBook(selectedRoomId));
}

export default function RoomLottery({rooms}) {
  const dispatch = useDispatch();
  const [isBannerVisible, setIsBannerVisible] = useState(
    localStorage.getItem('hideRBLotteryBanner') !== 'true'
  );
  const [isUnlucky, setIsUnlucky] = useState(false);
  const [isRolling, setIsRolling] = useState(false);

  const hideLotteryBanner = () => {
    localStorage.setItem('hideRBLotteryBanner', 'true');
    setIsBannerVisible(false);
  };

  useEffect(() => {
    setIsBannerVisible(localStorage.getItem('hideRBLotteryBanner') !== 'true');
  }, []);

  console.log(rooms);

  if (!isBannerVisible || rooms.length === 0) {
    return null;
  }

  if (isUnlucky) {
    return (
      <Message
        icon="calendar times outline"
        color="purple"
        header={Translate.string('Better luck next time!')}
        onDismiss={hideLotteryBanner}
        content={<Translate as="p">The odds were not in your favour.</Translate>}
      />
    );
  }

  return (
    <Message
      icon="magic"
      color="blue"
      header={Translate.string('Feeling lucky?')}
      onDismiss={hideLotteryBanner}
      content={
        <>
          <Translate as="p" style={{marginBottom: '0.5rem'}}>
            Tired of searching for the perfect room? Overwhelmed by choices? Leave it to chance!
            Click the button below to let fate decide your next room booking.
          </Translate>
          <Button
            primary
            loading={isRolling}
            disabled={isRolling}
            onClick={() => {
              setIsRolling(true);
              setTimeout(() => {
                pickRoom(rooms, dispatch, setIsUnlucky);
                setIsRolling(false);
              }, 1500); // for added suspense
            }}
          >
            {Translate.string("I'm feeling lucky!")}
          </Button>
        </>
      }
    />
  );
}

RoomLottery.propTypes = {
  rooms: PropTypes.array.isRequired,
};
