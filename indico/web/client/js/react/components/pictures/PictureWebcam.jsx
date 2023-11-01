// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import Webcam from 'react-webcam';
import {Header, Icon} from 'semantic-ui-react';

import './Picture.module.scss';
import {Translate} from 'indico/react/i18n';

export function PictureWebcam({
  cameraRef,
  height,
  width,
  onCapture,
  onUserMediaError,
  backAction,
  minSize,
}) {
  const [userMediaStarted, setUserMediaStarted] = useState(false);
  height = Math.max(height, minSize) + 100;
  width = Math.max(height, minSize) + 100;
  return (
    <>
      {!userMediaStarted && (
        <Icon styleName="loading-overlay" loading name="spinner" size="huge" color="grey" />
      )}
      <div
        styleName={userMediaStarted ? 'picture-outer-div show' : 'picture-outer-div hidden'}
        onClick={onCapture}
      >
        <div styleName="picture-inner-div">
          <Header as="h3" icon textAlign="center" color="grey">
            <Translate>Camera</Translate>
          </Header>
          <Webcam
            ref={cameraRef}
            audio={false}
            height={height}
            width={width}
            screenshotFormat="image/png"
            onUserMedia={() => setUserMediaStarted(true)}
            onUserMediaError={onUserMediaError}
            mirrored
          />
          <p>
            <Translate>click anywhere on the image to take a picture</Translate>
          </p>
          <Icon
            styleName="back"
            name="arrow left"
            color="grey"
            size="large"
            onClick={evt => {
              evt.stopPropagation();
              backAction();
            }}
          />
        </div>
      </div>
    </>
  );
}

PictureWebcam.propTypes = {
  cameraRef: PropTypes.object.isRequired,
  height: PropTypes.number,
  width: PropTypes.number,
  minSize: PropTypes.number,
  onCapture: PropTypes.func.isRequired,
  onUserMediaError: PropTypes.func,
  backAction: PropTypes.func.isRequired,
};

PictureWebcam.defaultProps = {
  height: 400,
  width: 400,
  minSize: 250,
  onUserMediaError: null,
};
